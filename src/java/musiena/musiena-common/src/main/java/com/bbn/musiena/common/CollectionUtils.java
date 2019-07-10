package com.bbn.musiena.common;

import com.google.common.base.Function;
import com.google.common.collect.Ordering;

import java.util.Map;

public final class CollectionUtils {
  public static final Ordering<Map.Entry<? extends Object, Double>> entryValueOrdering = Ordering.natural()
      .onResultOf(new Function<Map.Entry<?, Double>, Double>() {
        public Double apply(Map.Entry<?, Double> entry) {
          return entry.getValue();
        }
      }).reverse();
}
