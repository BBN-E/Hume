package com.bbn.necd.common.theory;

import com.google.common.base.Objects;

/**
 * Created by ychan on 1/26/16.
 */
public class RealVectorPair {
  private final RealVector v1;
  private final RealVector v2;

  protected RealVectorPair(final RealVector v1, final RealVector v2) {
    this.v1 = v1;
    this.v2 = v2;
  }

  public RealVector getFirstVector() {
    return v1;
  }

  public RealVector getSecondVector() {
    return v2;
  }

  public int hashCode() {
    return Objects.hashCode(v1, v2);
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
    final RealVectorPair other = (RealVectorPair) obj;
    return Objects.equal(v1, other.v1) &&
        Objects.equal(v2, other.v2);
  }
}
