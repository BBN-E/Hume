package com.bbn.necd.common.theory;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.base.Objects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;

import java.util.Map;

/**
 * Created by ychan on 1/26/16.
 */
public final class FactoredRealVector {
  private final ImmutableMap<Symbol, RealVector> factors;
  private final double norm;
  private final double dotProduct;

  private FactoredRealVector(final ImmutableMap<Symbol, RealVector> factors, final double norm, final double dotProduct) {
    this.factors = factors;
    this.norm = norm;
    this.dotProduct = dotProduct;
  }

  public ImmutableMap<Symbol, RealVector> getFactors() {
    return factors;
  }

  public Optional<RealVector> getFactor(final Symbol factorId) {
    return Optional.fromNullable(factors.get(factorId));
  }

  public double getNorm() {
    return norm;
  }

  public double getDotProduct() {
    return dotProduct;
  }

  public Optional<Double> getValueByFactorIndex(final Symbol factorType, final int index) {
    return factors.get(factorType).getValueByIndex(index);
  }


  public Optional<Double> getValueByIndex(final int index) {
    for(final RealVector v : factors.values()) {
      final Optional<Double> value = v.getValueByIndex(index);
      if(value.isPresent()) {
        return value;
      }
    }
    return Optional.<Double>absent();
  }


  public boolean hasIndex(final int index) {
    for(final RealVector v : factors.values()) {
      final Optional<Double> value = v.getValueByIndex(index);
      if(value.isPresent()) {
        return true;
      }
    }
    return false;
  }

  public static Builder builder() {
    return new Builder();
  }

  public static final class Builder {
    private final ImmutableMap.Builder<Symbol, RealVector> factorsBuilder;

    private Builder() {
      factorsBuilder = ImmutableMap.builder();
    }

    public Builder withFactor(final Symbol factorId, final RealVector v) {
      factorsBuilder.put(factorId, v);
      return this;
    }

    public FactoredRealVector build() {
      final ImmutableMap<Symbol, RealVector> factors = factorsBuilder.build();

      double dotProduct = 0;
      for(final RealVector v : factors.values()) {
        dotProduct += v.getDotProduct();
      }

      double norm = Math.sqrt(dotProduct);

      return new FactoredRealVector(factors, norm, dotProduct);
    }
  }

  public String toString() {
    final StringBuilder sb = new StringBuilder();
    for(final Map.Entry<Symbol, RealVector> entry : factors.entrySet()) {
      sb.append("<");
      sb.append(entry.getKey().asString());
      sb.append("> ");
      sb.append(entry.getValue().toString());
      sb.append("\n");
    }
    sb.append("dotProduct="+dotProduct);
    sb.append(" norm="+norm);

    return sb.toString();
  }

  public String toSparseString() {
    final StringBuilder sb = new StringBuilder();

    for(final RealVector v : factors.values()) {
      if(sb.length() > 0) {
        sb.append(" ");
      }
      sb.append(v.toSparseString());
    }

    return sb.toString();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(factors, norm, dotProduct);
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
    final FactoredRealVector other = (FactoredRealVector) obj;
    return Objects.equal(factors, other.factors) &&
        Objects.equal(norm, other.norm) &&
        Objects.equal(dotProduct, other.dotProduct);
  }


}
