package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.collect.ImmutableSet;

import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class TestEvaluationMetric {
  // this example models Figure 16.4 in the Stanford IR book
  final Symbol x1 = Symbol.from("x1");
  final Symbol x2 = Symbol.from("x2");
  final Symbol x3 = Symbol.from("x3");
  final Symbol x4 = Symbol.from("x4");
  final Symbol x5 = Symbol.from("x5");
  final Symbol x6 = Symbol.from("x6");
  final Symbol x7 = Symbol.from("x7");
  final Symbol x8 = Symbol.from("x8");

  final Symbol o1 = Symbol.from("o1");
  final Symbol o2 = Symbol.from("o2");
  final Symbol o3 = Symbol.from("o3");
  final Symbol o4 = Symbol.from("o4");
  final Symbol o5 = Symbol.from("o5");

  final Symbol h1 = Symbol.from("h1");
  final Symbol h2 = Symbol.from("h2");
  final Symbol h3 = Symbol.from("h3");
  final Symbol h4 = Symbol.from("h4");

  final ImmutableSet<Symbol> class1 = ImmutableSet.of(x1, x2, x3, x4, x5, x6, x7, x8);
  final ImmutableSet<Symbol> class2 = ImmutableSet.of(o1, o2, o3, o4, o5);
  final ImmutableSet<Symbol> class3 = ImmutableSet.of(h1, h2, h3, h4);
  final ImmutableSet<ImmutableSet<Symbol>> goldClusters = ImmutableSet.of(class1, class2, class3);

  final ImmutableSet<Symbol> cluster1 = ImmutableSet.of(x1, x2, x3, x4, x5, o1);
  final ImmutableSet<Symbol> cluster2 = ImmutableSet.of(x6, o2, o3, o4, o5, h1);
  final ImmutableSet<Symbol> cluster3 = ImmutableSet.of(x7, x8, h2, h3, h4);
  final ImmutableSet<ImmutableSet<Symbol>> predictionClusters = ImmutableSet.of(cluster1, cluster2, cluster3);

  @Before
  public void setup() {

  }

  @Test
  public void pairwiseFTest() {
    final double score = PairwiseF.score(goldClusters, predictionClusters).getF1Score();
    assertEquals(0.476190476, score, 0.001);
  }

  @Test
  public void bcubedTest() {
    final double score = BCubed.score(goldClusters, predictionClusters).getF1Score();
    assertEquals(0.486437064, score, 0.001);
  }

  @Test
  public void nmiTest() {
    final double score = NormalizedMutualInformation.score(goldClusters, predictionClusters);
    assertEquals(0.364562, score, 0.001);
  }

}
