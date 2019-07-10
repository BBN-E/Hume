package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.PairwiseSampler;
import com.bbn.necd.common.sampler.SamplerCluster;
import com.bbn.necd.common.sampler.SymbolPair;

import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class PairwiseF {
  private static final Logger log = LoggerFactory.getLogger(PairwiseF.class);

  public static EvaluationMetric.F1 score(final ImmutableSet<ImmutableSet<Symbol>> goldClusters, final ImmutableSet<ImmutableSet<Symbol>> predictionClusters) {
    assert EvaluationMetric.equalMembers(goldClusters, predictionClusters);

    final ImmutableSet<SymbolPair> goldPairs = PairwiseSampler.getIntraPairsFromAllClusters(toSamplerClusters(goldClusters));
    final ImmutableSet<SymbolPair> predictionPairs = PairwiseSampler.getIntraPairsFromAllClusters(toSamplerClusters(predictionClusters));

    final double recall = recall(goldPairs, predictionPairs);
    final double precision = precision(goldPairs, predictionPairs);

    return EvaluationMetric.F1.from(recall, precision);
  }

  private static ImmutableSet<SamplerCluster> toSamplerClusters(final ImmutableSet<ImmutableSet<Symbol>> clusters) {
    final ImmutableSet.Builder<SamplerCluster> ret = ImmutableSet.builder();

    int runningId = 1;
    for(final ImmutableSet<Symbol> cluster : clusters) {
      ret.add(SamplerCluster.builder(Symbol.from(String.valueOf(runningId++))).withIds(cluster).build());
    }

    return ret.build();
  }

  private static double recall(final ImmutableSet<SymbolPair> gold, final ImmutableSet<SymbolPair> prediction) {
    if(gold.size()==0 || prediction.size()==0) {
      return 0.0;
    } else {
      final int commonCount = Sets.intersection(gold, prediction).size();
      return commonCount/(double)gold.size();
    }
  }

  private static double precision(final ImmutableSet<SymbolPair> gold, final ImmutableSet<SymbolPair> prediction) {
    if(gold.size()==0 || prediction.size()==0) {
      return 0.0;
    } else {
      final int commonCount = Sets.intersection(gold, prediction).size();
      return commonCount/(double)prediction.size();
    }
  }


}
