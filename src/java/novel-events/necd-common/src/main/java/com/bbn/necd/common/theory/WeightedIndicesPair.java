package com.bbn.necd.common.theory;


import com.google.common.collect.ImmutableMap;

/*
  In general, feature values for an example are represented by a map of (feature-index -> real number as weight).
  When we are comparing example pairs, we have firstIndices and secondIndices
 */
public final class WeightedIndicesPair {
  private final ImmutableMap<Integer, Double> firstIndices;
  private final ImmutableMap<Integer, Double> secondIndices;

  private WeightedIndicesPair(final ImmutableMap<Integer, Double> firstIndices, final ImmutableMap<Integer, Double> secondIndices) {
    this.firstIndices = firstIndices;
    this.secondIndices = secondIndices;
  }

  public static WeightedIndicesPair from(final ImmutableMap<Integer, Double> firstIndices, final ImmutableMap<Integer, Double> secondIndices) {
    return new WeightedIndicesPair(firstIndices, secondIndices);
  }

  public ImmutableMap<Integer, Double> getFirstIndices() {
    return firstIndices;
  }

  public ImmutableMap<Integer, Double> getSecondIndices() {
    return secondIndices;
  }
}

