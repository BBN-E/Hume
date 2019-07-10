package com.bbn.necd.common.theory;

import com.google.common.collect.ImmutableMap;

/**
 * Created by ychan on 1/26/16.
 */
public final class WeightedRealVectorPair extends RealVectorPair {


  private WeightedRealVectorPair(final WeightedRealVector v1, final WeightedRealVector v2) {
    super(v1, v2);
  }

  public static WeightedRealVectorPair from(final WeightedRealVector v1, final WeightedRealVector v2) {
    return new WeightedRealVectorPair(v1, v2);
  }

  public static Builder builder(final double[] weights) {
    return new Builder(weights);
  }

  public static class Builder {
    private final ImmutableMap.Builder<Integer, Double> elementsBuilder;
    private final ImmutableMap.Builder<Integer, Double> elements1Builder;
    private final ImmutableMap.Builder<Integer, Double> elements2Builder;
    private final double[] weights;

    private Builder(final double[] weights) {
      this.elementsBuilder = ImmutableMap.builder();
      this.elements1Builder = ImmutableMap.builder();
      this.elements2Builder = ImmutableMap.builder();
      this.weights = weights;
    }

    public Builder withElement(final int index, final double weight) {
      elementsBuilder.put(index, weight);
      return this;
    }

    public Builder withElements(final ImmutableMap<Integer, Double> elements) {
      elementsBuilder.putAll(elements);
      return this;
    }

    public Builder withElements(final ImmutableMap<Integer, Double> elements1, final ImmutableMap<Integer, Double> elements2) {
      elements1Builder.putAll(elements1);
      elements2Builder.putAll(elements2);
      return this;
    }

    public WeightedRealVectorPair build() {
      final ImmutableMap<Integer, Double> elements = elementsBuilder.build();
      final WeightedRealVector v =
          WeightedRealVector.weightedBuilder(false, weights).withElements(elements).build();

      // now for the paired values. These will use 1.0 as placeholders
      final ImmutableMap.Builder<Integer, Double> pairedElementsBuilder = ImmutableMap.builder();
      for (final Integer key : elements.keySet()) {
        pairedElementsBuilder.put(key, 1.0);
      }
      final ImmutableMap<Integer, Double> pairedElements = pairedElementsBuilder.build();
      final WeightedRealVector pairedV =
          WeightedRealVector.weightedBuilder(false, weights).withElements(pairedElements).build();

      return new WeightedRealVectorPair(v, pairedV);
    }

    public WeightedRealVectorPair buildPair() {
      final ImmutableMap<Integer, Double> elements1 = elements1Builder.build();
      final ImmutableMap<Integer, Double> elements2 = elements2Builder.build();

      final WeightedRealVector v1 =
          WeightedRealVector.weightedBuilder(false, weights).withElements(elements1).build();
      final WeightedRealVector v2 =
          WeightedRealVector.weightedBuilder(false, weights).withElements(elements2).build();

      return new WeightedRealVectorPair(v1, v2);
    }

  }


}
