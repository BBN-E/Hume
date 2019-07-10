package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class NormalizedMutualInformation {
  private static final Logger log = LoggerFactory.getLogger(NormalizedMutualInformation.class);

  public static double score(final ImmutableSet<ImmutableSet<Symbol>> goldClusters, final ImmutableSet<ImmutableSet<Symbol>> predictionClusters) {
    assert EvaluationMetric.equalMembers(goldClusters, predictionClusters);

    final int N = EvaluationMetric.numberOfMembers(goldClusters);

    final double mi = mutualInformation(goldClusters, predictionClusters, N);
    final double predictionEntropy = entropy(predictionClusters, N);
    final double goldEntropy = entropy(goldClusters, N);

    final double nmi = mi / ((predictionEntropy + goldEntropy)/2);
    return nmi;
  }

  public static double mutualInformation(final ImmutableSet<ImmutableSet<Symbol>> goldClusters, final ImmutableSet<ImmutableSet<Symbol>> predictionClusters, final int N) {
    double mi = 0;

    for(final ImmutableSet<Symbol> predictionCluster : predictionClusters) {
      for(final ImmutableSet<Symbol> goldCluster : goldClusters) {
        final int intersectSize = Sets.intersection(predictionCluster, goldCluster).size();
        if(intersectSize > 0) {
          mi += intersectSize/(double)N * log2( N*intersectSize/(double)(predictionCluster.size()*goldCluster.size()) );
        }
      }
    }

    return mi;
  }

  private static double entropy(final ImmutableSet<ImmutableSet<Symbol>> clusters, final int N) {
    double entropy = 0;

    for(final ImmutableSet<Symbol> cluster : clusters) {
      final double prob = cluster.size()/(double)N;
      //log.info("cluster.size={}, N={}, prob={}, log2(p)={}", cluster.size(), N, prob, log2(prob));
      entropy += prob * log2(prob);
    }

    return -entropy;
  }

  private static double log2(final double x) {
    return Math.log(x)/Math.log(2);
  }
}


