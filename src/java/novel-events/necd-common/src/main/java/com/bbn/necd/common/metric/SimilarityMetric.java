package com.bbn.necd.common.metric;

import com.bbn.necd.common.hypothesis.CosineHypothesis;
import com.bbn.necd.common.hypothesis.Hypothesis;
import com.bbn.necd.common.hypothesis.ManhattanHypothesis;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.PairedRealInstance;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedRealVector;

import com.google.common.collect.ImmutableList;

public final class SimilarityMetric {





  public enum MetricType {
    COSINE {
      @Override
      public double similarity(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights) {
        return CosineSimilarity.similarity(v1, v2);
      }

      @Override
      public double similarity(final RealVector v1, final RealVector v2, final double[] weights) {
        return CosineSimilarity.similarity(v1, v2);
      }

      @Override
      public CosineHypothesis hypothesisFrom(final ImmutableList<PairedRealInstance> examples, final double[] weights) {
        return CosineHypothesis.from(examples, weights);
      }
    }, WEIGHTED_COSINE {
      @Override
      public double similarity(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights) {
        return CosineSimilarity.weightedSimilarity(v1, v2, weights);
      }

      @Override
      public double similarity(final RealVector v1, final RealVector v2, final double[] weights) {
        return CosineSimilarity.weightedSimilarity((WeightedRealVector)v1, (WeightedRealVector)v2, weights);
      }

      @Override
      public CosineHypothesis hypothesisFrom(final ImmutableList<PairedRealInstance> examples, final double[] weights) {
        return CosineHypothesis.from(examples, weights);
      }
    }, WEIGHTED_MANHATTAN {
      @Override
      public double similarity(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights) {
        final double distance = ManhattanDistance.weightedDistance(v1, v2, weights);
        return sigmoid(distance);
      }

      @Override
      public double similarity(final RealVector v1, final RealVector v2, final double[] weights) {
        final double distance = ManhattanDistance.weightedDistance(v1, v2, weights);
        return sigmoid(distance);
      }

      @Override
      public ManhattanHypothesis hypothesisFrom(final ImmutableList<PairedRealInstance> examples, final double[] weights) {
        return ManhattanHypothesis.from(examples, weights);
      }
    };

    public abstract double similarity(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights);
    public abstract double similarity(final RealVector v1, final RealVector v2, final double[] weights);
    public abstract Hypothesis hypothesisFrom(final ImmutableList<PairedRealInstance> examples, final double[] weights);
  }

  private static double sigmoid(double x) {
    return 1/(1 + Math.exp(-x));
  }
}
