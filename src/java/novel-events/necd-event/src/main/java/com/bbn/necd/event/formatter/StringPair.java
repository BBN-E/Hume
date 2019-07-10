package com.bbn.necd.event.formatter;

import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Ordering;

/**
 * Created by ychan on 2/4/16.
 * This should probably be moved somewhere to necd-common.
 * But this is currently only used within this package.
 */
public final class StringPair implements Comparable<StringPair> {
  private final String s1;
  private final String s2;

  private StringPair(final String s1, final String s2) {
    this.s1 = s1;
    this.s2 = s2;
  }

  public static StringPair from(final String s1, final String s2) {
    final ImmutableList<String> strings =
        Ordering.natural().immutableSortedCopy(ImmutableList.of(s1, s2));
    return new StringPair(strings.get(0), strings.get(1));
  }

  public static StringPair fromUnordered(final String s1, final String s2) {
    return new StringPair(s1, s2);
  }

  public String getFirstString() {
    return s1;
  }

  public String getSecondString() {
    return s2;
  }

  public int compareTo(final StringPair other) {
    if (!s1.equals(other.getFirstString())) {
      return s1.compareTo(other.getFirstString());
    } else {
      return s2.compareTo(other.getSecondString());
    }
  }

  public int hashCode() {
    return Objects.hashCode(s1, s2);
  }

  @Override
  public boolean equals(final Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null) {
      return false;
    }
    if (getClass() != obj.getClass()) {
      return false;
    }
    final StringPair other = (StringPair) obj;
    return Objects.equal(s1, other.s1) &&
        Objects.equal(s2, other.s2);
  }

  public static ImmutableSet<StringPair> toStringPairs(final ImmutableSet<String> strings1, final ImmutableSet<String> strings2) {
    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();

    for(final String s1 : strings1) {
      for(final String s2 : strings2) {
        ret.add(StringPair.from(s1, s2));
      }
    }

    return ret.build();
  }
}
