package com.bbn.necd.common.hypothesis;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairedRealInstance;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;


public interface Hypothesis {

  public ImmutableCollection<PairedRealInstance> getExamples();

  public PairedRealInstance getExampleById(final SymbolPair id);

  public ImmutableList<PairedRealInstance> getExamplesByIds(final ImmutableSet<SymbolPair> ids);

  public int getNumberOfExamples();

  public void updateCache(final double[] weights);

  public Hypothesis copyWithWeights(final double[] weights);

  public double value(final PairedRealInstance x, final double[] weights);

  public Optional<Double> derivative(final PairedRealInstance x,
      final double[] weights, final int featureIndex, final Symbol factorType);

  public double logLossDerivative(final PairedRealInstance x, final double[] weights, final int featureIndex, final Symbol factorType);

  public double logLossDerivative(final PairedRealInstance x, final double fv1, final double fv2);

  public double logLoss(final PairedRealInstance x, final double[] weights);

}
