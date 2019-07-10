package com.bbn.necd.common.theory;


import com.bbn.necd.common.sampler.SymbolPair;

import com.google.common.collect.BiMap;
import com.google.common.collect.ImmutableMap;

import java.util.Map;

public class PairFeature extends Feature {
  private final ImmutableMap<SymbolPair, WeightedIndicesPair> features; // id-pairs to features

  protected PairFeature(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, featureIndices, startIndex, endIndex);
    this.features = features;
  }

  public ImmutableMap<SymbolPair, WeightedIndicesPair> getFeatures() {
    return features;
  }

  // we do not directly build and store this, because during construction we might not have weights available
  public ImmutableMap<SymbolPair, RealVectorPair> toWeightedRealVectorPair(final double[] weights) {
    final ImmutableMap.Builder<SymbolPair, RealVectorPair> ret = ImmutableMap.builder();

    for(final Map.Entry<SymbolPair, WeightedIndicesPair> entry : features.entrySet()) {
      final SymbolPair item = entry.getKey();
      final RealVectorPair vectorPair = toWeightedRealVectorPair(entry.getValue(), weights);
      ret.put(item, vectorPair);
    }

    return ret.build();
  }

  private static WeightedRealVectorPair toWeightedRealVectorPair(final WeightedIndicesPair indicesPair, final double[] weights) {
    final WeightedRealVector v1 = WeightedRealVector.weightedBuilder(false, weights).withElements(indicesPair.getFirstIndices()).build();
    final WeightedRealVector v2 = WeightedRealVector.weightedBuilder(false, weights).withElements(indicesPair.getSecondIndices()).build();
    return WeightedRealVectorPair.from(v1, v2);
  }
}
