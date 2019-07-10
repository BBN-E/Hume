package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.PropositionTreeFeatures;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Multiset;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 5/17/16.
 */
public final class PropRolesOnPath extends PairFeature {

  private PropRolesOnPath(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final int sparsityThreshold) {
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

      final ImmutableTable.Builder<Symbol, String, Double> featuresCacheBuilder = ImmutableTable.builder();
      Set<Symbol> seenIds = Sets.newHashSet();

      for (final SymbolPair idPair : idPairs) {
        for(final Symbol item : idPair.getMembers()) {
          // check whether we have seen this EC before, because there might be individual EC ids within idPairs that are duplicated
          if(!seenIds.contains(item)) {
            final EventFeatures eg = examples.get(item);

            // set of prop labels on path from source to target. Note this includes the prop roles directly connected to source and target.
            final ImmutableSet<String> rolesOnPath = PropositionTreeFeatures.getRolesOnPathBetweenSourceTarget(eg);

            for(final String role : rolesOnPath) {
              final String v = featureName + DELIMITER + role;
              featuresCacheBuilder.put(item, v, 1.0);
            }

            seenIds.add(item);
          }
        }
      }
      final ImmutableTable<Symbol, String, Double> featuresCache = featuresCacheBuilder.build();

      final Multiset<String> featureCounts = getFeatureCount(featuresCache);


      for (final SymbolPair idPair : idPairs) {
        final Symbol id1 = idPair.getFirstMember();
        final Symbol id2 = idPair.getSecondMember();

        final ImmutableMap<Integer, Double> indices1 = toFeatureIndices(featuresCache.row(id1), featureCounts);
        final ImmutableMap<Integer, Double> indices2 = toFeatureIndices(featuresCache.row(id2), featureCounts);

        features.put(idPair, WeightedIndicesPair.from(indices1, indices2));
      }

      return this;
    }

    private ImmutableMap<Integer, Double> toFeatureIndices(
        final ImmutableMap<String, Double> features, final Multiset<String> featureCounts) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for(final Map.Entry<String, Double> feature : features.entrySet()) {
        final String v = feature.getKey();
        final Double weight = feature.getValue();

        if(featureCounts.count(v) >= sparsityThreshold) {
          if(existingFeatureIndices.isPresent()) {
            if(existingFeatureIndices.get().containsKey(v)) {
              final int index = existingFeatureIndices.get().get(v);
              featureIndices.put(v, index);
              ret.put(index, weight);
            }
          } else {
            if(featureIndices.containsKey(v)) {
              ret.put(featureIndices.get(v), weight);
            } else {
              featureIndices.put(v, runningIndex);
              ret.put(runningIndex, weight);
              runningIndex++;
            }
          }
        }
      }

      return ret.build();
    }

    public PropRolesOnPath build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new PropRolesOnPath(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new PropRolesOnPath(featureName, features.build(), featureIndices, -1, -1);
      }

    }
  }
}
