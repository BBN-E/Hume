package com.bbn.necd.event.features.single;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.SingleFeature;
import com.bbn.necd.event.features.EventFeatures;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Multiset;
import com.google.common.collect.Ordering;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 4/18/16.
 */
public final class PredicatesFeature extends SingleFeature {
  private static final Logger log = LoggerFactory.getLogger(PredicatesFeature.class);

  private PredicatesFeature(final String featureName,
      final ImmutableTable<Symbol, Integer, Double> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
    return new Builder(featureName, runningIndex, sparsityThreshold);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableTable.Builder<Symbol, Integer, Double> features;
    private final BiMap<String, Integer> featureIndices;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final int sparsityThreshold;

    private Builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableTable.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
      this.sparsityThreshold = sparsityThreshold;
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<Symbol> ids,
        final ImmutableMap<Symbol, EventFeatures> examples) {

      final Multiset<Symbol> featureCount = getFeatureCount(ids, examples);

      for (final Symbol item : ids) {
        final EventFeatures eg = examples.get(item);

        final ImmutableMap.Builder<Integer, Double> indicesBuilder = ImmutableMap.builder();
        for (final Symbol value : ImmutableSet.copyOf(eg.stems())) {
          if(featureCount.count(value) >= sparsityThreshold) {
            final String v = featureName + DELIMITER + value.asString();

            log.info("{} {}", item.asString(), v);

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

        // NOTE! If indices is empty, i.e. there is no feature value, then the example 'item' will not be inserted into 'features' table
        for(final Map.Entry<Integer, Double> entry : indices.entrySet()) {
          features.put(item, entry.getKey(), entry.getValue());
        }
      }

      return this;
    }

    private Multiset<Symbol> getFeatureCount(final ImmutableList<Symbol> ids,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      final Multiset<Symbol> ret = HashMultiset.create();

      for (final Symbol item : ids) {
        final EventFeatures eg = examples.get(item);
        ret.addAll(eg.predicates());
      }

      return ret;
    }

    public PredicatesFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new PredicatesFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new PredicatesFeature(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }
}
