package com.bbn.necd.common.learner;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.hypothesis.Hypothesis;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairedRealInstance;
import com.bbn.necd.common.theory.RealVector;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.Arrays;
import java.util.List;

/*
    Parameters:
    - learner.learningRate
    - learner.regularizationCoefficient
    - learner.iterations
    - learner.positiveWeight
    - learner.annealingT
*/
public final class GradientDescent {
  private static final Logger log = LoggerFactory.getLogger(GradientDescent.class);

  private double[] weights;               // we assume the weight at index 0 is the bias ; NOTE: i.e. all feature vectors index 0 have the value 1
  private final double learningRate;
  private final double regularizationCoefficient;
  private final int maxIterations;
  private final double positiveWeight;
  private final int annealingT;
  //private final ImmutableMultimap<Integer, SymbolPair> indexToExampleId;
  //private final ImmutableMap<Symbol, int[]> factorIndices;
  private final List<String> logLines;
  private final boolean loggingHx;
  private final boolean loggingLoss;
  private final boolean loggingWeights;
  private final boolean normalizeWeights;
  private final boolean clipWeights;

  private GradientDescent(final double learningRate, final double regularizationCoefficient,
      final int maxIterations, final double positiveWeight, final int annealingT,
      final double[] weights,
      final boolean loggingHx, final boolean loggingLoss, final boolean loggingWeights,
      final boolean normalizeWeights, final boolean clipWeights) {
      //final ImmutableMultimap<Integer, SymbolPair> indexToExampleId,
      //final ImmutableMap<Symbol, int[]> factorIndices) {
    this.learningRate = learningRate;
    this.regularizationCoefficient = regularizationCoefficient;
    this.maxIterations = maxIterations;
    this.positiveWeight = positiveWeight;
    this.annealingT = annealingT;
    this.weights = weights;
    this.logLines = Lists.newArrayList();
    //this.indexToExampleId = indexToExampleId;
    //this.factorIndices = factorIndices;
    this.loggingHx = loggingHx;
    this.loggingLoss = loggingLoss;
    this.loggingWeights = loggingWeights;
    this.normalizeWeights = normalizeWeights;
    this.clipWeights = clipWeights;
  }

  //public static GradientDescent from(final double learningRate, final double regularizationCoefficient, final int numberOfFeatures, final double initialWeight) {
  //  return new GradientDescent(learningRate, regularizationCoefficient, numberOfFeatures, initialWeight);
  //}

  public void forget() {
    Arrays.fill(weights, 0);
  }

  public double[] getWeights() {
    return weights;
  }

  public boolean loggingHx() {
    return loggingHx;
  }

  public boolean loggingLoss() {
    return loggingLoss;
  }

  public boolean loggingWeights() {
    return loggingWeights;
  }

  public double currentLoss(final Hypothesis hypothesis) {
    final ImmutableCollection<PairedRealInstance> examples = hypothesis.getExamples();
    final double N = examples.size();

    double loss = 0;
    for(final PairedRealInstance eg : examples) {
      final double egLoss = hypothesis.logLoss(eg, weights);
      //log.info("idPair {},{} with loss {}", eg.getIdPair().getFirstMember().asString(), eg.getIdPair().getSecondMember().asString(), egLoss);
      if(eg.getLabel()==1) {
        loss += (positiveWeight * egLoss);
      } else {
        loss += egLoss;
      }
    }


    //if(Double.isNaN(loss/N)) {
    //  log.info("total loss is {}", loss);
    //}

    return -1 * loss/N;
  }

  public void batchLearn(Hypothesis hypothesis, final File logFile) throws IOException {
    final DecimalFormat df = new DecimalFormat("#.###");
    String previousLossString = "";
    double previousF = 0;
    long previousLoss = 0;
    for(int iteration=1; iteration<=maxIterations; iteration++) {
      final ImmutableList<String> lossStrings = learn(hypothesis, hypothesis.getExamples().asList(), (iteration-1));
      if(loggingLoss) {
        Files.asCharSink(new File(logFile.getPath() + ".gd." + iteration + ".loss"), Charsets.UTF_8)
            .writeLines(lossStrings);
      }

      final double loss = currentLoss(hypothesis);
      hypothesis = hypothesis.copyWithWeights(getWeights());
      //hypothesis.updateCache(getWeights());

      final Optional<File> hxLogFile = loggingHx ? Optional.of(new File(logFile.getPath()+".gd."+iteration+".hx")) : Optional.<File>absent();
      final double pairwiseF = pairwiseF(hypothesis, getWeights(), hxLogFile);
      log.info("GD iteration {}, loss={}, pairwiseF={}", iteration, loss, pairwiseF);
      logLines.add(String.format("GD iteration %d, loss=%.4f, pairwiseF=%.4f", iteration, loss, pairwiseF));
      //log.info("GD iteration {}", iteration);

      if(loggingWeights) {
        writeWeightsToFile(getWeights(),
            new File(logFile.getPath() + ".gd." + iteration + ".weights"));
      }

      if((iteration>1) && (pairwiseF < previousF)) {
        //break;
      } else {
        previousF = pairwiseF;
      }

      /*
      final long currentLoss = Math.round(loss*1000);
      if((iteration > 1) && (currentLoss >= previousLoss)) {
        //break;
      } else {
        previousLoss = currentLoss;
      }
      */

      /*
      final String currentLossString = df.format(loss);
      if(previousLossString.compareTo(currentLossString)==0) {
        //  break;
      } else {
        previousLossString = currentLossString;
      }
      */

    }

    Files.asCharSink(logFile, Charsets.UTF_8).writeLines(logLines);
  }

  public void miniBatchLearn(Hypothesis hypothesis, final String logDir, final int batchSize) throws IOException {
    final DecimalFormat df = new DecimalFormat("#.###");
    String previousLossString = "";

    final ImmutableList<ImmutableList<PairedRealInstance>> batches = toBatches(hypothesis.getExamples().asList(), batchSize);
    int batchIndex = 0;

    for(int iteration=1; iteration<=maxIterations; iteration++) {
      final ImmutableSet<SymbolPair> trainingIdsForIteration = ImmutableSet.copyOf(Iterables.transform(batches.get(batchIndex), PairedRealInstance.IDPAIR));

      final ImmutableList<String> lossStrings = learn(hypothesis, hypothesis.getExamplesByIds(trainingIdsForIteration), (iteration-1));
      if(loggingLoss) {
        Files.asCharSink(new File(logDir + "/gd." + iteration + ".loss"), Charsets.UTF_8)
            .writeLines(lossStrings);
      }


      final double loss = currentLoss(hypothesis);
      hypothesis = hypothesis.copyWithWeights(getWeights());

      final Optional<File> hxLogFile = loggingHx ? Optional.of(new File(logDir+"/gd."+iteration+".hx")) : Optional.<File>absent();
      log.info("GD iteration {}, loss={}, pairwiseF={}", iteration, loss, pairwiseF(hypothesis, getWeights(), hxLogFile));

      if(loggingWeights) {
        writeWeightsToFile(getWeights(), new File(logDir + "/gd." + iteration + ".weights"));
      }

      final String currentLossString = df.format(loss);
      if(previousLossString.compareTo(currentLossString)==0) {
        //  break;
      } else {
        previousLossString = currentLossString;
      }

      batchIndex += 1;
      if(batchIndex >= batches.size()) {
        batchIndex = 0;
      }
    }
  }

  public ImmutableList<String> learn(final Hypothesis hypothesis, final ImmutableList<PairedRealInstance> examples, final int iterationIndex) {
    final ImmutableList.Builder<String> lossStringBuilder = ImmutableList.builder();

    final double N = examples.size();
    double[] newWeights = new double[weights.length];
    double[] losses = new double[weights.length];

    for (final PairedRealInstance example : examples) {
      final ImmutableMap<Symbol, RealVector> v1Factors = example.getFirstMember().getFactors();
      final ImmutableMap<Symbol, RealVector> v2Factors = example.getSecondMember().getFactors();

      final ImmutableSet<Symbol> commonFactors =
          Sets.intersection(v1Factors.keySet(), v2Factors.keySet()).immutableCopy();

      for (final Symbol factor : commonFactors) {
        final RealVector v1 = v1Factors.get(factor);
        final RealVector v2 = v2Factors.get(factor);

        final ImmutableMap<Integer, Double> v1Elements = v1.getElements();
        final ImmutableMap<Integer, Double> v2Elements = v2.getElements();

        final ImmutableSet<Integer> commonIndices =
            Sets.intersection(v1Elements.keySet(), v2Elements.keySet()).immutableCopy();

        //final ImmutableMap.Builder<Integer, Double> lossBuilder = ImmutableMap.builder();
        for (final Integer index : commonIndices) {
          final double fv1 = v1Elements.get(index);
          final double fv2 = v2Elements.get(index);
          final double indexLoss = hypothesis.logLossDerivative(example, fv1, fv2);

          if(example.getLabel()==1) {
            losses[index] += (positiveWeight * indexLoss);
          } else {
            losses[index] += indexLoss;
          }
          //lossBuilder.put(index, indexLoss);
        }
      }
    }

    final double currentLearningRate = learningRate/(1 + (double)iterationIndex/annealingT);
    for(int i=0; i<newWeights.length; i++) {
      if(i==0) {
        newWeights[i] = weights[i] - currentLearningRate * (losses[i]/N);
      } else { 
        newWeights[i] = weights[i] - currentLearningRate * (losses[i]/N + regularizationCoefficient/N*weights[i]);
      }

      lossStringBuilder.add(String.format("OVERALL loss on weightIndex %d is %.4f, weights %.4f -> %.4f",
          i, losses[i], weights[i], newWeights[i]));

      if(clipWeights) {
        if (newWeights[i] > 0) {
          weights[i] = newWeights[i];
        } else {
          weights[i] = 0;
        }
      } else {
        weights[i] = newWeights[i];
      }
    }

    // normalize weights
    if(normalizeWeights) {
      double W = 0;
      for (int i = 0; i < weights.length; i++) {
        W += (weights[i] * weights[i]);
      }
      W = Math.sqrt(W);
      for (int i = 0; i < weights.length; i++) {
        weights[i] = weights[i] / W;
      }
    }


    return lossStringBuilder.build();
  }

  /*
  public ImmutableList<String> learn(final Hypothesis hypothesis, final ImmutableList<PairedRealInstance> examples) {
    final ImmutableList.Builder<String> lossStringBuilder = ImmutableList.builder();

    final double N = examples.size();
    double[] newWeights = new double[weights.length];

    // bias
    double loss = 0;

    if(factorIndices.containsKey(FeatureTable.BIAS)) {
      log.info("BIAS weights");
      for (final PairedRealInstance eg : examples) {
        loss += hypothesis.logLossDerivative(eg, weights, 0, FeatureTable.BIAS);
      }
      newWeights[0] = weights[0] - learningRate * (loss / N);
      lossStringBuilder.add(String
          .format("OVERALL loss on weightIndex %d is %.4f, N={}, weights %.4f -> %.4f", 0, loss, N,
              weights[0], newWeights[0]));
    }

    final ImmutableSet.Builder<SymbolPair> exampleIdsBuilder = ImmutableSet.builder();
    for(final PairedRealInstance eg : examples) {
      exampleIdsBuilder.add(eg.getIdPair());
    }
    final ImmutableSet<SymbolPair> exampleIds = exampleIdsBuilder.build();

    for(final Map.Entry<Symbol, int[]> factorEntry : factorIndices.entrySet()) {
      final Symbol factorType = factorEntry.getKey();
      final int[] factorInt = factorEntry.getValue();

      log.info("{} weights", factorType.asString());
      for(int index=0; index<factorInt.length; index++) {
        final int weightIndex = factorInt[index];

        loss = 0;
        for(final SymbolPair egId : Sets.intersection(ImmutableSet.copyOf(indexToExampleId.get(weightIndex)), exampleIds)) {
          final double egLoss = hypothesis.logLossDerivative(hypothesis.getExampleById(egId), weights, weightIndex, factorType);
          loss += egLoss;
        }
        newWeights[weightIndex] = weights[weightIndex] -
            learningRate * (loss/N + regularizationCoefficient/N*weights[weightIndex]);
        lossStringBuilder.add(String.format("OVERALL loss on weightIndex %d is %.4f, weights %.4f -> %.4f",
            weightIndex, loss, weights[weightIndex], newWeights[weightIndex]));
      }
    }


    //for(int weightIndex=1; weightIndex<weights.length; weightIndex++) {
    //  loss = 0;
    //  for(final SymbolPair egId : Sets.intersection(ImmutableSet.copyOf(indexToExampleId.get(weightIndex)), exampleIds)) {
    //    final double egLoss = hypothesis.logLossDerivative(hypothesis.getExampleById(egId), weights, weightIndex);
    //    loss += egLoss;
    //  }
    //  newWeights[weightIndex] = weights[weightIndex] -
    //      learningRate * (loss/N + regularizationCoefficient/N*weights[weightIndex]);
    //  lossStringBuilder.add(String.format("OVERALL loss on weightIndex %d is %.4f, weights %.4f -> %.4f",
    //      weightIndex, loss, weights[weightIndex], newWeights[weightIndex]));
    //}


    for(int i=0; i<newWeights.length; i++) {
      if(newWeights[i] > 0) {
        weights[i] = newWeights[i];
      } else {
        weights[i] = 0;
      }

    }

    return lossStringBuilder.build();
  }
  */

  /*
  public ImmutableList<String> learn(final Hypothesis hypothesis) {
    final ImmutableList.Builder<String> lossStringBuilder = ImmutableList.builder();
    //final ImmutableList.Builder<String> egLossStringBuilder = ImmutableList.builder();

    final ImmutableCollection<PairedRealInstance> examples = hypothesis.getExamples();
    final double N = examples.size();

    //log.info("Learning with {} examples and {} weights", N, weights.length);

    double[] newWeights = new double[weights.length];

    // bias
    double loss = 0;
    for(final PairedRealInstance eg : examples) {
      loss += hypothesis.logLossDerivative(eg, weights, 0);
    }
    //log.info("loss on bias {}", loss);
    newWeights[0] = weights[0] - learningRate * (loss/N);
    lossStringBuilder.add(String.format("OVERALL loss on weightIndex %d is %.4f, N={}, weights %.4f -> %.4f", 0, loss, N, weights[0], newWeights[0]));


    for(int weightIndex=1; weightIndex<weights.length; weightIndex++) {
      loss = 0;
      for(final SymbolPair egId : indexToExampleId.get(weightIndex)) {
        final double egLoss = hypothesis.logLossDerivative(hypothesis.getExampleById(egId), weights, weightIndex);
        //log.info("egId {},{} loss {}", egId.getFirstMember().asString(), egId.getSecondMember().asString(), egLoss);
        //lossStringBuilder.add(String.format("loss on weightIndex %d eg %s,%s is %.4f", weightIndex, egId.getFirstMember().asString(), egId.getSecondMember().asString(), egLoss));
        loss += egLoss;
      }
      newWeights[weightIndex] = weights[weightIndex] - learningRate * (loss/N + regularizationCoefficient/N*weights[weightIndex]);
      lossStringBuilder.add(String.format("OVERALL loss on weightIndex %d is %.4f, weights %.4f -> %.4f", weightIndex, loss, weights[weightIndex], newWeights[weightIndex]));
      //log.info("loss on weightIndex {}={}, weights:{}->{}", weightIndex, loss, weights[weightIndex], newWeights[weightIndex]);

      //if((weightIndex % 2500)==0) {
      //  log.info("weightIndex {}", weightIndex);
      //}
    }

    for(int i=0; i<newWeights.length; i++) {
      if(newWeights[i] > 0) {
        weights[i] = newWeights[i];
      } else {
        weights[i] = 0;
      }

    }

    return lossStringBuilder.build();
  }
  */

  private ImmutableList<ImmutableList<PairedRealInstance>> toBatches(final ImmutableList<PairedRealInstance> examples, final int batchSize) {
    final ImmutableList.Builder<ImmutableList<PairedRealInstance>> ret = ImmutableList.builder();

    for(int i=0; i<examples.size(); i++) {
      final int startIndex = i;               // inclusive
      int endIndex = startIndex + batchSize -1;  // inclusive

      if((endIndex+batchSize) >= examples.size()) {
        endIndex = examples.size()-1;
      }

      final ImmutableList.Builder<PairedRealInstance> batchExamples = ImmutableList.builder();
      for(int j=startIndex; j<=endIndex; j++) {
        batchExamples.add(examples.get(j));
      }
      ret.add(batchExamples.build());
    }

    return ret.build();
  }




  public static double[] toWeights(final int numberOfFeatures, final double initialWeight) {
    final double[] weights = new double[numberOfFeatures+1];   // add 1 for bias
    Arrays.fill(weights, initialWeight);
    return weights;
  }

  public static ImmutableMultimap<Integer, SymbolPair> indexToExampleId(final ImmutableList<PairedRealInstance> examples, final int maxIndex) {
    final ImmutableMultimap.Builder<Integer, SymbolPair> ret = ImmutableMultimap.builder();

    // index 0 is bias, which involves all examples. Therefore, we start capturing from index 1
    for(int weightIndex=1; weightIndex<maxIndex; weightIndex++) {
      for(final PairedRealInstance eg : examples) {
        if(eg.hasIndex(weightIndex)) {
          ret.put(weightIndex, eg.getIdPair());
        }
      }
    }

    return ret.build();
  }

  // accuracy according to current hypothesis
  public double pairwiseF(final Hypothesis hypothesis, final double[] weights, final Optional<File> hxLogFile) throws IOException {
    int correctCount = 0;
    int tp = 0;     // true positive
    int tn = 0;     // true negative
    int pp = 0;     // prediction positive
    int pn = 0;     // prediction negative
    int positiveCount = 0;

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

      if(y==1) {
        positiveCount += 1;
      }

      if(hx < 0.5) {
        pn += 1;
      } else {
        pp += 1;
      }

      if(y==0 && hx<0.5) {
        tn += 1;
        //correctCount += 1;
      } else if(y==1 && hx>=0.5) {
        tp += 1;
        //correctCount += 1;
      }
    }

    if(hxLogFile.isPresent()) {
      Files.asCharSink(hxLogFile.get(), Charsets.UTF_8).writeLines(lines.build());
    }

    final double rec = (double)tp/positiveCount;
    final double pre = (double)tp/pp;
    final double f1 = (2*pre*rec)/(pre+rec);

    log.info("PP={}, TP={}, PN={}, TN={}, P={}, R,P,F1=({},{},{})", pp, tp, pn, tn, positiveCount, String.format("%.3f",rec), String.format("%.3f",pre), String.format("%.3f",f1));
    logLines.add(String.format("PP=%d TP=%d PN=%d TN=%d P=%d R,P,F1=(%.3f,%.3f,%.3f)", pp, tp, pn, tn, positiveCount, rec, pre, f1));

    return f1;
    //return (double)(tp+tn)/(double)hypothesis.getNumberOfExamples();
  }

  private static void writeWeightsToFile(final double[] weights, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    for(int i=0; i<weights.length; i++) {
      lines.add(i + "\t" + weights[i]);
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }


  public static Builder builder(final Parameters params) {
    return new Builder(params);
  }

  public static final class Builder {
    private final double learningRate;
    private final double regularizationCoefficient;
    private final int maxIterations;
    private final double positiveWeight;
    private double[] weights;
    private final int annealingT;
    //private ImmutableMultimap<Integer, SymbolPair> indexToExampleId;
    //private ImmutableMap<Symbol, int[]> factorIndices;
    private boolean loggingHx;
    private boolean loggingLoss;
    private boolean loggingWeights;
    private boolean normalizeWeights;
    private boolean clipWeights;

    private Builder(final Parameters params) {
      this.learningRate = params.getDouble("learner.learningRate");
      this.regularizationCoefficient = params.getDouble("learner.regularizationCoefficient");
      this.maxIterations = params.getInteger("learner.iterations");
      this.positiveWeight = params.getDouble("learner.positiveWeight");
      this.annealingT = params.getInteger("learner.annealingT");
      this.loggingHx = params.getBoolean("learner.loggingHx");
      this.loggingLoss = params.getBoolean("learner.loggingLoss");
      this.loggingWeights = params.getBoolean("learner.loggingWeights");
      this.normalizeWeights = params.getBoolean("learner.normalizeWeights");  // normalize weights during each GD iteration
      this.clipWeights = params.getBoolean("learner.clipWeights");  // whether to clip the weights to at least 0
    }

    public Builder withWeights(final double[] weights) {
      this.weights = new double[weights.length];
      for(int i=0; i<weights.length; i++) {
        this.weights[i] = weights[i];
      }
      return this;
    }

    /*
    public Builder withIndexToExampleId(final ImmutableMultimap<Integer, SymbolPair> indexToExampleId) {
      this.indexToExampleId = indexToExampleId;
      return this;
    }

    public Builder withFactorIndices(final ImmutableMap<Symbol, int[]> factorIndices) {
      this.factorIndices = factorIndices;
      return this;
    }
    */

    public GradientDescent build() {
      return new GradientDescent(learningRate, regularizationCoefficient, maxIterations,
          positiveWeight, annealingT, weights,
          loggingHx, loggingLoss, loggingWeights, normalizeWeights, clipWeights);
    }


  }
}
