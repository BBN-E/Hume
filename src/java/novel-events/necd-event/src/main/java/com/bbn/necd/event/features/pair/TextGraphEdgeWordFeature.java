package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.FeatureUtils;
import com.bbn.necd.event.features.PropositionTreeFeatures;
import com.bbn.necd.event.formatter.StringPair;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 6/28/16.
 */
public final class TextGraphEdgeWordFeature extends PairFeature {
  private TextGraphEdgeWordFeature(final String featureName,
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
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final PredictVectorManager pvManager;
    private Map<StringPair, Double> simCache;

    private Builder(final String featureName, final int runningIndex,
        final PredictVectorManager pvManager) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
      this.pvManager = pvManager;
      this.simCache = Maps.newHashMap();
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    private double similarity(final String w1, final String w2,
        final ImmutableMap<String, RealVector> predicateToRealVector) {
      double sim = 0;

      if (w1.compareTo(w2)==0) {
        sim = 1.0;
      } else {
        final StringPair wordPair = StringPair.from(w1, w2);
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

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {

      final ImmutableSet<String> allWords = FeatureUtils.getAllWordsOnPath(examples.values());
      // convert the predicates to embeddings vectors. We do this so that we can calculate pairwise similarity
      final ImmutableMap<String, RealVector> predicateToRealVector = FeatureUtils.toRealVectors(allWords, pvManager);
      final ImmutableSet<String> predicatesWithEmbeddings = predicateToRealVector.keySet();

      for (final SymbolPair idPair : idPairs) {
        final Symbol id1 = idPair.getFirstMember();
        final Symbol id2 = idPair.getSecondMember();

        final ImmutableMap.Builder<String, Double> featuresBuilder = ImmutableMap.builder();

        final ImmutableSet<StringPair> source1 = FeatureUtils.getSourcePropRolesWords(examples.get(id1));
        final ImmutableSet<StringPair> source2 = FeatureUtils.getSourcePropRolesWords(examples.get(id2));
        for(final StringPair p1 : source1) {
          for(final StringPair p2 : source2) {
            if(p1.getFirstString().length()>0 && p2.getFirstString().length()>0) {
              String s = "";
              if (p1.getFirstString().compareTo(p2.getFirstString()) <= 0) {
                s = featureName + DELIMITER + PropositionTreeFeatures.SOURCE + DELIMITER + p1
                    .getFirstString() + DELIMITER + p2.getFirstString();
              } else {
                s = featureName + DELIMITER + PropositionTreeFeatures.SOURCE + DELIMITER + p2
                    .getFirstString() + DELIMITER + p1.getFirstString();
              }
              final String w1 = p1.getSecondString();
              final String w2 = p2.getSecondString();
              if (w1.compareTo(w2) == 0 || (predicatesWithEmbeddings.contains(w1)
                                                && predicatesWithEmbeddings.contains(w2))) {
                final double sim = similarity(w1, w2, predicateToRealVector);
                featuresBuilder.put(s, sim);
              }
            }
          }
        }

        final ImmutableSet<StringPair> target1 = FeatureUtils.getTargetPropRolesWords(examples.get(id1));
        final ImmutableSet<StringPair> target2 = FeatureUtils.getTargetPropRolesWords(examples.get(id2));
        for(final StringPair p1 : target1) {
          for(final StringPair p2 : target2) {
            if(p1.getFirstString().length()>0 && p2.getFirstString().length()>0) {
              String s = "";
              if (p1.getFirstString().compareTo(p2.getFirstString()) <= 0) {
                s = featureName + DELIMITER + PropositionTreeFeatures.TARGET + DELIMITER + p1
                    .getFirstString() + DELIMITER + p2.getFirstString();
              } else {
                s = featureName + DELIMITER + PropositionTreeFeatures.TARGET + DELIMITER + p2
                    .getFirstString() + DELIMITER + p1.getFirstString();
              }
              final String w1 = p1.getSecondString();
              final String w2 = p2.getSecondString();
              if (w1.compareTo(w2) == 0 || (predicatesWithEmbeddings.contains(w1)
                                                && predicatesWithEmbeddings.contains(w2))) {
                final double sim = similarity(w1, w2, predicateToRealVector);
                featuresBuilder.put(s, sim);
              }
            }
          }
        }

        final ImmutableMap<Integer, Double> indices = toFeatureIndices(featuresBuilder.build());
        final ImmutableMap<Integer, Double> dummyIndices = FeatureUtils.toDummyIndices(indices);

        features.put(idPair, WeightedIndicesPair.from(indices, dummyIndices));
      }

      return this;
    }

    private ImmutableMap<Integer, Double> toFeatureIndices(
        final ImmutableMap<String, Double> features) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for (final Map.Entry<String, Double> feature : features.entrySet()) {
        final String v = feature.getKey();
        final Double weight = feature.getValue();

        if (existingFeatureIndices.isPresent()) {
          if (existingFeatureIndices.get().containsKey(v)) {
            final int index = existingFeatureIndices.get().get(v);
            featureIndices.put(v, index);
            ret.put(index, weight);
          }
        } else {
          if (featureIndices.containsKey(v)) {
            ret.put(featureIndices.get(v), weight);
          } else {
            featureIndices.put(v, runningIndex);
            ret.put(runningIndex, weight);
            runningIndex++;
          }
        }
      }

      return ret.build();
    }

    public TextGraphEdgeWordFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new TextGraphEdgeWordFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new TextGraphEdgeWordFeature(featureName, features.build(), featureIndices, -1, -1);
      }

    }
  }
}
