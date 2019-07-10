package com.bbn.necd.event.bin;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.bin.TrainSimilarityMetric;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.FeatureTable;
import com.bbn.necd.common.theory.SingleFeature;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatureType;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventFeaturesUtils;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.base.Predicates;
import com.google.common.collect.FluentIterable;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.List;

public final class EventFeaturesToSparseVectors {

  private static final Logger log = LoggerFactory.getLogger(EventFeaturesToSparseVectors.class);

  public static void main(String[] argv) {
    // we wrap the main method in this way to
    // ensure a non-zero return value on failure
    try {
      trueMain(argv);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  /*
    Parameters:
    - targetMembers.label
    - eventFeatures
    - feature.extractFeatureTypes
    - feature.sparsityThreshold

    - * from BackgroundInformation
        - docInfoDirectory
        - * from PredictVectorManager
            - data.predictVectorFile
            - feature.minValue

    - * from FeatureTable
        - learner.weightsFile (optional during training)
        - learner.initialWeight (optional else default to 1.0)
        - learner.useBias
        - feature.exampleType

    - * from RealInstanceManager
        - targetMembers.list
        - learner.useBias
        - feature.exampleType
   */
  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    //final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();
    final BackgroundInformation backgroundInfo = BackgroundInformation.fromParams(params);

    final ImmutableList<Symbol> ids =
        FluentIterable.from(Files.readLines(params.getExistingFile("targetMembers.list"), Charsets.UTF_8))
            .transform(SymbolUtils.symbolizeFunction())
            .toList();

    // now let's read features from a JSON file
    // NOTE: each id in idPairs must be found as a key in the following eventFeatures
    final File eventFeaturesFile = params.getExistingFile("eventFeatures");
    log.info("Loading event features from {}", eventFeaturesFile);
    final ImmutableMap<Symbol, EventFeatures> eventFeatures = EventFeaturesUtils.readEventFeatures(
        eventFeaturesFile);

    // get the list of features the user would like to use
    final List<EventFeatureType.ExtractSingleFeatureType> featureTypes =
        params.getEnumList("eventNotEvent.extractFeatureTypes",
            EventFeatureType.ExtractSingleFeatureType.class);

    // feature indices file is only present during decoding
    final Optional<File> featureIndicesFile =
        params.getOptionalExistingFile("eventNotEvent.decodingFeatureIndices");
    final Optional<ImmutableMap<String, Integer>> featureIndices = featureIndicesFile.isPresent()
        ? Optional.of(FeatureTable.readFeatureIndices(featureIndicesFile.get()))
        : Optional.<ImmutableMap<String, Integer>>absent();

    // We only use a feature value if it occurs at least this number of times
    final int sparsityThreshold = params.getInteger("eventNotEvent.sparsityThreshold");

    final FeatureTable featureTable =
        createFeatureTable(params, backgroundInfo, ids, eventFeatures, featureTypes,
            sparsityThreshold, featureIndices);

    final RealInstanceManager realInstanceManager = RealInstanceManager.from(params, featureTable);

    final Optional<ImmutableMap<Symbol, Symbol>> memberIdToLabel =
        params.isPresent("targetMembers.label")
        ? Optional.of(readMemberLabel(params.getExistingFile("targetMembers.label")))
        : Optional.<ImmutableMap<Symbol, Symbol>>absent();
    writeSparseVectors(realInstanceManager, ids, memberIdToLabel,
        params.getCreatableFile("sparseVectorFile"));

    // this is only during training
    final Optional<File> featureIndicesOutputFile =
        params.getOptionalCreatableFile("eventNotEvent.trainingFeatureIndices");
    if (featureIndicesOutputFile.isPresent()) {
      TrainSimilarityMetric.writeFeatureIndicesToFile(realInstanceManager.getFeatureTable(),
              featureIndicesOutputFile.get());
    }

  }

  private static FeatureTable createFeatureTable(final Parameters params,
      final BackgroundInformation backgroundInfo, final ImmutableList<Symbol> ids,
      final ImmutableMap<Symbol, EventFeatures> eventFeatures,
      final List<EventFeatureType.ExtractSingleFeatureType> featureTypes,
      final int sparsityThreshold,
      final Optional<ImmutableMap<String, Integer>> featureIndices) throws IOException {
    final FeatureTable.Builder featureTableBuilder = FeatureTable.from(params);
    int runningFeatureIndex = FeatureTable.initialFeatureIndex;

    // Filter ids down to those that have features
    final ImmutableList<Symbol> idsWithFeatures = FluentIterable.from(ids)
        .filter(Predicates.in(eventFeatures.keySet()))
        .toList();

    int lostIds = ids.size() - idsWithFeatures.size();
    if (lostIds != 0) {
      log.info("Removed {} of {} ids due to missing features", lostIds, ids.size());
    }
    if (idsWithFeatures.isEmpty()) {
      throw new RuntimeException("Features were found for none of the requested IDs");
    }

    for (final EventFeatureType.ExtractSingleFeatureType featureType : featureTypes) {
      // We transform each feature value to an integer or feature index, and we start indexing for
      // this feature from runningFeatureIndex
      final SingleFeature feature = featureType.from(idsWithFeatures, eventFeatures,
          runningFeatureIndex, backgroundInfo, sparsityThreshold, featureIndices, params);
      featureTableBuilder.withFeature(feature);
      runningFeatureIndex = feature.getEndIndex() + 1;    // to prepare for the next featureType
    }

    return featureTableBuilder.build();
  }

  private static void writeSparseVectors(final RealInstanceManager realInstanceManager,
      final ImmutableList<Symbol> ids, final Optional<ImmutableMap<Symbol, Symbol>> memberIdToLabel,
      final File outfile) throws IOException {
    final File logFile = new File(outfile.getAbsolutePath() + ".log");

    final ImmutableMap<Symbol, FactoredRealVector> factoredInstances =
        realInstanceManager.getSingleInstances();

    log.info("Features found for {} out of {} total examples", factoredInstances.keySet().size(),
        ids.size());
    // As the files are large, we write them out line by line
    final Writer vectorWriter = Files.asCharSink(outfile, Charsets.UTF_8).openBufferedStream();
    final Writer logWriter = Files.asCharSink(logFile, Charsets.UTF_8).openBufferedStream();

    for (final Symbol id : ids) {
      final Symbol label = memberIdToLabel.isPresent() ? memberIdToLabel.get().get(id) : DUMMY_LABEL;

      if (factoredInstances.containsKey(id)) {
        final FactoredRealVector v = factoredInstances.get(id);
        final String sparseString = v.toSparseString();

        final String vectorString = label.asString() + " " + sparseString + "\n";
        vectorWriter.write(vectorString);

        final String logString = id.asString() + " " + sparseString + "\n";
        logWriter.write(logString);
      }
    }

    // Clean up
    vectorWriter.close();
    logWriter.close();
  }

  public static ImmutableMap<Symbol, Symbol> readMemberLabel(final File infile)
      throws IOException {
    final ImmutableMap.Builder<Symbol, Symbol> ret = ImmutableMap.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      ret.put(Symbol.from(tokens[0]), Symbol.from(tokens[1]));
    }

    return ret.build();
  }

  private final static Symbol DUMMY_LABEL = Symbol.from("1");
}
