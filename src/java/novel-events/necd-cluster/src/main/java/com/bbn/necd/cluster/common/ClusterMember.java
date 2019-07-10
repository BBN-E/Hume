package com.bbn.necd.cluster.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.RealVector;
import com.google.common.base.Function;
import com.google.common.base.Objects;
import com.google.common.base.Optional;

import static com.google.common.base.Preconditions.checkNotNull;

public final class ClusterMember {
  private final Symbol id;
  private final Optional<RealVector> unitV;               // unit vector
  private final Optional<RealVector> unNormalizedV;   // not unit vector

  private ClusterMember(final Symbol id, final RealVector unitV, final RealVector unNormalizedV) {
    this.id = checkNotNull(id);
    this.unitV = Optional.fromNullable(unitV);
    this.unNormalizedV = Optional.fromNullable(unNormalizedV);
  }

  // I will assume that vector is un-normalized
  public static ClusterMember from(final Symbol id, final RealVector vector) {
    if(vector!=null) {
      return new ClusterMember(id, vector.toUnitVector(), vector);
    } else {
      return new ClusterMember(id, null, null);
    }
  }

  public Symbol getId() {
    return id;
  }

  public Optional<RealVector> getUnitVector() {
    return unitV;
  }

  public Optional<RealVector> getUnNormalizedVector() {
    return unNormalizedV;
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(id);
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
    final ClusterMember other = (ClusterMember) obj;
    return Objects.equal(id, other.id);
  }

  public static final Function<ClusterMember, Symbol> ID =
      new Function<ClusterMember, Symbol>() {
        @Override
        public Symbol apply(final ClusterMember member) {
          return member.getId();
        }
      };


}
