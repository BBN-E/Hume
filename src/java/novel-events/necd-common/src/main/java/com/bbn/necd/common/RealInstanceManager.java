package com.bbn.necd.common;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.FactoredRealVectorPair;
import com.bbn.necd.common.theory.FeatureTable;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.RealVectorPair;
import com.bbn.necd.common.theory.WeightedRealVector;
import com.bbn.necd.common.theory.WeightedRealVectorPair;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Map;

/*
   Parameters:
   - targetMembers.list
   - learner.useBias
   - feature.exampleType
*/
public final class RealInstanceManager {

  private static final Logger log = LoggerFactory.getLogger(RealInstanceManager.class);

  private final double[] weights;

  // either pairInstances or singleInstances will be present
  private final Optional<ImmutableMap<SymbolPair, FactoredRealVectorPair>> pairInstances;
  private final Optional<ImmutableMap<Symbol, FactoredRealVector>> singleInstances;

  private final FeatureTable featureTable;

  private RealInstanceManager(final double[] weights,
      final ImmutableMap<SymbolPair, FactoredRealVectorPair> pairInstances,
      final ImmutableMap<Symbol, FactoredRealVector> singleInstances,
      final FeatureTable featureTable) {
    this.weights = weights;
    this.pairInstances = Optional.fromNullable(pairInstances);
    this.singleInstances = Optional.fromNullable(singleInstances);
    this.featureTable = featureTable;
  }

  public double[] getWeights() {
    return weights;
  }

  //public ImmutableMap<Symbol, RealVector> getInstances() {
  //  return instances;
  //}

  public ImmutableMap<SymbolPair, FactoredRealVectorPair> getPairInstances() {
    return pairInstances.get();
  }

  public ImmutableMap<Symbol, FactoredRealVector> getSingleInstances() {
    return singleInstances.get();
  }

  public FeatureTable getFeatureTable() {
    return featureTable;
  }

  public static RealInstanceManager from(final Parameters params, final FeatureTable featureTable)
      throws IOException {

    //final Optional<Integer> featureDimThreshold =
    //    params.getOptionalInteger("feature.featureDimThreshold");

    final ImmutableSet<Symbol> targetMemberIds = readTargetMembers(params.getExistingFile("targetMembers.list"));

    //final ImmutableList<SymbolPair> targetIdPairs = readPairIds(params.getExistingFile("memberPair.list"));

    final double[] weights = featureTable.getWeights();

    final ImmutableMap<Symbol, RealVector> biasInstances =
        params.getBoolean("learner.useBias") ? toBiasRealVectors(targetMemberIds, weights)
                                             : ImmutableMap.<Symbol, RealVector>of();

    //final ImmutableMap<Symbol, RealVector> instances =
    //    toWeightedRealVectors(featureTable.getFeatureWeights(), weights);

    //final ImmutableMap<SymbolPair, RealVectorPair> pairInstances =
    //    toWeightedRealVectorsPair(featureTable.getPairwiseFeatureWeights(), weights);

    //final ImmutableMap<SymbolPair, RealVectorPair> maxSimWordPairInstances =
    //    maxSimWordsToWeightedRealVectorsPair(params.getExistingFile("feature.maxSimWordFile"),
    //        predictVectorManager, weights, featureTable.getFeatureStringToIndex());


    //if(params.isPresent("log.maxSimWordPairInstances")) {
    //  logVectorPairInstances(maxSimWordPairInstances,
    //      params.getCreatableFile("log.maxSimWordPairInstances"));
    //  log.info("logged maxSimWordPairInstances");
    //}

    FeatureTable.ExampleType exampleType = params.getEnum("feature.exampleType", FeatureTable.ExampleType.class);

    switch(exampleType) {
      case PAIR:
        final ImmutableMap<SymbolPair, FactoredRealVectorPair> factoredPairInstances = toFactoredRealVectorsPair(biasInstances, featureTable);
        log.info("Produced factoredPairInstances");
        return new RealInstanceManager(weights, factoredPairInstances, null, featureTable);
      case SINGLE:
        final ImmutableMap<Symbol, FactoredRealVector> factoredSingleInstances = toFactoredRealVectors(biasInstances, featureTable);
        log.info("Produced factoredSingleInstances");
        return new RealInstanceManager(weights, null, factoredSingleInstances, featureTable);
      default:
        throw new IllegalArgumentException("Unknown feature.exampleType");
    }
  }

  private static void logVectorPairInstances(final ImmutableMap<SymbolPair, RealVectorPair> instances, final File outfile) throws IOException {
    final ImmutableList.Builder<String> linesBuilder = ImmutableList.builder();

    for(final Map.Entry<SymbolPair, RealVectorPair> entry : instances.entrySet()) {
      linesBuilder.add(entry.getKey().getFirstMember().asString() + " " + entry.getKey().getSecondMember().asString());
      linesBuilder.add("<RealVectorPair>");
      linesBuilder.add("<v1>");
      linesBuilder.add(entry.getValue().getFirstVector().toString());
      linesBuilder.add("</v1>");
      linesBuilder.add("<v2>");
      linesBuilder.add(entry.getValue().getFirstVector().toString());
      linesBuilder.add("</v2>");
      linesBuilder.add("</RealVectorPair>");
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(linesBuilder.build());
  }

  private static void logFactoredPairInstances(final ImmutableMap<SymbolPair, FactoredRealVectorPair> factoredPairInstances, final File outfile) throws IOException {
    final ImmutableList.Builder<String> linesBuilder = ImmutableList.builder();

    for(final Map.Entry<SymbolPair, FactoredRealVectorPair> entry : factoredPairInstances.entrySet()) {
      linesBuilder.add(entry.getKey().getFirstMember().asString() + " " + entry.getKey().getSecondMember().asString());
      linesBuilder.add(entry.getValue().toString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(linesBuilder.build());
  }

  public static double[] prepareWeights(final Optional<File> weightsFile,
      final Optional<Double> initialWeight, final int numberOfFeatures, final boolean useBias) throws IOException {
    double[] weights;

    if (weightsFile.isPresent()) {
      final ImmutableList<String> lines =
          Files.asCharSource(weightsFile.get(), Charsets.UTF_8).readLines();
      weights = new double[lines.size()];
      for (final String line : lines) {
        final String[] tokens = line.split("\t");
        final int index = new Integer(tokens[0]).intValue();
        weights[index] = new Double(tokens[1]).doubleValue();  // weight value
      }
    } else {
      weights = new double[numberOfFeatures + 1];
      if(initialWeight.isPresent()) {
        Arrays.fill(weights, initialWeight.get());
        if(!useBias) {
          weights[0] = 0;
        }
      } else {
        Arrays.fill(weights, 1.0);
        // since there is no weight file, there is no bias term. Hence set weight of bias to 0
        weights[0] = 0;
      }
    }

    return weights;
  }

  public static ImmutableMap<Symbol, RealVector> toBiasRealVectors(final ImmutableSet<Symbol> items, final double[] weights) {
    final ImmutableMap.Builder<Symbol, RealVector> ret = ImmutableMap.builder();

    // prepare bias feature at index 0, with value of 1
    final ImmutableMap<Integer, Double> biasFeature = ImmutableMap.of(FeatureTable.biasFeatureIndex, 1.0);

    final WeightedRealVector v =
        WeightedRealVector.weightedBuilder(false, weights).withElements(biasFeature).build();

    for(final Symbol item : items) {
      ret.put(item, v);
    }

    return ret.build();
  }

  public static ImmutableMap<Symbol, RealVector> toWeightedRealVectors(
      final ImmutableTable<Symbol, Integer, Double> featureWeights,
      final Optional<Integer> dimThreshold, final double[] weights) {
    final ImmutableMap.Builder<Symbol, RealVector> ret = ImmutableMap.builder();

    //final ImmutableMap<Integer, Double> biasFeature =
    //    ImmutableMap.of(0, 1.0);  // prepare bias feature at index 0, with value of 1

    final Map<ImmutableMap<Integer, Double>, WeightedRealVector> vectorMap = Maps.newHashMap();

    for (final Symbol item : featureWeights.rowKeySet()) {
      final ImmutableMap<Integer, Double> features = featureWeights.row(item);

      if(vectorMap.containsKey(features)) {
        ret.put(item, vectorMap.get(features));
      } else {
        final WeightedRealVector v =
            WeightedRealVector.weightedBuilder(false, weights).withElements(features).build();
        ret.put(item, v);
        vectorMap.put(features, v);
      }
    }

    return ret.build();
  }

  public static ImmutableMap<SymbolPair, RealVectorPair> toWeightedRealVectorsPair(
      final ImmutableTable<SymbolPair, Integer, Double> featureWeights, final double[] weights) {
    final ImmutableMap.Builder<SymbolPair, RealVectorPair> ret = ImmutableMap.builder();

    final Map<ImmutableMap<Integer, Double>, WeightedRealVectorPair> vectorMap = Maps.newHashMap();

    for (final SymbolPair item : featureWeights.rowKeySet()) {
      final ImmutableMap<Integer, Double> features = featureWeights.row(item);

      if(vectorMap.containsKey(features)) {
        ret.put(item, vectorMap.get(features));
      } else {
        final WeightedRealVectorPair
            v = WeightedRealVectorPair.builder(weights).withElements(features).build();
        ret.put(item, v);
        vectorMap.put(features, v);
      }
    }

    log.info("{} unique out of {}", vectorMap.keySet().size(), featureWeights.rowKeySet().size());

    return ret.build();
  }

  public static ImmutableMap<SymbolPair, RealVectorPair> maxSimWordsToWeightedRealVectorsPair(
      final File wordsFile, final PredictVectorManager predictVectorManager, final double[] weights,
      final ImmutableMap<String, Integer> featureStringToIndex) throws IOException {
    final ImmutableMap.Builder<SymbolPair, RealVectorPair> ret = ImmutableMap.builder();

    final ImmutableList<Symbol> featureType = predictVectorManager.getFeatureType();

    final ImmutableList.Builder<Integer> indicesBuilder = ImmutableList.builder();
    for(final Symbol type : featureType) {
      indicesBuilder.add(featureStringToIndex.get(type.asString()));
    }
    final ImmutableList<Integer> indices = indicesBuilder.build();

    //for(int i=0; i<indices.size(); i++) {
    //  log.info("indices {}:{}", i ,indices.get(i));
    //}

    final ImmutableList<String> lines = Files.asCharSource(wordsFile, Charsets.UTF_8).readLines();

    Map<Symbol, WeightedRealVector> wordToVector = Maps.newHashMap();

    for(final String line : lines) {
      final String[] tokens = line.split("\t");
      final SymbolPair item = SymbolPair.from(Symbol.from(tokens[0]), Symbol.from(tokens[1]));
      final Symbol word1 = Symbol.from(tokens[2]);
      final Symbol word2 = Symbol.from(tokens[3]);

      WeightedRealVector v1;
      WeightedRealVector v2;

      if(wordToVector.containsKey(word1)) {
        v1 = wordToVector.get(word1);
      } else {
        final double[] values1 = predictVectorManager.getVector(word1).get().getValues();

        final ImmutableMap.Builder<Integer, Double> features1Builder = ImmutableMap.builder();
        for(int i=0; i<indices.size(); i++) {
          features1Builder.put(indices.get(i), values1[i]);
        }
        final ImmutableMap<Integer, Double> features1 = features1Builder.build();

        v1 = WeightedRealVector.weightedBuilder(false, weights).withElements(features1).build();
        wordToVector.put(word1, v1);
      }

      if(wordToVector.containsKey(word2)) {
        v2 = wordToVector.get(word2);
      } else {
        final double[] values2 = predictVectorManager.getVector(word2).get().getValues();

        final ImmutableMap.Builder<Integer, Double> features2Builder = ImmutableMap.builder();
        for(int i=0; i<indices.size(); i++) {
          features2Builder.put(indices.get(i), values2[i]);
        }
        final ImmutableMap<Integer, Double> features2 = features2Builder.build();

        v2 = WeightedRealVector.weightedBuilder(false, weights).withElements(features2).build();
        wordToVector.put(word2, v2);
      }

      final WeightedRealVectorPair vPair = WeightedRealVectorPair.from(v1, v2);
      ret.put(item, vPair);

    }

    return ret.build();
  }

  public static ImmutableMap<SymbolPair, FactoredRealVectorPair> toFactoredRealVectorsPair(
      final ImmutableMap<Symbol, RealVector> biasInstances,
      final FeatureTable featureTable) {

    final ImmutableMap.Builder<SymbolPair, FactoredRealVectorPair> ret = ImmutableMap.builder();

    final ImmutableTable<SymbolPair, Symbol, RealVectorPair> idPairFeatureTypes = featureTable.getEgPairFeatures().get();
    final ImmutableSet<SymbolPair> targetIdPairs = idPairFeatureTypes.rowKeySet();

    for (final SymbolPair idPair : targetIdPairs) {
      final Symbol id1 = idPair.getFirstMember();
      final Symbol id2 = idPair.getSecondMember();

      final FactoredRealVector.Builder fv1Builder = FactoredRealVector.builder();
      final FactoredRealVector.Builder fv2Builder = FactoredRealVector.builder();

      if (biasInstances.containsKey(id1)) {
        fv1Builder.withFactor(BIAS, biasInstances.get(id1));
      }
      if (biasInstances.containsKey(id2)) {
        fv2Builder.withFactor(BIAS, biasInstances.get(id2));
      }

      final ImmutableMap<Symbol, RealVectorPair> rvPairs = idPairFeatureTypes.row(idPair);
      for (final Map.Entry<Symbol, RealVectorPair> entry : rvPairs.entrySet()) {
        fv1Builder.withFactor(entry.getKey(), entry.getValue().getFirstVector());
        fv2Builder.withFactor(entry.getKey(), entry.getValue().getSecondVector());
      }

      ret.put(idPair, FactoredRealVectorPair.from(fv1Builder.build(), fv2Builder.build()));
    }

    return ret.build();
  }

  public static ImmutableMap<Symbol, FactoredRealVector> toFactoredRealVectors(
      final ImmutableMap<Symbol, RealVector> biasInstances,
      final FeatureTable featureTable) {

    final ImmutableMap.Builder<Symbol, FactoredRealVector> ret = ImmutableMap.builder();

    final ImmutableTable<Symbol, Symbol, RealVector> idFeatureTypes = featureTable.getEgSingleFeatures().get();
    final ImmutableSet<Symbol> targetIds = idFeatureTypes.rowKeySet();

    log.info("Building factored RVs for {} ids", targetIds.size());

    for (final Symbol id : targetIds) {
      final FactoredRealVector.Builder fvBuilder = FactoredRealVector.builder();

      if (biasInstances.containsKey(id)) {
        fvBuilder.withFactor(BIAS, biasInstances.get(id));
      }

      final ImmutableMap<Symbol, RealVector> rv = idFeatureTypes.row(id);
      for (final Map.Entry<Symbol, RealVector> entry : rv.entrySet()) {
        fvBuilder.withFactor(entry.getKey(), entry.getValue());
      }

      ret.put(id, fvBuilder.build());
    }

    return ret.build();
  }

  /*
  public static ImmutableMap<SymbolPair, FactoredRealVectorPair> toFactoredRealVectorsPair(
      final ImmutableList<SymbolPair> targetIdPairs,
      final ImmutableMap<Symbol, RealVector> biasInstances,
      final ImmutableMap<Symbol, RealVector> instances,
      final ImmutableMap<SymbolPair, RealVectorPair> pairInstances,
      final ImmutableMap<SymbolPair, RealVectorPair> maxSimWordPairInstances) {

    final ImmutableMap.Builder<SymbolPair, FactoredRealVectorPair> ret = ImmutableMap.builder();

    for(final SymbolPair idPair : targetIdPairs) {
      final Symbol id1 = idPair.getFirstMember();
      final Symbol id2 = idPair.getSecondMember();

      final FactoredRealVector.Builder fv1Builder = FactoredRealVector.builder();
      final FactoredRealVector.Builder fv2Builder = FactoredRealVector.builder();

      if (biasInstances.containsKey(id1)) {
        fv1Builder.withFactor(FeatureTable.BIAS, biasInstances.get(id1));
      }
      if (biasInstances.containsKey(id2)) {
        fv2Builder.withFactor(FeatureTable.BIAS, biasInstances.get(id2));
      }

      if (instances.containsKey(id1)) {
        fv1Builder.withFactor(FeatureTable.SINGLE, instances.get(id1));
      }
      if (instances.containsKey(id2)) {
        fv2Builder.withFactor(FeatureTable.SINGLE, instances.get(id2));
      }

      if (pairInstances.containsKey(idPair)) {
        final RealVectorPair vectorPair = pairInstances.get(idPair);
        fv1Builder.withFactor(FeatureTable.PAIR, vectorPair.getFirstVector());
        fv2Builder.withFactor(FeatureTable.PAIR, vectorPair.getSecondVector());
      }

      if (maxSimWordPairInstances.containsKey(idPair)) {
        final RealVectorPair vectorPair = maxSimWordPairInstances.get(idPair);
        fv1Builder.withFactor(FeatureTable.MAXSIMWORD, vectorPair.getFirstVector());
        fv2Builder.withFactor(FeatureTable.MAXSIMWORD, vectorPair.getSecondVector());
      }

      ret.put(idPair, FactoredRealVectorPair.from(fv1Builder.build(), fv2Builder.build()));

    }

    return ret.build();
  }
  */

  public static ImmutableSet<Symbol> readTargetMembers(final File infile) throws IOException {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      ret.add(Symbol.from(line));
    }

    return ret.build();
  }

  public ImmutableSet<SymbolPair> hasPairInstances(final ImmutableSet<SymbolPair> ids) {
    return Sets.intersection(pairInstances.get().keySet(), ids).immutableCopy();
  }

  private static ImmutableList<SymbolPair> readPairIds(final File infile)
      throws IOException {
    final ImmutableList.Builder<SymbolPair> ret = ImmutableList.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      final SymbolPair idPair = SymbolPair.from(Symbol.from(tokens[0]), Symbol.from(tokens[1]));
      ret.add(idPair);
    }

    return ret.build();
  }


  private final static Symbol BIAS = Symbol.from("BIAS");

}

