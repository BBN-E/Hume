package com.bbn.necd.common.theory;

import com.bbn.bue.common.primitives.DoubleUtils;

import com.google.common.base.Objects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Ordering;
import com.google.common.primitives.Doubles;

import java.util.Map;

public class RealVector {
  protected final ImmutableMap<Integer, Double> elements;
  protected final double norm;                              // L2-norm
  protected final double dotProduct;

  protected RealVector(final ImmutableMap<Integer, Double> elements, final double norm, final double dotProduct) {
    this.elements = ImmutableMap.copyOf(elements);
    this.norm = norm;
    this.dotProduct = dotProduct;
  }

  public ImmutableMap<Integer, Double> getElements() {
    return elements;
  }

  public double getNorm() {
    return norm;
  }

  public double getDotProduct() {
    return dotProduct;
  }

  public Optional<Double> getValueByIndex(final int index) {
    return Optional.fromNullable(elements.get(index));
  }

  public static double calculateDotProduct(final ImmutableMap<Integer, Double> elements) {
    final double[] values = Doubles.toArray(elements.values());
    return DoubleUtils.dotProduct(values, values);
  }

  public static double calculateL2Norm(final ImmutableMap<Integer, Double> elements) {
    final double dotProduct = calculateDotProduct(elements);
    return Math.sqrt(dotProduct);
  }

  public static ImmutableMap<Integer, Double> normalizeByNorm(final ImmutableMap<Integer, Double> elements, final double norm) {
    final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

    for(final Map.Entry<Integer, Double> entry : elements.entrySet()) {
      ret.put(entry.getKey(), entry.getValue()/norm);
    }

    return ret.build();
  }

  public RealVector toUnitVector() {
    return new RealVector(normalizeByNorm(elements, norm), norm, dotProduct);
    //return builder(true).withElements(elements).build();
  }

  public static RealVector toRealVector(final double[] values) {
    final ImmutableMap.Builder<Integer, Double> elementsBuilder = ImmutableMap.builder();
    for(int i=0; i<values.length; i++) {
      elementsBuilder.put(i, values[i]);
    }
    final ImmutableMap<Integer, Double> elements = elementsBuilder.build();

    return RealVector.builder(false).withElements(elements).build();
  }

  public static Builder builder(final boolean makeUnitVector) {
    return new Builder(makeUnitVector);
  }

  public static class Builder {
    private final ImmutableMap.Builder<Integer, Double> elementsBuilder;
    private final boolean makeUnitVector;

    private Builder(final boolean makeUnitVector) {
      this.makeUnitVector = makeUnitVector;
      this.elementsBuilder = ImmutableMap.builder();
    }

    public Builder withElement(final int index, final double weight) {
      elementsBuilder.put(index, weight);
      return this;
    }

    public Builder withElements(final ImmutableMap<Integer, Double> elements) {
      elementsBuilder.putAll(elements);
      return this;
    }

    public RealVector build() {
      final ImmutableMap<Integer, Double> elements = elementsBuilder.build();
      final double dotProduct = calculateDotProduct(elements);
      final double norm = Math.sqrt(dotProduct);

      if(makeUnitVector) {
        return new RealVector(normalizeByNorm(elements, norm), norm, dotProduct);
      } else {
        return new RealVector(elements, norm, dotProduct);
      }
    }
  }

  public String toString() {
    final StringBuilder sb = new StringBuilder();

    sb.append("elements");
    for(final Integer index : Ordering.natural().immutableSortedCopy(elements.keySet())) {
      final double v = elements.get(index);
      sb.append(" " + index + ":" + v);
    }
    sb.append("\n");
    sb.append("dotProduct="+dotProduct);
    sb.append(" norm="+norm);

    return sb.toString();
  }

  public String toSparseString() {
    final StringBuilder sb = new StringBuilder();

    for(final Integer index : Ordering.natural().immutableSortedCopy(elements.keySet())) {
      final double v = elements.get(index);
      if(sb.length() > 0) {
        sb.append(" ");
      }
      sb.append(index + ":" + v);
    }

    return sb.toString();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(elements, norm, dotProduct);
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
    final RealVector other = (RealVector) obj;
    return Objects.equal(elements, other.elements) &&
           Objects.equal(norm, other.norm) &&
           Objects.equal(dotProduct, other.dotProduct);
  }

}
