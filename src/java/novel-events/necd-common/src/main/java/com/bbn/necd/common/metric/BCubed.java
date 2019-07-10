package com.bbn.necd.common.metric;

import com.bbn.bue.common.primitives.DoubleUtils;
import com.bbn.bue.common.symbols.Symbol;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;
import java.util.Map;

public final class BCubed {
  private static final Logger log = LoggerFactory.getLogger(BCubed.class);

  public static EvaluationMetric.F1 score(final ImmutableSet<ImmutableSet<Symbol>> goldClusters, final ImmutableSet<ImmutableSet<Symbol>> predictionClusters) {
    assert EvaluationMetric.equalMembers(goldClusters, predictionClusters);

    final ImmutableMap<Symbol, ImmutableSet<Symbol>> goldMemberToCluster = getMemberToCluster(goldClusters);
    final ImmutableMultimap<Symbol, ImmutableSet<Symbol>> predictionMemberToCluster = getMemberToClusters(predictionClusters);

    final ImmutableMap<Symbol, Integer> predictionMemberTrueNeighborCounts = calculateNumberOfTrueNeighbors(goldMemberToCluster, predictionMemberToCluster);

    final ImmutableMap<Symbol, Double> precisionValues = calculateMemberScores(predictionMemberToCluster, predictionMemberTrueNeighborCounts, goldMemberToCluster);
    final ImmutableMap<Symbol, Double> recallValues = calculateMemberScores(goldMemberToCluster, predictionMemberTrueNeighborCounts, goldMemberToCluster);

    final double precision = precisionValues.size()>0? DoubleUtils.sum(precisionValues.values())/precisionValues.size() : 0;
    final double recall = recallValues.size()>0? DoubleUtils.sum(recallValues.values())/recallValues.size() : 0;

    return EvaluationMetric.F1.from(recall, precision);
  }

  private static ImmutableMap<Symbol, Double> calculateMemberScores(final ImmutableMultimap<Symbol, ImmutableSet<Symbol>> memberToCluster,
      final ImmutableMap<Symbol, Integer> memberTrueNeighborCounts,
      final ImmutableMap<Symbol, ImmutableSet<Symbol>> goldMemberToCluster) {
    final ImmutableMap.Builder<Symbol, Double> ret = ImmutableMap.builder();

    for(final Symbol member : memberToCluster.keySet()) {
      if(goldMemberToCluster.get(member).size() > 1) {
        final int numberOfTrueNeighbors = memberTrueNeighborCounts.get(member);

        final ImmutableSet.Builder<Symbol> ids = ImmutableSet.builder();
        for (final ImmutableSet<Symbol> cluster : memberToCluster.get(member)) {
          ids.addAll(cluster);
        }
        final int numberOfCandidateNeighbors =
            Sets.difference(ids.build(), ImmutableSet.of(member)).immutableCopy().size();

        double score = 0;
        if (numberOfTrueNeighbors > 0 && numberOfCandidateNeighbors > 0) {
          score = numberOfTrueNeighbors / (double) numberOfCandidateNeighbors;
        }
        ret.put(member, score);
      }
    }

    return ret.build();
  }

  private static ImmutableMap<Symbol, Double> calculateMemberScores(final ImmutableMap<Symbol, ImmutableSet<Symbol>> memberToCluster,
      final ImmutableMap<Symbol, Integer> memberTrueNeighborCounts,
      final ImmutableMap<Symbol, ImmutableSet<Symbol>> goldMemberToCluster) {
    final ImmutableMap.Builder<Symbol, Double> ret = ImmutableMap.builder();

    for(final Symbol member : memberToCluster.keySet()) {
      if (goldMemberToCluster.get(member).size() > 1) {
        final int numberOfTrueNeighbors = memberTrueNeighborCounts.get(member);

        final int numberOfCandidateNeighbors = memberToCluster.get(member).size() - 1;
        double score = 0;
        if (numberOfTrueNeighbors > 0 && numberOfCandidateNeighbors > 0) {
          score = numberOfTrueNeighbors / (double) numberOfCandidateNeighbors;
        }
        ret.put(member, score);
      }
    }

    return ret.build();
  }

  private static ImmutableMap<Symbol, Integer> calculateNumberOfTrueNeighbors(final ImmutableMap<Symbol, ImmutableSet<Symbol>> goldMemberToCluster,
      final ImmutableMultimap<Symbol, ImmutableSet<Symbol>> predictionMemberToCluster) {
    final ImmutableMap.Builder<Symbol, Integer> ret = ImmutableMap.builder();

    for(final Map.Entry<Symbol, Collection<ImmutableSet<Symbol>>> entry : predictionMemberToCluster.asMap().entrySet()) {
      final Symbol member = entry.getKey();
      final ImmutableSet.Builder<Symbol> ids = ImmutableSet.builder();
      for(final ImmutableSet<Symbol> cluster : entry.getValue()) {
        ids.addAll(cluster);
      }
      final ImmutableSet<Symbol> candidateNeighbors = Sets.difference(ids.build(), ImmutableSet.of(member)).immutableCopy();
      final int trueNeighborCount = calculateNumberOfTrueNeighbors(member, candidateNeighbors, goldMemberToCluster);

      ret.put(member, trueNeighborCount);
    }

    return ret.build();
  }

  private static int calculateNumberOfTrueNeighbors(final Symbol member, final ImmutableSet<Symbol> candidateNeighbors,
      final ImmutableMap<Symbol, ImmutableSet<Symbol>> goldMemberToCluster) {
    int count = 0;

    final ImmutableSet<Symbol> targetCluster = goldMemberToCluster.get(member);
    for(final Symbol n : candidateNeighbors) {
      if(goldMemberToCluster.containsKey(n)) {
        final ImmutableSet<Symbol> c = goldMemberToCluster.get(n);
        if(targetCluster.equals(c)) {
          count += 1;
        }
      }
    }

    return count;
  }

  private static ImmutableMap<Symbol, ImmutableSet<Symbol>> getMemberToCluster(final ImmutableSet<ImmutableSet<Symbol>> clusters) {
    final ImmutableMap.Builder<Symbol, ImmutableSet<Symbol>> ret = ImmutableMap.builder();

    for(final ImmutableSet<Symbol> cluster : clusters) {
      for(final Symbol member : cluster) {
        ret.put(member, cluster);
      }
    }

    return ret.build();
  }

  private static ImmutableMultimap<Symbol, ImmutableSet<Symbol>> getMemberToClusters(final ImmutableSet<ImmutableSet<Symbol>> clusters) {
    final ImmutableMultimap.Builder<Symbol, ImmutableSet<Symbol>> ret = ImmutableMultimap.builder();

    for(final ImmutableSet<Symbol> cluster : clusters) {
      for(final Symbol member : cluster) {
        ret.put(member, cluster);
      }
    }

    return ret.build();
  }

}
