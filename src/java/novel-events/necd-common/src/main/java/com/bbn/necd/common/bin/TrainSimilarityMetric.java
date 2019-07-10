package com.bbn.necd.common.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.hypothesis.Hypothesis;
import com.bbn.necd.common.learner.GradientDescent;
import com.bbn.necd.common.metric.SimilarityMetric;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.FactoredRealVectorPair;
import com.bbn.necd.common.theory.FeatureTable;
import com.bbn.necd.common.theory.PairedRealInstance;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Map;

/**
 * Created by ychan on 1/27/16.

 Parameters:
 - learner.log
 - memberPair.label
 - metricType
 - learner.output.featureIndicesFile
 - learner.output.weightsFile
 - * from GradientDescent
 */
public final class TrainSimilarityMetric {
  private static final Logger log = LoggerFactory.getLogger(TrainSimilarityMetric.class);

  private final RealInstanceManager realInstanceManager;
  private final ImmutableList<PairedRealInstance> examples;
  private final GradientDescent gd;
  private Hypothesis hypothesis;
  private final String featureIndicesOutputFile;
  private final String weightsOutputFile;
  private final File logFile;
  private final boolean writeModel;

  private TrainSimilarityMetric(final RealInstanceManager realInstanceManager,
      final ImmutableList<PairedRealInstance> examples, final GradientDescent gd,
      Hypothesis hypothesis, final String featureIndicesOutputFile, final String weightsOutputFile,
      final File logFile, final boolean writeModel) {
    this.realInstanceManager = realInstanceManager;
    this.examples = examples;
    this.gd = gd;
    this.hypothesis = hypothesis;
    this.featureIndicesOutputFile = featureIndicesOutputFile;
    this.weightsOutputFile = weightsOutputFile;
    this.logFile = logFile;
    this.writeModel = writeModel;
  }

  public static TrainSimilarityMetric from(final Parameters params, final RealInstanceManager realInstanceManager)
      throws IOException {

    final File logFile = params.getCreatableFile("learner.log");

    final ImmutableMap<SymbolPair, Symbol> pairLabels = readPairLabel(params.getExistingFile("memberPair.label"));
    // pairLabels form our training set, but we need to filter by the instances that actually get
    // instantiated by RealInstanceManager. For instance, it only instantiates those that passes
    // the feature dim threshold
    final ImmutableMap<SymbolPair, Symbol> filteredPairLabels = filterByHasPairInstances(pairLabels, realInstanceManager);
    log.info("Going to train on {} out of {} total examples", filteredPairLabels.keySet().size(), pairLabels.keySet().size());

    final ImmutableList<PairedRealInstance> examples = constructPairInstances(filteredPairLabels, realInstanceManager);

    final SimilarityMetric.MetricType metricType = params.getEnum("metricType", SimilarityMetric.MetricType.class);
    Hypothesis hypothesis = metricType.hypothesisFrom(examples, realInstanceManager.getWeights());

    final GradientDescent gd = GradientDescent.builder(params)
        .withWeights(realInstanceManager.getWeights()).build();

    final String featureIndicesOutputFile = params.getString("learner.output.featureIndicesFile");
    final String weightsOutputFile = params.getString("learner.output.weightsFile");

    final boolean writeModel = params.getBoolean("learner.writeModel");

    return new TrainSimilarityMetric(realInstanceManager, examples, gd, hypothesis, featureIndicesOutputFile, weightsOutputFile, logFile, writeModel);
  }

  public void run() throws IOException {
    final Optional<File> hxLogFile = gd.loggingHx() ? Optional.of(new File(logFile.getPath()+".gd.start.hx")) : Optional.<File>absent();
    log.info("Starting pairwiseF {}", gd.pairwiseF(hypothesis, gd.getWeights(), hxLogFile));

    gd.batchLearn(hypothesis, logFile);

    if(writeModel) {
      writeFeatureIndicesToFile(realInstanceManager.getFeatureTable(), new File(featureIndicesOutputFile));
      writeWeightsToFile(gd.getWeights(), new File(weightsOutputFile));
    }

  }

  /*
  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    //final Optional<Integer> featureDimThreshold = params.getOptionalInteger("feature.featureDimThreshold");
    //final double learningRate = params.getDouble("learner.learningRate");
    //final double regularizationCoefficient = params.getDouble("learner.regularizationCoefficient");
    //final int maxIterations = params.getInteger("learner.iterations");

    //final double initialWeight = params.getDouble("learner.initialWeight");     // either 0 or 1

    final File logFile = params.getCreatableFile("learner.log");
    final Optional<Integer> batchSize = params.getOptionalInteger("learner.batchSize");

    final SimilarityMetric.MetricType
        metricType = params.getEnum("metricType", SimilarityMetric.MetricType.class);



    final RealInstanceManager realInstanceManager = RealInstanceManager.from(params);

    final ImmutableMap<SymbolPair, Symbol> pairLabels = readPairLabel(params.getExistingFile("memberPair.label"));
    // pairLabels form our training set, but we need to filter by the instances that actually get
    // instantiated by RealInstanceManager. For instance, it only instantiates those that passes
    // the feature dim threshold
    final ImmutableMap<SymbolPair, Symbol> filteredPairLabels = filterByHasPairInstances(pairLabels, realInstanceManager);
    log.info("Going to train on {} out of {} total examples", filteredPairLabels.keySet().size(), pairLabels.keySet().size());


    final ImmutableList<PairedRealInstance> examples = constructPairInstances(filteredPairLabels, realInstanceManager);

    //final double[] weights = GradientDescent
    //    .toWeights(realInstanceManager.getFeatureTable().getNumberOfFeatures(), initialWeight);

    Hypothesis hypothesis = metricType.hypothesisFrom(examples, realInstanceManager.getWeights());
    //hypothesis.updateCache(weights);

    final GradientDescent gd = GradientDescent.builder(params)
        .withWeights(realInstanceManager.getWeights()).build();

    //log.info("Starting accuracy {}", gd.accuracy(hypothesis, gd.getWeights(), new File(logDir+"/gd.0.hx")));
    log.info("Starting pairwiseF {}", gd.pairwiseF(hypothesis, gd.getWeights()));

    if(batchSize.isPresent()) {
      //gd.miniBatchLearn(hypothesis, logDir, batchSize.get());
    } else {
      gd.batchLearn(hypothesis, logFile);
    }

    //final DecimalFormat df = new DecimalFormat("#.###");
    //String previousLossString = "";
    //for(int iteration=1; iteration<=maxIterations; iteration++) {
    //  final ImmutableList<String> lossStrings = gd.batchLearn(hypothesis);
    //  Files.asCharSink(new File(logDir+"/gd."+iteration+".loss"), Charsets.UTF_8).writeLines(lossStrings);

    //  final double loss = gd.currentLoss(hypothesis);
    //  hypothesis = hypothesis.copyWithWeights(gd.getWeights());

    //  final File hxLogFile = new File(logDir+"/gd."+iteration+".hx");
    //  log.info("GD iteration {}, loss={}, accuracy={}", iteration, loss, accuracy(hypothesis, gd.getWeights(), hxLogFile));

    //  writeWeightsToFile(gd.getWeights(), new File(logDir+"/gd."+iteration+".weights"));

    //  final String currentLossString = df.format(loss);
    //  if(previousLossString.compareTo(currentLossString)==0) {
        //  break;
    //  } else {
    //    previousLossString = currentLossString;
    //  }
    //}

    writeFeatureIndicesToFile(realInstanceManager.getFeatureTable(), params.getCreatableFile("learner.output.featureIndicesFile"));
    writeWeightsToFile(gd.getWeights(), params.getCreatableFile("learner.output.weightsFile"));

  }
  */

  // accuracy according to current hypothesis
  public static double accuracy(final Hypothesis hypothesis, final double[] weights, final File hxLogFile) throws  IOException {
    int correctCount = 0;
    int tp = 0;     // true positive
    int tn = 0;     // true negative

    final ImmutableList.Builder<String> lines = ImmutableList.builder();
    for(final PairedRealInstance x : hypothesis.getExamples()) {
      final int y = x.getLabel();
      final double hx = hypothesis.value(x, weights);

      //if(Double.isNaN(hx)) {
      //  log.info("label={} idPair={},{}", y, x.getIdPair().getFirstMember().asString(), x.getIdPair().getSecondMember().asString());
      //  log.info("V1 = {}", x.getFirstMember().toString());
      //  log.info("V2 = {}", x.getSecondMember().toString());
      //  System.exit(0);
      //}

      StringBuilder sb = new StringBuilder();
      sb.append(x.getIdPair().getFirstMember().asString() + " ");
      sb.append(x.getIdPair().getSecondMember().asString() + " ");
      sb.append(y + " ");
      sb.append(hx);
      lines.add(sb.toString());

      if(y==0 && hx<0.5) {
        tn += 1;
        //correctCount += 1;
      } else if(y==1 && hx>=0.5) {
        tp += 1;
        //correctCount += 1;
      }
    }

    Files.asCharSink(hxLogFile, Charsets.UTF_8).writeLines(lines.build());

    log.info("TP={}, TN={}", tp, tn);
    return (double)(tp+tn)/(double)hypothesis.getNumberOfExamples();
  }

  public static void writeFeatureIndicesToFile(final FeatureTable featureTable,
      final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    final BiMap<Integer, String> featureIndices = featureTable.getFeatureIndices().inverse();
    final int numberOfFeatures = featureTable.getNumberOfFeatures();

    for(int i=1; i<=numberOfFeatures; i++) {
      lines.add(i + "\t" + featureIndices.get(i));
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static void writeWeightsToFile(final double[] weights, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    for(int i=0; i<weights.length; i++) {
      lines.add(i + "\t" + weights[i]);
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static ImmutableList<PairedRealInstance> constructPairInstances(final ImmutableMap<SymbolPair, Symbol> pairLabels, final RealInstanceManager realInstanceManager) {
    final ImmutableList.Builder<PairedRealInstance> ret = ImmutableList.builder();

    final ImmutableMap<SymbolPair, FactoredRealVectorPair> pairInstances = realInstanceManager.getPairInstances();

    for(final Map.Entry<SymbolPair, Symbol> entry : pairLabels.entrySet()) {
      final SymbolPair idPair = entry.getKey();
      final int label = Integer.valueOf(entry.getValue().asString()); // either 0 or 1

      final FactoredRealVectorPair vPair = pairInstances.get(idPair);
      ret.add(PairedRealInstance.from(label, vPair.getFirstVector(), vPair.getSecondVector(), idPair));
    }

    return ret.build();
  }

  private static ImmutableMap<SymbolPair, Symbol> filterByHasPairInstances(final ImmutableMap<SymbolPair, Symbol> pairLabels, final RealInstanceManager realInstanceManager) {
    final ImmutableMap.Builder<SymbolPair, Symbol> ret = ImmutableMap.builder();

    final ImmutableSet<SymbolPair> targetIds = realInstanceManager.hasPairInstances(pairLabels.keySet());
    for(final Map.Entry<SymbolPair, Symbol> entry : pairLabels.entrySet()) {
      if(targetIds.contains(entry.getKey())) {
        ret.put(entry);
      }
    }

    return ret.build();
  }

  public static ImmutableMap<SymbolPair, Symbol> readPairLabel(final File infile)
      throws IOException {
    final ImmutableMap.Builder<SymbolPair, Symbol> ret = ImmutableMap.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      final SymbolPair idPair = SymbolPair.from(Symbol.from(tokens[0]), Symbol.from(tokens[1]));
      final Symbol label = Symbol.from(tokens[2]);
      ret.put(idPair, label);
    }

    return ret.build();
  }
}
