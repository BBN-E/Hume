package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;

public final class EvaluationMetric {


  public static boolean equalMembers(final ImmutableSet<ImmutableSet<Symbol>> clusters1, final ImmutableSet<ImmutableSet<Symbol>> clusters2) {
    final ImmutableSet<Symbol> members1 = ImmutableSet.copyOf(Iterables.concat(clusters1));
    final ImmutableSet<Symbol> members2 = ImmutableSet.copyOf(Iterables.concat(clusters2));

    return members1.equals(members2);
  }

  public static int numberOfMembers(final ImmutableSet<ImmutableSet<Symbol>> clusters) {
    return ImmutableSet.copyOf(Iterables.concat(clusters)).size();
  }

  public static final class F1 {
    private final double recall;
    private final double precision;
    private final double f1Score;

    private F1(final double recall, final double precision, final double f1Score) {
      this.recall = recall;
      this.precision = precision;
      this.f1Score = f1Score;
    }

    public static F1 from(final double recall, final double precision) {
      double f1Score = 0;

      if(recall>0 && precision>0) {
        f1Score = (2*precision*recall)/(precision+recall);
      }
      return new F1(recall, precision, f1Score);
    }

    public double getRecall() {
      return recall;
    }

    public double getPrecision() {
      return precision;
    }

    public double getF1Score() {
      return f1Score;
    }
  }
}
