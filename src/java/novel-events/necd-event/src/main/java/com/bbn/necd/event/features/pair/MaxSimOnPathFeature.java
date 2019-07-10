package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.PropositionTreeFeatures;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 7/20/16.
 */
public final class MaxSimOnPathFeature extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(MaxSimPredicateFeature.class);

  private MaxSimOnPathFeature(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final PredictVectorManager pvManager, final BackgroundInformation backgroundInformation) {
    return new Builder(featureName, runningIndex, pvManager, backgroundInformation);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private final PredictVectorManager pvManager;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final BackgroundInformation backgroundInformation;

    private Builder(final String featureName, final int runningIndex,
        final PredictVectorManager pvManager, final BackgroundInformation backgroundInformation) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.pvManager = pvManager;
      this.existingFeatureIndices = Optional.absent();
      this.backgroundInformation = backgroundInformation;
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      // assign (running) feature indices to the embeddings
      final ImmutableList<Integer> pvIndices = getPvIndices();

      // get all predicates from all examples
      //final ImmutableSet<Symbol> predicates = getPredicates(examples.values());
      final ImmutableMap<Symbol, ImmutableSet<Symbol>> predicatesOnPath = getPredicatesOnPath(examples);
      final ImmutableSet<Symbol> predicates = toPredicates(predicatesOnPath);

      // convert the predicates to embeddings vectors. We do this so that we can calculate pairwise similarity
      final ImmutableMap<Symbol, RealVector> predicateToRealVector = toRealVectors(predicates);

      // similarity between words
      Map<SymbolPair, Double> simCache = Maps.newHashMap();
      Map<Symbol, ImmutableMap<Integer, Double>> featuresCache = Maps.newHashMap();
      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        //final ImmutableSet<Symbol> words1 =
        //    ImmutableSet.<Symbol>builder().addAll(examples.get(id1).predicates()).build();
        //final ImmutableSet<Symbol> words2 =
        //    ImmutableSet.<Symbol>builder().addAll(examples.get(id2).predicates()).build();
        final ImmutableSet<Symbol> words1 = predicatesOnPath.get(id1);
        final ImmutableSet<Symbol> words2 = predicatesOnPath.get(id2);

        double maxSim = 0;
        Symbol maxWord1 = null;
        Symbol maxWord2 = null;
        for (final Symbol w1 : words1) {
          for (final Symbol w2 : words2) {
            if (predicateToRealVector.containsKey(w1) && predicateToRealVector.containsKey(w2)) {
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
              if (sim > maxSim) {
                maxSim = sim;
                maxWord1 = w1;
                maxWord2 = w2;
              }
            }
          }
        }

        // notice that this will only be true if maxWord1 and maxWord2 are in predicateToRealVector
        if (maxSim > 0) {
          // the following is just a map from feature-index to feature-value (which is a real number)
          ImmutableMap<Integer, Double> word1Features = null;
          ImmutableMap<Integer, Double> word2Features = null;

          if (featuresCache.containsKey(maxWord1)) {
            word1Features = featuresCache.get(maxWord1);
          } else {
            word1Features = toWeightedFeatures(maxWord1, pvIndices);
            featuresCache.put(maxWord1, word1Features);
          }
          if (featuresCache.containsKey(maxWord2)) {
            word2Features = featuresCache.get(maxWord2);
          } else {
            word2Features = toWeightedFeatures(maxWord2, pvIndices);
            featuresCache.put(maxWord2, word2Features);
          }

          features.put(item, WeightedIndicesPair.from(word1Features, word2Features));
        }
      }

      return this;
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final Symbol word,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      final double[] values = pvManager.getVector(word).get().getValues();
      for (int i = 0; i < indices.size(); i++) {
        //if(values[i] < 0) {
        //  ret.put(indices.get(i), 0.0);
        //} else {
        ret.put(indices.get(i), values[i]);
        //}
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

    private ImmutableSet<Symbol> toPredicates(final ImmutableMap<Symbol, ImmutableSet<Symbol>> predicatesOnPath) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      for(final ImmutableSet<Symbol> p : predicatesOnPath.values()) {
        ret.addAll(p);
      }

      return ret.build();
    }

    private ImmutableMap<Symbol, ImmutableSet<Symbol>> getPredicatesOnPath(
        final ImmutableMap<Symbol, EventFeatures> examples) {
      final ImmutableMap.Builder<Symbol, ImmutableSet<Symbol>> ret = ImmutableMap.builder();

      for(final Map.Entry<Symbol, EventFeatures> entry : examples.entrySet()) {
        final Symbol id = entry.getKey();
        final ImmutableSet<Symbol> words = PropositionTreeFeatures.getWordsOnPathSourceToTarget(entry.getValue(), backgroundInformation);
        ret.put(id, words);
      }

      return ret.build();
    }

    private ImmutableSet<Symbol> getPredicates(final ImmutableCollection<EventFeatures> examples) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      for (final EventFeatures eg : examples) {
        ret.addAll(eg.predicates());
      }

      return ret.build();
    }

    private ImmutableList<Integer> getPvIndices() {
      final ImmutableList<Symbol> pvFeatures = pvManager.getFeatureType();

      final ImmutableList.Builder<Integer> ret = ImmutableList.builder();

      if(existingFeatureIndices.isPresent()) {
        for(final Symbol type : pvFeatures) {
          // the following get(type.asString()) should not fail, as the embeddings dimensions are fixed.
          // if it fails, it means we did not train with this (i.e. existingFeatureIndices does not contain embeddings), but we tried to use it during decoding
          if(!existingFeatureIndices.get().containsKey(type.asString())) {
            log.info("ERROR: existingFeatureIndices does not contain {}", type.asString());
          }
          final int index = existingFeatureIndices.get().get(type.asString());
          featureIndices.put(type.asString(), index);
          ret.add(index);
        }
      } else {
        for (final Symbol type : pvFeatures) {
          featureIndices.put(type.asString(), runningIndex);
          ret.add(runningIndex++);
        }
      }

      return ret.build();
    }

    public MaxSimOnPathFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new MaxSimOnPathFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new MaxSimOnPathFeature(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }
}
