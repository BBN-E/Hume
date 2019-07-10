package com.bbn.necd.common.theory;


import com.bbn.necd.common.sampler.SymbolPair;

import com.google.common.base.Function;
import com.google.common.base.Objects;

/*
 * Represents a data instance
 */
public final class PairedRealInstance {
  private final int label;
  private final FactoredRealVector v1;
  private final FactoredRealVector v2;
  private final SymbolPair idPair;

  private PairedRealInstance(final int label, final FactoredRealVector v1, final FactoredRealVector v2, final SymbolPair idPair) {
    this.label = label;
    this.v1 = v1;
    this.v2 = v2;
    this.idPair = idPair;
  }

  public static PairedRealInstance from(final int label, final FactoredRealVector v1, final FactoredRealVector v2, final SymbolPair idPair) {
    return new PairedRealInstance(label, v1, v2, idPair);
  }

  public int getLabel() {
    return label;
  }

  public FactoredRealVector getFirstMember() {
    return v1;
  }

  public FactoredRealVector getSecondMember() {
    return v2;
  }

  public SymbolPair getIdPair() {
    return idPair;
  }

  public boolean hasIndex(final int index) {
    return v1.hasIndex(index) && v2.hasIndex(index);
  }

  public int hashCode() {
    return Objects.hashCode(label, v1, v2, idPair);
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
    final PairedRealInstance other = (PairedRealInstance) obj;
    return Objects.equal(label, label) &&
        Objects.equal(v1, other.v1) &&
        Objects.equal(v2, other.v2) &&
        Objects.equal(idPair, other.idPair);
  }

  public static final Function<PairedRealInstance, SymbolPair> IDPAIR =
      new Function<PairedRealInstance, SymbolPair>() {
        @Override
        public SymbolPair apply(final PairedRealInstance eg) {
          return eg.getIdPair();
        }
      };
}
