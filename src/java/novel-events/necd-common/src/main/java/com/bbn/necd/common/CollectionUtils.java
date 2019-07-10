package com.bbn.necd.common;

import com.bbn.serif.theories.TokenSequence.Span;
import com.google.common.base.Function;
import com.google.common.collect.Ordering;

import java.util.Map;


public final class CollectionUtils {

  public static boolean spanPairIsInCorrectOrder(final Span m1, final Span m2) {
    final int m1Start = m1.startCharOffset().asInt();
    final int m1End = m1.endCharOffset().asInt();

    final int m2Start = m2.startCharOffset().asInt();
    final int m2End = m2.endCharOffset().asInt();

    if((m1Start <= m2Start) && (m1End <= m2End)) {
      return true;
    } else if( m1Start==m2Start ) {
      if(m1End <= m2End) {
        return true;
      } else {
        return false;
      }
    } else if( m1End==m2End ) {
      if(m1Start <= m2Start) {
        return true;
      } else {
        return false;
      }
    } else {
      if(m1End <= m2End) {
        return true;
      } else {
        return false;
      }
    }
  }

  public static final Ordering<Map.Entry<? extends Object, Double>> entryValueOrdering = Ordering.natural()
      .onResultOf(new Function<Map.Entry<?, Double>, Double>() {
        public Double apply(Map.Entry<?, Double> entry) {
          return entry.getValue();
        }
      }).reverse();
}
