package com.bbn.necd.event.bin;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.bin.TrainSimilarityMetric;
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
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;

public final class DoTraining {
  private static final Logger log = LoggerFactory.getLogger(DoTraining.class);

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
    - memberPair.label
    - eventFeatures
    - feature.extractFeatureTypes
    - feature.sparsityThreshold

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

    - * from TrainSimilarityMetric
        - learner.log
        - memberPair.label
        - metricType
        - learner.output.featureIndicesFile
        - learner.output.weightsFile
        - * from GradientDescent
            - learner.learningRate
            - learner.regularizationCoefficient
            - learner.iterations
            - learner.positiveWeight
            - learner.annealingT
   */
  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());





    //final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();
    final BackgroundInformation backgroundInfo = BackgroundInformation.fromParams(params);

    // getting id pairs from a CSV file
    final ImmutableList<SymbolPair> idPairs = getEventIds(params.getExistingFile("memberPair.label"));

    // now let's read features from a JSON file
    // NOTE: each id in idPairs must be found as a key in the following eventFeatures
    final ImmutableMap<Symbol, EventFeatures> eventFeatures = EventFeaturesUtils.readEventFeatures(params.getExistingFile("eventFeatures"));

    final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures = EventFeaturesUtils.readEventPairFeatures(params.getExistingFile("eventPairFeatures"));

    // get the list of features the user would like to use
    final List<EventFeatureType.ExtractPairFeatureType>
        featureTypes = params.getEnumList("feature.extractFeatureTypes", EventFeatureType.ExtractPairFeatureType.class);

    // since this is training, there is no feature indices file
    final Optional<ImmutableMap<String, Integer>> featureIndices = Optional.<ImmutableMap<String, Integer>>absent();

    final FeatureTable.Builder featureTableBuilder = FeatureTable.from(params);
    int runningFeatureIndex = FeatureTable.initialFeatureIndex;
    final int sparsityThreshold = params.getInteger("feature.sparsityThreshold"); // we only use a feature value if it occurs at least this number of times

    for(final EventFeatureType.ExtractPairFeatureType featureType : featureTypes) {
      // We transform each feature value to an integer or feature index, and we start indexing for this feature from runningFeatureIndex
      final PairFeature
          feature = featureType.from(idPairs, eventFeatures, eventPairFeatures,
          runningFeatureIndex, backgroundInfo, sparsityThreshold, featureIndices, params);

      if(feature.hasFeatureValue()) {
        featureTableBuilder.withFeature(feature);
        runningFeatureIndex = feature.getEndIndex() + 1;    // to prepare for the next featureType
      }
    }

    final FeatureTable featureTable = featureTableBuilder.build();

    final RealInstanceManager realInstanceManager = RealInstanceManager.from(params, featureTable);

    final TrainSimilarityMetric
        trainSimilarityMetric = TrainSimilarityMetric.from(params, realInstanceManager);
    trainSimilarityMetric.run();

  }

  // TODO: shift this somewhere else
  private static ImmutableList<SymbolPair> getEventIds(final File pairLabelsTable) throws IOException {
    final ImmutableList.Builder<SymbolPair> ret = ImmutableList.builder();

    for(final String line : Files.asCharSource(pairLabelsTable, Charsets.UTF_8).readLines()) {
      final String[] tokens = line.split("\t");
      ret.add(SymbolPair.from(Symbol.from(tokens[0]), Symbol.from(tokens[1])));
    }

    return ret.build();
  }



}
