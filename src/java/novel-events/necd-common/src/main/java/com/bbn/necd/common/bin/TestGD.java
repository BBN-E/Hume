package com.bbn.necd.common.bin;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PairwiseSampler.SymbolPair;
import com.bbn.necd.common.hypothesis.Hypothesis;
import com.bbn.necd.common.theory.PairedRealInstance;
import com.bbn.necd.common.theory.WeightedRealVector;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;

public final class TestGD {
  private static final Logger log = LoggerFactory.getLogger(TestGD.class);

  public static void main(final String[] argv) throws IOException {
    /*
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final Optional<Integer> featureDimThreshold = params.getOptionalInteger("feature.featureDimThreshold");
    final double learningRate = params.getDouble("learner.learningRate");
    final double regularizationCoefficient = params.getDouble("learner.regularizationCoefficient");
    final int maxIterations = params.getInteger("learner.iterations");
    final double initialWeight = params.getDouble("learner.initialWeight");     // either 0 or 1
    final MetricType metricType = params.getEnum("metricType", MetricType.class);



    final ImmutableMap<Symbol, Symbol> targetMemberIdsLabels = readMemberLabel(params.getExistingFile("targetMembers.label"));
    //for(final Map.Entry<Symbol, Symbol> entry : targetMemberIdsLabels.entrySet()) {
    //  System.out.println(entry.getKey().toString() + " " + entry.getValue().toString());
    //}

    //final FeatureTable featureTable = FeatureTable.fromFeatureFile(params.getExistingFile("feature.featureTable"))
    //    .withMinValue(params.getDouble("feature.minValue")).withTargetMembers(targetMemberIdsLabels.keySet()).build();
    final FeatureTable featureTable = FeatureTable.fromParams(params).withTargetMembers(targetMemberIdsLabels.keySet()).build();
    log.info("Read feature table with {} unique features", featureTable.getNumberOfFeatures());

    final ImmutableMap<Symbol, Symbol> filteredTargetMemberIdsLabels = featureDimThreshold.isPresent()?
        filterByFeatureDim(targetMemberIdsLabels, featureTable, featureDimThreshold.get()) : targetMemberIdsLabels;

    // there has been 2 filterings:
    // - only positive feature values are kept
    // - based on the above, only items having at least a certain number of features (>= featureDimThreshold) are kept
    final PairwiseSampler sampler = PairwiseSampler.from(filteredTargetMemberIdsLabels, 1.0);


    final ImmutableTable<Symbol, Integer, Double> featureWeights = featureTable.getFeatureWeights();
    final int numberOfFeatures = featureTable.getNumberOfFeatures();

    final ImmutableMap<Symbol, WeightedRealVector> weightedVectors = toWeightedRealVectors(featureWeights, featureDimThreshold, numberOfFeatures, initialWeight);
    log.info("Constructed {} weighted real vectors", weightedVectors.size());



    final ImmutableList<PairedRealInstance> positives = constructPairInstances(sampler.getPositives(), weightedVectors, 1);
    final ImmutableList<PairedRealInstance> negatives = constructPairInstances(sampler.getNegatives(), weightedVectors, 0);
    final ImmutableList<PairedRealInstance> examples = ImmutableList.<PairedRealInstance>builder().addAll(positives).addAll(negatives).build();

    final GradientDescent gd = GradientDescent.from(learningRate, regularizationCoefficient, numberOfFeatures, initialWeight);

    //Hypothesis hypothesis = CosineHypothesis.from(examples, gd.getWeights());
    Hypothesis hypothesis = metricType.hypothesisFrom(examples, gd.getWeights());
    log.info("Starting accuracy {}", accuracy(hypothesis, gd.getWeights()));

    final DecimalFormat df = new DecimalFormat("#.###");
    String previousLossString = "";
    for(int iteration=1; iteration<=maxIterations; iteration++) {
      gd.learn(hypothesis);

      final double loss = gd.currentLoss(hypothesis);
      hypothesis = hypothesis.copyWithWeights(gd.getWeights());

      log.info("GD iteration {}, loss={}, accuracy={}", iteration, loss, accuracy(hypothesis, gd.getWeights()));

      final String currentLossString = df.format(loss);
      if(previousLossString.compareTo(currentLossString)==0) {
      //  break;
      } else {
        previousLossString = currentLossString;
      }
    }

    writeFeatureIndicesToFile(featureTable.getFeatureIndices(), featureTable.getNumberOfFeatures(), params.getCreatableFile("learner.featureIndicesFile"));
    writeWeightsToFile(gd.getWeights(), params.getCreatableFile("learner.weightsFile"));
    */
  }

  // accuracy according to current hypothesis
  public static double accuracy(final Hypothesis hypothesis, final double[] weights) {
    int correctCount = 0;
    int tp = 0;     // true positive
    int tn = 0;     // true negative

    for(final PairedRealInstance x : hypothesis.getExamples()) {
      final int y = x.getLabel();
      final double hx = hypothesis.value(x, weights);

      if(y==0 && hx<0.5) {
        tn += 1;
        //correctCount += 1;
      } else if(y==1 && hx>=0.5) {
        tp += 1;
        //correctCount += 1;
      }
    }

    log.info("TP={}, TN={}", tp, tn);
    return (double)(tp+tn)/(double)hypothesis.getNumberOfExamples();
  }

  /*
  private static ImmutableMap<Symbol, Symbol> filterByFeatureDim(final ImmutableMap<Symbol, Symbol> targetMemberIdsLabels,
      final FeatureTable featureTable, final int featureDimThreshold) {
    final ImmutableMap.Builder<Symbol, Symbol> ret = ImmutableMap.builder();

    final ImmutableTable<Symbol, Integer, Double> featureWeights = featureTable.getFeatureWeights();

    for(final Map.Entry<Symbol, Symbol> idLabel : targetMemberIdsLabels.entrySet()) {
      final Symbol id = idLabel.getKey();
      final Symbol label = idLabel.getValue();

      if(featureWeights.row(id).size() >= featureDimThreshold) {
        ret.put(id, label);
      }
    }

    return ret.build();
  }
  */

  private static void writeFeatureIndicesToFile(final ImmutableMap<Integer, String> featureIndices, final int numberOfFeatures,
      final File outfile) throws IOException {
    StringBuffer s = new StringBuffer("");

    for(int i=1; i<=numberOfFeatures; i++) {
      s.append(i);
      s.append("\t");
      s.append(featureIndices.get(i));
      s.append("\n");
    }

    Files.write(s.toString(), outfile, Charsets.UTF_8);
  }

  private static void writeWeightsToFile(final double[] weights, final File outfile) throws IOException {
    StringBuffer s = new StringBuffer("");

    for(int i=0; i<weights.length; i++) {
      s.append(i);
      s.append("\t");
      s.append(weights[i]);
      s.append("\n");
    }

    //log.info("Weights\n {}", s.toString());

    Files.write(s.toString(), outfile, Charsets.UTF_8);
  }


  public static ImmutableList<PairedRealInstance> constructPairInstances(final ImmutableSet<SymbolPair> idPairs,
      final ImmutableMap<Symbol, WeightedRealVector> examples, final int label) {
    final ImmutableList.Builder<PairedRealInstance> ret = ImmutableList.builder();

    /*
    for(final SymbolPair idPair : idPairs) {
      final Symbol id1 = idPair.getFirstMember();
      final Symbol id2 = idPair.getSecondMember();

      final WeightedRealVector v1 = examples.get(id1);
      final WeightedRealVector v2 = examples.get(id2);

      ret.add(PairedRealInstance.from(label, v1, v2));
    }
    */

    return ret.build();
  }


  public static ImmutableMap<Symbol, WeightedRealVector> toWeightedRealVectors(final ImmutableTable<Symbol, Integer, Double> featureWeights,
      final Optional<Integer> dimThreshold, final int numberOfFeatures, final double initialWeight) {
    final ImmutableMap.Builder<Symbol, WeightedRealVector> ret = ImmutableMap.builder();

    double[] weights = new double[numberOfFeatures+1];  // pad index 0 for bias
    Arrays.fill(weights, initialWeight);                          // so that vector norm does not go to zero

    final ImmutableMap<Integer, Double> biasFeature = ImmutableMap.of(0, 1.0);

    for(final Symbol item : featureWeights.rowKeySet()) {
      final ImmutableMap<Integer, Double> features = featureWeights.row(item);

      if( (dimThreshold.isPresent() && features.size() >= dimThreshold.get()) || !dimThreshold.isPresent() ) {
        final ImmutableMap<Integer, Double> newFeatures = ImmutableMap.<Integer, Double>builder()
            .putAll(biasFeature).putAll(features).build();

        final WeightedRealVector v = WeightedRealVector.weightedBuilder(false, weights).withElements(newFeatures).build();
        ret.put(item, v);
      }
    }

    return ret.build();
  }

  private static ImmutableMap<Symbol, Symbol> readMemberLabel(final File infile) throws IOException {
    final ImmutableMap.Builder<Symbol, Symbol> ret = ImmutableMap.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for(final String line : lines) {
      final String[] tokens = line.split("\t");
      final String instanceId = tokens[0];
      final String label = tokens[1];

      ret.put(Symbol.from(instanceId), Symbol.from(label));
    }

    return ret.build();
  }



}

