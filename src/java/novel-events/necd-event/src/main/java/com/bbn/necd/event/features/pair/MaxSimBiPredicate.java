package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventFeatures;

import com.google.common.base.Optional;
import com.google.common.base.Predicates;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;
import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 5/23/16.
 */
public final class MaxSimBiPredicate extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(MaxSimBiPredicate.class);

  private MaxSimBiPredicate(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final PredictVectorManager pvManager) {
    return new Builder(featureName, runningIndex, pvManager);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private final PredictVectorManager pvManager;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private Map<SymbolPair, Double> simCache;
    private Map<Symbol, ImmutableMap<Integer, Double>> featuresCache;
    private Map<Symbol, ImmutableMap<Integer, Double>> featuresBiCache;

    private Builder(final String featureName, final int runningIndex,
        final PredictVectorManager pvManager) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.pvManager = pvManager;
      this.existingFeatureIndices = Optional.absent();
      this.simCache = Maps.newHashMap();
      this.featuresCache = Maps.newHashMap();
      this.featuresBiCache = Maps.newHashMap();
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      // assign (running) feature indices to the embeddings
      final ImmutableList<Integer> pvIndices = getPvIndices(FIRST); // for 1st max predicate first
      final ImmutableList<Integer> pvIndices2 = getPvIndices(SECOND); // for 2nd max predicate first

      // get all predicates from all examples
      final ImmutableSet<Symbol> predicates = getPredicates(examples.values());

      // convert the predicates to embeddings vectors. We do this so that we can calculate pairwise similarity
      final ImmutableMap<Symbol, RealVector> predicateToRealVector = toRealVectors(predicates);
      final ImmutableSet<Symbol> predicatesWithEmbeddings = predicateToRealVector.keySet();

      final ImmutableMultimap.Builder<SymbolPair, WeightedIndicesPair> multiFeaturesBuilder = ImmutableMultimap.builder();

      // similarity between words
      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        final ImmutableSet<Symbol> words1 = ImmutableSet.copyOf(
            Iterables.filter(examples.get(id1).predicates(), Predicates.in(predicatesWithEmbeddings)));
        final ImmutableSet<Symbol> words2 = ImmutableSet.copyOf(Iterables.filter(examples.get(id2).predicates(), Predicates.in(predicatesWithEmbeddings)));

        double maxSim = 0;
        Symbol maxWord1 = null;
        Symbol maxWord2 = null;
        for (final Symbol w1 : words1) {
          for (final Symbol w2 : words2) {
            final double sim = similarity(w1, w2, predicateToRealVector);
            if (sim > maxSim) {
              maxSim = sim;
              maxWord1 = w1;
              maxWord2 = w2;
            }
          }
        }

        if (maxSim > 0) {
          // the following is just a map from feature-index to feature-value (which is a real number)
          ImmutableMap<Integer, Double> word1Features = getFeatureMappings(maxWord1, pvIndices);
          ImmutableMap<Integer, Double> word2Features = getFeatureMappings(maxWord2, pvIndices);
          multiFeaturesBuilder.put(item, WeightedIndicesPair.from(word1Features, word2Features));

          // do we have a second best pair of predicates?
          final ImmutableSet<Symbol> w1Prime = Sets.difference(words1, ImmutableSet.of(maxWord1)).immutableCopy();
          final ImmutableSet<Symbol> w2Prime = Sets.difference(words2, ImmutableSet.of(maxWord2)).immutableCopy();
          Symbol maxPrimeWord1 = null;
          Symbol maxPrimeWord2 = null;
          if(w1Prime.size() > 0 && w2Prime.size() > 0) {
            double maxPrimeSim = 0;
            for(final Symbol w1 : w1Prime) {
              for(final Symbol w2 : w2Prime) {
                final double sim = similarity(w1, w2, predicateToRealVector);
                if(sim > maxPrimeSim) {
                  maxPrimeSim = sim;
                  maxPrimeWord1 = w1;
                  maxPrimeWord2 = w2;
                }
              }
            }
            if(maxPrimeSim > 0) {
              ImmutableMap<Integer, Double> word1PrimeFeatures = getFeatureBiMappings(maxPrimeWord1, pvIndices2);
              ImmutableMap<Integer, Double> word2PrimeFeatures = getFeatureBiMappings(maxPrimeWord2, pvIndices2);
              multiFeaturesBuilder.put(item, WeightedIndicesPair.from(word1PrimeFeatures, word2PrimeFeatures));
            }
          }
        }
      }

      final ImmutableMultimap<SymbolPair, WeightedIndicesPair> multiFeatures = multiFeaturesBuilder.build();
      for(final Map.Entry<SymbolPair, Collection<WeightedIndicesPair>> entry : multiFeatures.asMap().entrySet()) {
        final SymbolPair item = entry.getKey();
        final ImmutableMap.Builder<Integer, Double> indices1Builder = ImmutableMap.builder();
        final ImmutableMap.Builder<Integer, Double> indices2Builder = ImmutableMap.builder();
        for(final WeightedIndicesPair indicesPair : entry.getValue()) {
          indices1Builder.putAll(indicesPair.getFirstIndices());
          indices2Builder.putAll(indicesPair.getSecondIndices());
        }
        features.put(item, WeightedIndicesPair.from(indices1Builder.build(), indices2Builder.build()));
      }

      return this;
    }

    private double similarity(final Symbol w1, final Symbol w2,
        final ImmutableMap<Symbol, RealVector> predicateToRealVector) {
      double sim = 0;

      if (w1.equalTo(w2)) {
        sim = 1.0;
      } else {
        final SymbolPair wordPair = SymbolPair.from(w1, w2);
        if (simCache.containsKey(wordPair)) {
          sim = simCache.get(wordPair);
        } else {
          sim = CosineSimilarity
              .similarity(predicateToRealVector.get(w1), predicateToRealVector.get(w2));
          simCache.put(wordPair, sim);
        }
      }

      return sim;
    }

    private ImmutableMap<Integer, Double> getFeatureMappings(final Symbol word,
        final ImmutableList<Integer> indices) {
      final ImmutableMap<Integer, Double> features;

      if (featuresCache.containsKey(word)) {
        features = featuresCache.get(word);
      } else {
        features = toWeightedFeatures(word, indices);
        featuresCache.put(word, features);
      }

      return features;
    }

    private ImmutableMap<Integer, Double> getFeatureBiMappings(final Symbol word,
        final ImmutableList<Integer> indices) {
      final ImmutableMap<Integer, Double> features;

      if (featuresBiCache.containsKey(word)) {
        features = featuresBiCache.get(word);
      } else {
        features = toWeightedFeatures(word, indices);
        featuresBiCache.put(word, features);
      }

      return features;
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final Symbol word,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      final double[] values = pvManager.getVector(word).get().getValues();
      for (int i = 0; i < indices.size(); i++) {
        ret.put(indices.get(i), values[i]);
      }

      return ret.build();
    }

    private ImmutableMap<Integer, Double> getFeatureMappings(final ImmutableSet<Symbol> words,
        final ImmutableList<Integer> indices) {
      return toWeightedFeatures(words, indices);
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final ImmutableSet<Symbol> words,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      double[] weights = new double[pvManager.getDim()];
      for(final Symbol word : words) {
        final double[] values = pvManager.getVector(word).get().getValues();
        for(int i=0; i<values.length; i++) {
          weights[i] += values[i];
        }
      }
      for(int i=0; i<weights.length; i++) {
        weights[i] = weights[i]/words.size();
      }

      for (int i = 0; i < indices.size(); i++) {
        ret.put(indices.get(i), weights[i]);
      }

      return ret.build();
    }

    private ImmutableMap<Symbol, RealVector> toRealVectors(final ImmutableSet<Symbol> predicates) {
      final ImmutableMap.Builder<Symbol, RealVector> predicateToRealVectorBuilder =
          ImmutableMap.builder();

      for (final Symbol predicate : predicates) {
        final Optional<PredictVectorManager.PredictVector> predictVector =
            pvManager.getVector(predicate);
        if (predictVector.isPresent()) {
          final RealVector rv = RealVector.toRealVector(predictVector.get().getValues());
          predicateToRealVectorBuilder.put(predicate, rv);
        }
      }

      return predicateToRealVectorBuilder.build();
    }

    private ImmutableSet<Symbol> getPredicates(final ImmutableCollection<EventFeatures> examples) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      for (final EventFeatures eg : examples) {
        ret.addAll(eg.predicates());
      }

      return ret.build();
    }

    // prefix is useful when we want to form multiple types of embedding features
    private ImmutableList<Integer> getPvIndices(final String prefix) {
      final ImmutableList<Symbol> pvFeatures = pvManager.getFeatureType();

      final ImmutableList.Builder<Integer> ret = ImmutableList.builder();

      if(existingFeatureIndices.isPresent()) {
        for(final Symbol type : pvFeatures) {
          final String fv = prefix + "_" + type.asString();
          // the following get(type.asString()) should not fail, as the embeddings dimensions are fixed.
          // if it fails, it means we did not train with this (i.e. existingFeatureIndices does not contain embeddings), but we tried to use it during decoding
          final int index = existingFeatureIndices.get().get(fv);
          featureIndices.put(fv, index);
          ret.add(index);
        }
      } else {
        for (final Symbol type : pvFeatures) {
          final String fv = prefix + "_" + type.asString();
          featureIndices.put(fv, runningIndex);
          ret.add(runningIndex++);
        }
      }

      return ret.build();
    }

    public MaxSimBiPredicate build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new MaxSimBiPredicate(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new MaxSimBiPredicate(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }

  private final static String FIRST = "FIRST";
  private final static String SECOND = "SECOND";
}
