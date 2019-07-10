package com.bbn.necd.common.hypothesis;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.metric.ManhattanDistance;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairedRealInstance;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class ManhattanHypothesis implements Hypothesis {
  private static final Logger log = LoggerFactory.getLogger(ManhattanHypothesis.class);

  final ImmutableMap<SymbolPair, PairedRealInstance> examples;
  final ImmutableMap<SymbolPair, Double> distances;

  private ManhattanHypothesis(final ImmutableMap<SymbolPair, PairedRealInstance> examples,
      final ImmutableMap<SymbolPair, Double> distances) {
    this.examples = examples;
    this.distances = distances;
  }

  public static ManhattanHypothesis from(final ImmutableList<PairedRealInstance> examples,
      final double[] weights) {
    final ImmutableMap.Builder<SymbolPair, PairedRealInstance> egBuilder = ImmutableMap.builder();
    for(final PairedRealInstance eg : examples) {
      egBuilder.put(eg.getIdPair(), eg);
    }

    final ImmutableMap<SymbolPair, Double> distances = calculateDistance(examples, weights);
    return new ManhattanHypothesis(egBuilder.build(), distances);
  }

  public ImmutableCollection<PairedRealInstance> getExamples() {
    return examples.values();
  }

  public ImmutableList<PairedRealInstance> getExamplesByIds(final ImmutableSet<SymbolPair> ids) {
    final ImmutableList.Builder<PairedRealInstance> ret = ImmutableList.builder();

    for(final SymbolPair id : ids) {
      ret.add(examples.get(id));
    }

    return ret.build();
  }

  public PairedRealInstance getExampleById(final SymbolPair id) {
    return examples.get(id);
  }

  public int getNumberOfExamples() {
    return examples.size();
  }

  public void updateCache(final double[] weights) {

  }

  public ManhattanHypothesis copyWithWeights(final double[] weights) {
    final ImmutableMap<SymbolPair, Double> distances = calculateDistance(examples.values(), weights);
    return new ManhattanHypothesis(examples, distances);
  }

  private static double calculateDistance(final PairedRealInstance x, final double[] weights) {
    return ManhattanDistance.weightedDistance(x.getFirstMember(), x.getSecondMember(), weights);
  }

  private static ImmutableMap<SymbolPair, Double> calculateDistance(final ImmutableCollection<PairedRealInstance> examples, final double[] weights) {
    final ImmutableMap.Builder<SymbolPair, Double> ret = ImmutableMap.builder();

    for(final PairedRealInstance eg : examples) {
      ret.put(eg.getIdPair(), calculateDistance(eg, weights));
    }

    return ret.build();
  }

  public double value(final PairedRealInstance x, final double[] weights) {
    return sigmoid(distances.get(x.getIdPair()));
  }

  // derivative at a specific weight
  public Optional<Double> derivative(final PairedRealInstance x,
      final double[] weights, final int featureIndex, final Symbol factorType) {
    return ManhattanDistance.weightedDistanceForIndex(x.getFirstMember(), x.getSecondMember(),
        featureIndex, weights[featureIndex]);
  }

  public double logLossDerivative(final PairedRealInstance x, final double[] weights, final int featureIndex, final Symbol factorType) {
    //final WeightedRealVector v1 = (WeightedRealVector) x.getFirstMember();
    //final WeightedRealVector v2 = (WeightedRealVector) x.getSecondMember();


    final Optional<Double> d = derivative(x, weights, featureIndex, factorType);

    if(d.isPresent()) {
      final double y = (double)x.getLabel();
      final double hx = value(x, weights);
      final double loss = (hx - y) * d.get();
      //log.info("loss={}, y={}, hx={}, d={}", loss, y, hx, d.get());
      return loss;
    } else {
      return 0;
    }
  }

  public double logLossDerivative(final PairedRealInstance x, final double fv1, final double fv2) {
    return 0;
  }

  public double logLoss(final PairedRealInstance x, final double[] weights) {
    //final WeightedRealVector v1 = (WeightedRealVector) x.getFirstMember();
    //final WeightedRealVector v2 = (WeightedRealVector) x.getSecondMember();
    final double y = (double)x.getLabel();

    final double hx = value(x, weights);

    return y*Math.log(hx) + (1-y)*Math.log(1-hx);
  }

  private static double sigmoid(double x) {
    return 1/(1 + Math.exp(-x));
  }



}

