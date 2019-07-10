package com.bbn.necd.event.bin;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.bin.GenerateMemberSimilarity;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.FeatureTable;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatureType;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.necd.event.features.EventPairFeatures;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Table;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;

/*
  Parameter:
  - memberPair.list
  - eventFeatures
  - feature.extractFeatureTypes
  - learner.featureIndicesFile
  - feature.sparsityThreshold
  - interMemberSimilarity

  - * from PredictVectorManager
      - data.predictVectorFile
      - feature.minValue

  - * from FeatureTable
      - learner.weightsFile (optional during training)
      - learner.initialWeight
      - learner.useBias

  - * from RealInstanceManager
      - targetMembers.list
      - learner.useBias

  - * from GenerateMemberSimilarity
      - metricType
      - memberPair.label (optional)
*/
public final class DoDecoding {
  private static final Logger log = LoggerFactory.getLogger(DoDecoding.class);

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

  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());


    //final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();
    final BackgroundInformation backgroundInfo = BackgroundInformation.fromParams(params);



    final ImmutableList<SymbolPair> idPairs = getEventIds(params.getExistingFile("memberPair.list"));

    final ImmutableMap<Symbol, EventFeatures> eventFeatures = EventFeaturesUtils.readEventFeatures(params.getExistingFile("eventFeatures"));

    final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures = EventFeaturesUtils.readEventPairFeatures(params.getExistingFile("eventPairFeatures"));

    final List<EventFeatureType.ExtractPairFeatureType> featureTypes = params.getEnumList("feature.extractFeatureTypes", EventFeatureType.ExtractPairFeatureType.class);

    final File featureIndicesFile = params.getExistingFile("learner.featureIndicesFile");
    final ImmutableMap<String, Integer> featureIndices = FeatureTable.readFeatureIndices(featureIndicesFile);

    final FeatureTable.Builder featureTableBuilder = FeatureTable.from(params);
    int runningFeatureIndex = FeatureTable.initialFeatureIndex;
    final int sparsityThreshold = params.getInteger("feature.sparsityThreshold");

    for(final EventFeatureType.ExtractPairFeatureType featureType : featureTypes) {
      final PairFeature
          feature = featureType.from(idPairs, eventFeatures, eventPairFeatures, runningFeatureIndex, backgroundInfo, sparsityThreshold, Optional.of(featureIndices), params);

      if(feature.hasFeatureValue()) {
        featureTableBuilder.withFeature(feature);
        runningFeatureIndex = feature.getEndIndex() + 1;    // to prepare for the next featureType
      }
    }

    final FeatureTable featureTable = featureTableBuilder.build();

    final RealInstanceManager realInstanceManager = RealInstanceManager.from(params, featureTable);

    final GenerateMemberSimilarity generateMemberSimilarity = GenerateMemberSimilarity.from(params, realInstanceManager);
    generateMemberSimilarity.calculateSimilarityToFile(params.getCreatableFile("interMemberSimilarity"));

    if(params.getBoolean("useParagraphVector")) {
      final ImmutableList.Builder<String> pSimLines = ImmutableList.builder();

      for(final Table.Cell<Symbol, Symbol, Double> cell : generateMemberSimilarity.getMemberSimilarity().cellSet()) {
        final Symbol docId1 = eventFeatures.get(cell.getRowKey()).docId();
        final Symbol docId2 = eventFeatures.get(cell.getColumnKey()).docId();

        final double sim = calculateParagraphSimilarity(backgroundInfo.getPredictVectorManager(), docId1, docId2);

        pSimLines.add(docId1.asString() + " " + docId2.asString() + " " + sim);
      }

      Files.asCharSink(params.getCreatableFile("interMemberSimilarity.paragraphVectors"), Charsets.UTF_8).writeLines(pSimLines.build());
    }
  }

  private static double calculateParagraphSimilarity(final PredictVectorManager pvManager, final Symbol id1, final Symbol id2) {
    final Optional<PredictVectorManager.PredictVector> v1 = pvManager.getVector(id1);
    final Optional<PredictVectorManager.PredictVector> v2 = pvManager.getVector(id2);

    if(v1.isPresent() && v2.isPresent()) {
      final double dotProduct = CosineSimilarity.calculateDotProduct(v1.get().getValues(), v2.get().getValues());
      final double norm1 = CosineSimilarity.calculateL2Norm(v1.get().getValues());
      final double norm2 = CosineSimilarity.calculateL2Norm(v2.get().getValues());
      return dotProduct/(norm1 * norm2);
    } else {
      return 0;
    }
  }

  /*
  private static ImmutableList<SymbolPair> getEventIds(final File pairLabelsTable) throws IOException {
    final ImmutableList.Builder<SymbolPair> ret = ImmutableList.builder();

    final CSVParser pairTableReader = LabelWriter.getParser(pairLabelsTable);

    for (final CSVRecord row : pairTableReader) {
      // Get event ids
      ret.add(SymbolPair.from(Symbol.from(row.get(0)), Symbol.from(row.get(1))));
    }

    return ret.build();
  }
  */

  // TODO: this should shift somewhere else
  private static ImmutableList<SymbolPair> getEventIds(final File infile) throws IOException {
    final ImmutableList.Builder<SymbolPair> ret = ImmutableList.builder();

    for(final String line : Files.asCharSource(infile, Charsets.UTF_8).readLines()) {
      final String[] tokens = line.split("\t");
      final Symbol id1 = Symbol.from(tokens[0]);
      final Symbol id2 = Symbol.from(tokens[1]);
      ret.add(SymbolPair.from(id1, id2));
    }

    return ret.build();
  }



}
