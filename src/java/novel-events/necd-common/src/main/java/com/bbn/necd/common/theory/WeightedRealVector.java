package com.bbn.necd.common.theory;

import com.google.common.base.Objects;
import com.google.common.collect.ImmutableMap;

import java.util.Map;

public final class WeightedRealVector extends RealVector {

  protected WeightedRealVector(final ImmutableMap<Integer, Double> elements, final double norm, final double dotProduct) {
    super(elements, norm, dotProduct);
  }

  public static double calculateDotProduct(final ImmutableMap<Integer, Double> elements, final double[] weights) {
    double sum = 0;
    for(final Map.Entry<Integer, Double> entry : elements.entrySet()) {
      final double v = entry.getValue();
      final double w = weights[entry.getKey()];
      sum += (v * v * w);
    }
    return sum;
  }

  public static double calculateL2Norm(final ImmutableMap<Integer, Double> elements, final double[] weights) {
    final double dotProduct = calculateDotProduct(elements, weights);
    return Math.sqrt(dotProduct);
  }

  public WeightedRealVector copyWithWeights(final double[] weights) {
    final double dotProduct = calculateDotProduct(elements, weights);
    final double norm = Math.sqrt(dotProduct);
    return new WeightedRealVector(elements, norm, dotProduct);
  }

  @Override
  public WeightedRealVector toUnitVector() {
    return new WeightedRealVector(normalizeByNorm(elements, norm), norm, dotProduct);
  }


  public static WeightedBuilder weightedBuilder(final boolean makeUnitVector, final double[] weights) {
    return new WeightedBuilder(makeUnitVector, weights);
  }

  public static class WeightedBuilder {
    private final ImmutableMap.Builder<Integer, Double> elementsBuilder;
    private final boolean makeUnitVector;
    private final double[] weights;

    private WeightedBuilder(final boolean makeUnitVector, final double[] weights) {
      this.makeUnitVector = makeUnitVector;
      this.elementsBuilder = ImmutableMap.builder();
      this.weights = weights;
    }

    public WeightedBuilder withElement(final int index, final double weight) {
      elementsBuilder.put(index, weight);
      return this;
    }

    public WeightedBuilder withElements(final ImmutableMap<Integer, Double> elements) {
      elementsBuilder.putAll(elements);
      return this;
    }

    public WeightedRealVector build() {
      final ImmutableMap<Integer, Double> elements = elementsBuilder.build();
      final double dotProduct = calculateDotProduct(elements, weights);
      final double norm = Math.sqrt(dotProduct);

      if(makeUnitVector) {
        return new WeightedRealVector(normalizeByNorm(elements, norm), norm, dotProduct);
      } else {
        return new WeightedRealVector(elements, norm, dotProduct);
      }
    }
  }

  @Override
  public boolean equals(final Object obj) {
    if(this == obj) {
      return true;
    }
    if(obj == null) {
      return false;
    }
    if(getClass() != obj.getClass()) {
      return false;
    }
    final WeightedRealVector other = (WeightedRealVector) obj;
    return Objects.equal(elements, other.elements) &&
           Objects.equal(norm, other.norm) &&
           Objects.equal(dotProduct, other.dotProduct);
  }

}
