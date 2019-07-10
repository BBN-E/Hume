package com.bbn.necd.common.theory;

import com.google.common.base.Objects;

/**
 * Created by ychan on 1/26/16.
 */
public final class FactoredRealVectorPair {
  private final FactoredRealVector v1;
  private final FactoredRealVector v2;

  private FactoredRealVectorPair(final FactoredRealVector v1, final FactoredRealVector v2) {
    this.v1 = v1;
    this.v2 = v2;
  }

  public static FactoredRealVectorPair from(final FactoredRealVector v1, final FactoredRealVector v2) {
    return new FactoredRealVectorPair(v1, v2);
  }

  public FactoredRealVector getFirstVector() {
    return v1;
  }

  public FactoredRealVector getSecondVector() {
    return v2;
  }

  public String toString() {
    final StringBuilder sb = new StringBuilder();
    sb.append("<FactoredRealVectorPair>\n");
    sb.append("<v1>\n");
    sb.append(v1.toString());
    sb.append("\n");
    sb.append("</v1>\n");
    sb.append("<v2>\n");
    sb.append(v2.toString());
    sb.append("\n");
    sb.append("</v2>\n");
    sb.append("</FactoredRealVectorPair>");

    return sb.toString();
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
    final FactoredRealVectorPair other = (FactoredRealVectorPair) obj;
    return Objects.equal(v1, other.v1) &&
        Objects.equal(v2, other.v2);
  }
}
