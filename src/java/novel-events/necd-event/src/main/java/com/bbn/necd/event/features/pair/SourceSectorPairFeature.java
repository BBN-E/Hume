package com.bbn.necd.event.features.pair;


import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.formatter.StringPair;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Multiset;
import com.google.common.collect.Ordering;

import java.util.Set;

public final class SourceSectorPairFeature extends PairFeature {

  private SourceSectorPairFeature(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
    return new Builder(featureName, runningIndex, sparsityThreshold);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final int sparsityThreshold;

    private Builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
      this.sparsityThreshold = sparsityThreshold;
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {

      final Multiset<StringPair> featureCount = getFeatureCount(idPairs, examples);

      for (final SymbolPair item : idPairs) {
        final EventFeatures eg1 = examples.get(item.getFirstMember());
        final EventFeatures eg2 = examples.get(item.getSecondMember());

        final ImmutableSet<StringPair> values = getSourceSectorPairs(eg1, eg2);

        final ImmutableMap.Builder<Integer, Double> indicesBuilder = ImmutableMap.builder();
        for (final StringPair value : values) {
          if(featureCount.count(value) >= sparsityThreshold) {
            final String v = featureName + DELIMITER + value.getFirstString() + DELIMITER + value
                .getSecondString();

            if (existingFeatureIndices.isPresent()) {
              if (existingFeatureIndices.get().containsKey(v)) {
                final int index = existingFeatureIndices.get().get(v);
                indicesBuilder.put(index, 1.0);
                featureIndices.put(v, index);
              }
            } else {
              if (featureIndices.containsKey(v)) {
                indicesBuilder.put(featureIndices.get(v), 1.0);
              } else {
                indicesBuilder.put(runningIndex, 1.0);
                featureIndices.put(v, runningIndex++);
              }
            }
          }
        }
        final ImmutableMap<Integer, Double> indices = indicesBuilder.build();

        features.put(item, WeightedIndicesPair.from(indices, indices));
      }

      return this;
    }

    private Multiset<StringPair> getFeatureCount(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      final Multiset<StringPair> ret = HashMultiset.create();

      for (final SymbolPair item : idPairs) {
        final EventFeatures eg1 = examples.get(item.getFirstMember());
        final EventFeatures eg2 = examples.get(item.getSecondMember());

        ret.addAll(getSourceSectorPairs(eg1, eg2));
      }

      return ret;
    }

    private final ImmutableSet<StringPair> getSourceSectorPairs(final EventFeatures eg1, final EventFeatures eg2) {
      final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();

      for (final Symbol s1 : eg1.sourceSectors()) {
        for (final Symbol s2 : eg2.sourceSectors()) {
          ret.add(StringPair.from(s1.asString(), s2.asString()));
        }
      }

      return ret.build();
    }

    public SourceSectorPairFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new SourceSectorPairFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new SourceSectorPairFeature(featureName, features.build(), featureIndices, -1, -1);
      }
    }
  }

}
