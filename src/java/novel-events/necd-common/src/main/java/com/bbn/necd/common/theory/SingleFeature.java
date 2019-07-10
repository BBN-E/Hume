package com.bbn.necd.common.theory;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.collect.BiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;

import java.util.Map;

/**
 * Created by ychan on 4/18/16.
 */
public class SingleFeature extends Feature {
  private final ImmutableTable<Symbol, Integer, Double> features; // id, feature-index, feature-value

  protected SingleFeature(final String featureName,
      final ImmutableTable<Symbol, Integer, Double> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, featureIndices, startIndex, endIndex);
    this.features = features;
  }

  public ImmutableTable<Symbol, Integer, Double> getFeatures() {
    return features;
  }

  // we do not directly build and store this, because during construction we might not have weights available
  public ImmutableMap<Symbol, RealVector> toWeightedRealVector(final double[] weights) {
    final ImmutableMap.Builder<Symbol, RealVector> ret = ImmutableMap.builder();

    for(final Symbol item : features.rowKeySet()) {
      final WeightedRealVector v = WeightedRealVector.weightedBuilder(false, weights).withElements(features.row(item)).build();
      ret.put(item, v);
    }

    return ret.build();
  }

  public ImmutableList<String> printFeatures() {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    for(final Symbol id : features.rowKeySet()) {
      for(final Map.Entry<Integer, Double> entry : features.row(id).entrySet()) {
        ret.add(id.asString() + " " + entry.getKey() + " " + entry.getValue());
      }
    }

    return ret.build();
  }

}
