package com.bbn.necd.common.theory;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Map;
import java.util.Set;

/*
  This feature table requires weights. To kickoff training, these are some initial weights. For decoding, these are learned weights.
  Parameters:
  - learner.weightsFile (optional during training)
  - learner.initialWeight (optional else default to 1.0)
  - learner.useBias
  - feature.exampleType

  NOTE: either egPairFeatures or egSingleFeatures will be present, not both
 */
public final class FeatureTable {
  private static final Logger log = LoggerFactory.getLogger(FeatureTable.class);

  // (id-pair, name of feature type, a pair of real vectors)
  // in our context, since each of our example is a pair of instances, hence each feature type consists of a pair of feature values
  private final Optional<ImmutableTable<SymbolPair, Symbol, RealVectorPair>> egPairFeatures;

  // (id, name of feature type, a real vector)
  private final Optional<ImmutableTable<Symbol, Symbol, RealVector>> egSingleFeatures;

  private final double[] weights;
  private final BiMap<String, Integer> featureIndices;


  private FeatureTable(final ImmutableTable<SymbolPair, Symbol, RealVectorPair> egPairFeatures,
      final ImmutableTable<Symbol, Symbol, RealVector> egSingleFeatures,
      final double[] weights, final BiMap<String, Integer> featureIndices) {
    this.egPairFeatures = Optional.fromNullable(egPairFeatures);
    this.egSingleFeatures = Optional.fromNullable(egSingleFeatures);
    this.weights = weights;
    this.featureIndices = featureIndices;
  }

  public Optional<ImmutableTable<SymbolPair, Symbol, RealVectorPair>> getEgPairFeatures() {
    return egPairFeatures;
  }

  public Optional<ImmutableTable<Symbol, Symbol, RealVector>> getEgSingleFeatures() {
    return egSingleFeatures;
  }

  public double[] getWeights() {
    return weights;
  }

  public BiMap<String, Integer> getFeatureIndices() {
    return featureIndices;
  }

  public int getNumberOfFeatures() {
    return featureIndices.size();
  }

  public static Builder from(final Parameters params) {
    return new Builder(params);
  }

  public static final class Builder {
    private final ImmutableList.Builder<PairFeature> pairFeaturesBuilder;
    private final ImmutableList.Builder<SingleFeature> singleFeaturesBuilder;
    private final Optional<File> weightsFile;
    private final Optional<Double> initialWeight;
    private final Optional<Boolean> useBias;
    private final ExampleType exampleType;  // either SINGLE or PAIR
    private final Optional<String> normalizeInitialWeights; // either LOG2 or SQUAREROOT

    private Builder(final Parameters params) {
      // weights file will be present during decoding
      this.weightsFile = params.getOptionalExistingFile("learner.weightsFile");

      // usually either 0.0 or 1.0
      this.initialWeight = params.getOptionalPositiveDouble("learner.initialWeight");

      this.useBias = params.getOptionalBoolean("learner.useBias");

      this.pairFeaturesBuilder = ImmutableList.builder();
      this.singleFeaturesBuilder = ImmutableList.builder();

      this.exampleType = params.getEnum("feature.exampleType", ExampleType.class);

      // whether to normalize initial weights using feature set cardinality
      this.normalizeInitialWeights = params.getOptionalString("learner.normalizeInitialWeights");
    }

    public Builder withFeature(final PairFeature feature) {
      pairFeaturesBuilder.add(feature);
      return this;
    }

    public Builder withFeature(final SingleFeature feature) {
      singleFeaturesBuilder.add(feature);
      return this;
    }

    public FeatureTable build() throws IOException {
      final ImmutableList<PairFeature> pairFeatures = pairFeaturesBuilder.build();
      final ImmutableList<SingleFeature> singleFeatures = singleFeaturesBuilder.build();

      switch(exampleType) {
        case PAIR:
          final double[] pairWeights = weightsFile.isPresent()?
                                   prepareWeights(weightsFile.get()) :
                                   prepareWeights(getNumberOfFeatures(pairFeatures), pairFeatures,
                                       normalizeInitialWeights, initialWeight, useBias);
          final BiMap<String, Integer> pairFeatureIndices = getAllFeatureIndices(pairFeatures);
          final ImmutableTable<SymbolPair, Symbol, RealVectorPair> egPairFeatures = toEgPairFeatures(pairFeatures, pairWeights);
          return new FeatureTable(egPairFeatures, null, pairWeights, pairFeatureIndices);
        case SINGLE:
          final double[] singleWeights = weightsFile.isPresent()?
                                   prepareWeights(weightsFile.get()) :
                                   prepareWeights(getNumberOfFeatures(singleFeatures), singleFeatures,
                                       normalizeInitialWeights, initialWeight, useBias);
          final BiMap<String, Integer> singleFeatureIndices = getAllFeatureIndices(singleFeatures);
          final ImmutableTable<Symbol, Symbol, RealVector> egSingleFeatures = toEgSingleFeatures(singleFeatures, singleWeights);
          return new FeatureTable(null, egSingleFeatures, singleWeights, singleFeatureIndices);
        default:
          throw new IllegalArgumentException("Unknown feature.exampleType");

      }
    }

  }

  private static BiMap<String, Integer> getAllFeatureIndices(final ImmutableList<? extends Feature> features) {
    BiMap<String, Integer> featureIndices = HashBiMap.create();
    for(final Feature feature : features) {
      featureIndices.putAll(feature.getFeatureStringToIndex());
    }

    return featureIndices;
  }

  private static double[] prepareWeights(final File weightsFile) throws IOException {
    double[] weights;

    final ImmutableList<String> lines = Files.asCharSource(weightsFile, Charsets.UTF_8).readLines();
    weights = new double[lines.size()];

    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      final int index = new Integer(tokens[0]).intValue();
      weights[index] = new Double(tokens[1]).doubleValue();  // weight value
    }

    return weights;
  }

  private static double[] prepareWeights(final int numberOfFeatures,
      final ImmutableList<? extends Feature> features, final Optional<String> normalizeInitialWeights,
      final Optional<Double> initialWeight, final Optional<Boolean> useBias) throws IOException {
    double[] weights;

    weights = new double[numberOfFeatures + 1]; // we allow space for bias term
    log.info("numberOfFeatures={} weights.length={}", numberOfFeatures, weights.length);

    if (initialWeight.isPresent()) {
      Arrays.fill(weights, initialWeight.get());
    } else {
      Arrays.fill(weights, defaultInitialWeight);
    }

    // we will assume useBias default to true, unelss specified otherwise
    if (useBias.isPresent() && !useBias.get()) {
      weights[0] = 0;
    }

    if(normalizeInitialWeights.isPresent()) {
      for(final Feature feature : features) {
        double Z = 0;
        if(normalizeInitialWeights.get().compareTo("LOG2")==0) {
          Z = Math.log((double) (feature.getEndIndex() - feature.getStartIndex() + 1)) / Math.log(2);
        } else {
          Z = Math.sqrt((double) (feature.getEndIndex() - feature.getStartIndex() + 1));
        }
        log.info("Normalizing initial weights {} to {} by size {}", feature.getStartIndex(), feature.getEndIndex(), Z);
        for(int i=feature.getStartIndex(); i<=feature.getEndIndex(); i++) {
          weights[i] = weights[i]/Z;
        }
      }
    }

    return weights;
  }

  // there are two ways to get the number of features. Here as a sanity check, we will do both of them, and assert that they agree
  // this makes sure that the first index starts from 1, and not 0
  private static int getNumberOfFeatures(final ImmutableList<? extends Feature> features) {
    Set<Integer> endIndices = Sets.newHashSet();
    Set<Integer> allIndices = Sets.newHashSet();
    for(final Feature feature : features) {
      endIndices.add(feature.getEndIndex());
      allIndices.addAll(feature.getFeatureStringToIndex().values());
    }

    final int num1 = Ordering.natural().max(endIndices);
    final int num2 = allIndices.size();
    assert(num1==num2);

    return num1;
  }

  public static ImmutableTable<SymbolPair, Symbol, RealVectorPair> toEgPairFeatures(final ImmutableList<PairFeature> features, final double[] weights) {
    final ImmutableTable.Builder<SymbolPair, Symbol, RealVectorPair> ret = ImmutableTable.builder();

    for (final PairFeature featureType : features) {
      final Symbol featureName = Symbol.from(featureType.getFeatureName());

      // for each id-pair, its associated feature values, represented as a pair of real vectors
      final ImmutableMap<SymbolPair, RealVectorPair> rvPairs =
          featureType.toWeightedRealVectorPair(weights);

      for (final Map.Entry<SymbolPair, RealVectorPair> entry : rvPairs.entrySet()) {
        ret.put(entry.getKey(), featureName, entry.getValue());
      }
    }

    return ret.build();
  }

  public static ImmutableTable<Symbol, Symbol, RealVector> toEgSingleFeatures(final ImmutableList<SingleFeature> features, final double[] weights) {
    final ImmutableTable.Builder<Symbol, Symbol, RealVector> ret = ImmutableTable.builder();

    for (final SingleFeature featureType : features) {
      final Symbol featureName = Symbol.from(featureType.getFeatureName());

      // for each id, its associated feature values, represented as a real vector
      final ImmutableMap<Symbol, RealVector> rv =
          featureType.toWeightedRealVector(weights);

      for (final Map.Entry<Symbol, RealVector> entry : rv.entrySet()) {
        ret.put(entry.getKey(), featureName, entry.getValue());
      }
    }

    return ret.build();
  }


  public static ImmutableMap<String, Integer> readFeatureIndices(final File featureIndicesFile)
      throws IOException {
    final ImmutableMap.Builder<String, Integer> ret = ImmutableMap.builder();

    final ImmutableList<String> lines =
        Files.asCharSource(featureIndicesFile, Charsets.UTF_8).readLines();
    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      final int index = new Integer(tokens[0]);
      final String value = tokens[1];
      ret.put(value, index);
    }
    return ret.build();

  }

  private final static double defaultInitialWeight = 1.0;
  public final static int initialFeatureIndex = 1;
  public final static int biasFeatureIndex = 0;

  public enum ExampleType {
    SINGLE,
    PAIR
  }
}
