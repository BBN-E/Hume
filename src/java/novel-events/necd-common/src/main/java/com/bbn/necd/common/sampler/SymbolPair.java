package com.bbn.necd.common.sampler;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.google.common.collect.Ordering;

import java.util.List;

/**
 * Created by ychan on 1/12/16.
 */
public final class SymbolPair {
  private final Symbol id1;
  private final Symbol id2;

  private SymbolPair(final Symbol id1, final Symbol id2) {
    this.id1 = id1;
    this.id2 = id2;
  }

  public static SymbolPair from(final Symbol id1, final Symbol id2) {
    final List<String> sorted = Ordering
        .natural().sortedCopy( Lists.newArrayList(id1.asString(), id2.asString()) );

    return new SymbolPair(Symbol.from(sorted.get(0)), Symbol.from(sorted.get(1)));
  }

  /*
   * No automatic sorting
   */
  public static SymbolPair fromUnordered(final Symbol id1, final Symbol id2) {
    return new SymbolPair(id1, id2);
  }

  public Symbol getFirstMember() {
    return id1;
  }

  public Symbol getSecondMember() {
    return id2;
  }

  public ImmutableList<Symbol> getMembers() {
    return ImmutableList.<Symbol>builder().add(id1).add(id2).build();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(id1, id2);
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

    // we assume symmetry, i.e. order does not matter
    final SymbolPair other = (SymbolPair) obj;
    return (Objects.equal(id1, other.id1) && Objects.equal(id2, other.id2)) ||
        (Objects.equal(id1, other.id2) && Objects.equal(id2, other.id1));
  }
}
