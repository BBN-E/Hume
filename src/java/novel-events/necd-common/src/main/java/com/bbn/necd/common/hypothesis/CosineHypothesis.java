package com.bbn.necd.common.hypothesis;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.PairedRealInstance;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedRealVector;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Set;

public final class CosineHypothesis implements Hypothesis {
  private static final Logger log = LoggerFactory.getLogger(CosineHypothesis.class);

  private final ImmutableMap<SymbolPair, PairedRealInstance> examples;
  private Map<SymbolPair, Double> dotProducts;
  private Map<SymbolPair, Double> hxValues;
  //private final ImmutableTable<Integer, Symbol, double[]> derivativeCache;
  private Map<Symbol, Double> norms;

  private CosineHypothesis(final ImmutableMap<SymbolPair, PairedRealInstance> examples) {
    this.examples = examples;
    this.dotProducts = Maps.newHashMap();
    this.hxValues = Maps.newHashMap();
    this.norms = Maps.newHashMap();
  }

  /*
  public static CosineHypothesis from(final ImmutableList<PairedRealInstance> examples, double[] weights) {
    final ImmutableMap.Builder<SymbolPair, PairedRealInstance> egBuilder = ImmutableMap.builder();
    for(final PairedRealInstance eg : examples) {
      egBuilder.put(eg.getIdPair(), eg);
    }

    return new CosineHypothesis(egBuilder.build());
  }
  */

  private CosineHypothesis(final ImmutableMap<SymbolPair, PairedRealInstance> examples,
      final ImmutableMap<SymbolPair, Double> dotProducts,
      final ImmutableMap<SymbolPair, Double> hxValues) {
      //final ImmutableTable<Integer, Symbol, double[]> derivativeCache) {
    this.examples = examples;
    this.dotProducts = dotProducts;
    this.hxValues = hxValues;
    //this.derivativeCache = derivativeCache;
  }

  public static CosineHypothesis from(final ImmutableList<PairedRealInstance> examples, double[] weights) {
    final ImmutableMap.Builder<SymbolPair, PairedRealInstance> egBuilder = ImmutableMap.builder();
    for(final PairedRealInstance eg : examples) {
      egBuilder.put(eg.getIdPair(), eg);
    }

    //log.info("calculating dot products {}", LocalDateTime.now());
    final ImmutableMap<SymbolPair, Double> dotProducts = calculateDotProduct(examples, weights);
    //log.info("calculating hxValues {}", LocalDateTime.now());
    final ImmutableMap<SymbolPair, Double> hxValues = calculateHxValues(examples, dotProducts);
    //log.info("calculating derivateCache {}", LocalDateTime.now());
    //final ImmutableTable<Integer, Symbol, double[]> derivativeCache = calculateDerivativeCache(examples);

    //log.info("Creating CosineHypothesis {}", LocalDateTime.now());
    return new CosineHypothesis(egBuilder.build(), dotProducts, hxValues);
  }



  public static CosineHypothesis from(final ImmutableMap<SymbolPair, PairedRealInstance> examples, double[] weights) {
    final ImmutableMap<SymbolPair, Double> dotProducts = calculateDotProduct(examples.values(), weights);
    final ImmutableMap<SymbolPair, Double> hxValues = calculateHxValues(examples.values(), dotProducts);
    //final ImmutableTable<Integer, Symbol, double[]> derivativeCache = calculateDerivativeCache(examples.values());
    return new CosineHypothesis(examples, dotProducts, hxValues);
  }


  public ImmutableCollection<PairedRealInstance> getExamples() {
    return examples.values();
  }

  public PairedRealInstance getExampleById(final SymbolPair id) {
    return examples.get(id);
  }

  public ImmutableList<PairedRealInstance> getExamplesByIds(final ImmutableSet<SymbolPair> ids) {
    final ImmutableList.Builder<PairedRealInstance> ret = ImmutableList.builder();

    for(final SymbolPair id : ids) {
      ret.add(examples.get(id));
    }

    return ret.build();
  }

  public int getNumberOfExamples() {
    return examples.size();
  }

  public void updateCache(final double[] weights) {

  }

  /*
  public void updateCache(final double[] weights) {
    Map<RealVector, Double> dotMap = Maps.newHashMap();   // dot products
    Map<RealVector, Double> normMap = Maps.newHashMap();  // norms

    for (final PairedRealInstance eg : examples.values()) {
      for(final RealVector vector : eg.getFirstMember().getFactors().values()) {
        final WeightedRealVector v = (WeightedRealVector)vector;
        if(!dotMap.containsKey(v)) {
          final double dotProduct = v.calculateDotProduct(v.getElements(), weights);
          dotMap.put(v, dotProduct);
          final double norm = Math.sqrt(dotProduct);
          normMap.put(v, norm);
        }
      }
      for(final RealVector vector : eg.getSecondMember().getFactors().values()) {
        final WeightedRealVector v = (WeightedRealVector)vector;
        if(!dotMap.containsKey(v)) {
          final double dotProduct = v.calculateDotProduct(v.getElements(), weights);
          dotMap.put(v, dotProduct);
          final double norm = Math.sqrt(dotProduct);
          normMap.put(v, norm);
        }
      }
    }

    this.norms.clear();
    for(final PairedRealInstance eg : examples.values()) {
      double dotSum = 0;
      if(!norms.containsKey(eg.getIdPair().getFirstMember())) {
        for (final RealVector v : eg.getFirstMember().getFactors().values()) {
          dotSum += dotMap.get(v);
        }
        norms.put(eg.getIdPair().getFirstMember(), Math.sqrt(dotSum));
      }

      if(!norms.containsKey(eg.getIdPair().getSecondMember())) {
        dotSum = 0;
        for (final RealVector v : eg.getSecondMember().getFactors().values()) {
          dotSum += dotMap.get(v);
        }
        norms.put(eg.getIdPair().getSecondMember(), Math.sqrt(dotSum));
      }
    }

    dotProducts.clear();
    calculateDotProduct(examples.values(), weights);

    hxValues.clear();
    calculateHxValues(examples.values(), dotProducts);



    //return CosineHypothesis.from(newExamples, weights);
    //final ImmutableMap<PairedRealInstance, Double> dotProducts = calculateDotProduct(newExamples, weights);

    //return new CosineHypothesis(newExamples, dotProducts);
  }
  */

  /*
  public CosineHypothesis copyWithWeights(final double[] weights) {
    return new CosineHypothesis(examples);
  }
  */


  public CosineHypothesis copyWithWeights(final double[] weights) {
    Map<RealVector, RealVector> rvMap = Maps.newHashMap();

    for (final PairedRealInstance eg : examples.values()) {
      for(final RealVector vector : eg.getFirstMember().getFactors().values()) {
        final WeightedRealVector v = (WeightedRealVector)vector;
        if(!rvMap.containsKey(v)) {
          rvMap.put(v, v.copyWithWeights(weights));
        }
      }
      for(final RealVector vector : eg.getSecondMember().getFactors().values()) {
        final WeightedRealVector v = (WeightedRealVector)vector;
        if(!rvMap.containsKey(v)) {
          rvMap.put(v, v.copyWithWeights(weights));
        }
      }
    }

    final ImmutableMap.Builder<SymbolPair, PairedRealInstance> examplesBuilder = ImmutableMap.builder();
    for(final PairedRealInstance eg : examples.values()) {
      final FactoredRealVector oldV1 = eg.getFirstMember();
      final FactoredRealVector.Builder v1Builder = FactoredRealVector.builder();
      for(final Map.Entry<Symbol, RealVector> entry : oldV1.getFactors().entrySet()) {
        v1Builder.withFactor(entry.getKey(), rvMap.get(entry.getValue()));
      }

      final FactoredRealVector oldV2 = eg.getSecondMember();
      final FactoredRealVector.Builder v2Builder = FactoredRealVector.builder();
      for(final Map.Entry<Symbol, RealVector> entry : oldV2.getFactors().entrySet()) {
        v2Builder.withFactor(entry.getKey(), rvMap.get(entry.getValue()));
      }

      examplesBuilder.put(eg.getIdPair(), PairedRealInstance.from(eg.getLabel(), v1Builder.build(), v2Builder.build(), eg.getIdPair()));
    }

    final ImmutableMap<SymbolPair, PairedRealInstance> newExamples = examplesBuilder.build();

    return CosineHypothesis.from(newExamples, weights);
    //final ImmutableMap<PairedRealInstance, Double> dotProducts = calculateDotProduct(newExamples, weights);

    //return new CosineHypothesis(newExamples, dotProducts);
  }


  private static ImmutableTable<Integer, Symbol, double[]> calculateDerivativeCache(final ImmutableCollection<PairedRealInstance> examples) {
    final ImmutableTable.Builder<Integer, Symbol, double[]> ret = ImmutableTable.builder();

    final Set<Symbol> instancesSet = Sets.newHashSet();
    final ImmutableMap.Builder<Symbol, FactoredRealVector> instancesBuilder = ImmutableMap.builder();
    for(final PairedRealInstance eg : examples) {
      final SymbolPair idPair = eg.getIdPair();
      if(!instancesSet.contains(idPair.getFirstMember())) {
        instancesBuilder.put(idPair.getFirstMember(), eg.getFirstMember());
        instancesSet.add(idPair.getFirstMember());
      }
      if(!instancesSet.contains(idPair.getSecondMember())) {
        instancesBuilder.put(idPair.getSecondMember(), eg.getSecondMember());
        instancesSet.add(idPair.getSecondMember());
      }
    }
    final ImmutableMap<Symbol, FactoredRealVector> instances = instancesBuilder.build();

    for(final Map.Entry<Symbol, FactoredRealVector> instance : instances.entrySet()) {
      final Symbol id = instance.getKey();
      final FactoredRealVector eg = instance.getValue();
      final double normInverse = 1.0/eg.getNorm();
      final double normInverseThrice = normInverse * normInverse * normInverse;

      for(final RealVector v : eg.getFactors().values()) {
        for(final Map.Entry<Integer, Double> entry : v.getElements().entrySet()) {
          final double w = entry.getValue();

          double[] derivativeElements = new double[3];
          derivativeElements[0] = normInverse;
          derivativeElements[1] = w * normInverse;
          derivativeElements[2] = w * w * normInverseThrice;

          ret.put(entry.getKey(), id, derivativeElements);
        }
      }
    }

    return ret.build();
  }

  // weighted dot product, thus we need the weights
  private static double calculateDotProduct(final PairedRealInstance x, final double[] weights) {
    return CosineSimilarity.weightedDotProduct(x.getFirstMember(), x.getSecondMember(), weights);
  }

  /*
  private void calculateDotProduct(final ImmutableCollection<PairedRealInstance> examples, final double[] weights) {
    for(final PairedRealInstance eg : examples) {
      dotProducts.put(eg.getIdPair(), calculateDotProduct(eg, weights));
    }
  }
  */

  private static ImmutableMap<SymbolPair, Double> calculateDotProduct(final ImmutableCollection<PairedRealInstance> examples, final double[] weights) {
    final ImmutableMap.Builder<SymbolPair, Double> ret = ImmutableMap.builder();

    for(final PairedRealInstance eg : examples) {
      ret.put(eg.getIdPair(), calculateDotProduct(eg, weights));
    }

    return ret.build();
  }

  /*
  private void calculateHxValues(final ImmutableCollection<PairedRealInstance> examples, final Map<SymbolPair, Double> dotProducts) {
    for(final PairedRealInstance eg : examples) {
      final double v1Norm = norms.get(eg.getIdPair().getFirstMember());
      final double v2Norm = norms.get(eg.getIdPair().getSecondMember());
      final double hx = dotProducts.get(eg.getIdPair())/(v1Norm * v2Norm);
      hxValues.put(eg.getIdPair(), hx);
    }
  }
  */

  private static ImmutableMap<SymbolPair, Double> calculateHxValues(final ImmutableCollection<PairedRealInstance> examples, final ImmutableMap<SymbolPair, Double> dotProducts) {
    final ImmutableMap.Builder<SymbolPair, Double> ret = ImmutableMap.builder();

    for(final PairedRealInstance x : examples) {
      final double dotProduct = dotProducts.get(x.getIdPair());
      final double v1Norm = x.getFirstMember().getNorm();
      final double v2Norm = x.getSecondMember().getNorm();

      if(dotProduct==0 || v1Norm==0 || v2Norm==0) {
        ret.put(x.getIdPair(), 0.0);
      } else {
        final double hx = Math.max(0, dotProduct / (v1Norm * v2Norm));
        ret.put(x.getIdPair(), hx);
      }
    }

    return ret.build();
  }


  public double value(final PairedRealInstance x, final double[] weights) {
    //return dotProducts.get(x.getIdPair())/(x.getFirstMember().getNorm() * x.getSecondMember().getNorm());
    return hxValues.get(x.getIdPair());
  }

  /*
  public Optional<Double> derivative(final PairedRealInstance x, final int featureIndex) {
    final SymbolPair idPair = x.getIdPair();

    final double[] values1 = derivativeCache.get(featureIndex, idPair.getFirstMember());
    final double[] values2 = derivativeCache.get(featureIndex, idPair.getSecondMember());

    // 0: normInverse
    // 1: w  * normInverse
    // 2: w*w * normInverseThrice

    final double factor1 = values1[1] * values2[1];
    final double factor2 = values1[2] * values2[0];
    final double factor3 = values1[0] * values2[2];
    final double dotProduct = dotProducts.get(x.getIdPair());

    return Optional.of(factor1 - ((dotProduct/2) * (factor2 + factor3)));
  }
  */

  // derivative at a specific weight
  public Optional<Double> derivative(final PairedRealInstance x,
      final double[] weights, final int featureIndex, final Symbol factorType) {
    final FactoredRealVector v1 = x.getFirstMember();
    final FactoredRealVector v2 = x.getSecondMember();

    final Optional<Double> fv1 = v1.getValueByFactorIndex(factorType, featureIndex);
    final Optional<Double> fv2 = v2.getValueByFactorIndex(factorType, featureIndex);

    //final Optional<Double> fv1 = Optional.of(0.001);
    //final Optional<Double> fv2 = Optional.of(0.002);

    //if(fv1.isPresent() || fv2.isPresent()) {
    if(fv1.isPresent() && fv2.isPresent()) {

      final double dotProduct = dotProducts.get(x.getIdPair());


      final double v1Norm = v1.getNorm();
      final double v2Norm = v2.getNorm();

      final double factor1 = (fv1.get() * fv2.get())/(v1Norm * v2Norm);

      final double factor2 = (fv1.get()*fv1.get()) * (1/(v1Norm*v1Norm*v1Norm * v2Norm));

      final double factor3 = (fv2.get()*fv2.get()) * (1/(v1Norm * v2Norm*v2Norm*v2Norm));

      return Optional.of(factor1 - ((dotProduct/2) * (factor2 + factor3)));


    } else {
      return Optional.absent();
    }
  }

  /*
  public double logLossDerivative(final PairedRealInstance x, final double[] weights, final int featureIndex) {
    return 0.0001;
  }
  */


  public double logLossDerivative(final PairedRealInstance x, final double[] weights, final int featureIndex, final Symbol factorType) {
    final Optional<Double> d = derivative(x, weights, featureIndex, factorType);
    //final Optional<Double> d = Optional.of(0.001);

    if(d.isPresent()) {
      final double y = (double)x.getLabel();

      //final double hx = value(x, weights);
      final double hx = hxValues.get(x.getIdPair());

      double loss = 0;
      if(y == hx) {
        loss = 0;
      } else if(hx > 0.999) {
        final double hx_p = 0.999;
        loss = ( (hx_p - y)/(hx_p*(1.0-hx_p)) ) * (d.get());
      } else if(hx < 0.001) {
        final double hx_p = 0.001;
        loss = ( (hx_p - y)/(hx_p*(1.0-hx_p)) ) * (d.get());
      } else {
        loss = ( (hx - y)/(hx*(1.0-hx)) ) * (d.get());
      }
      //final double loss = ( (hx - y)/(hx*(1.0-hx)) ) * (d.get());

      return loss;
    } else {
      return 0;
    }
  }

  private double derivative(final PairedRealInstance x, final double fv1, final double fv2) {
    final double dotProduct = dotProducts.get(x.getIdPair());

    final FactoredRealVector v1 = x.getFirstMember();
    final FactoredRealVector v2 = x.getSecondMember();

    final double v1Norm = v1.getNorm();
    final double v2Norm = v2.getNorm();

    if(v1Norm==0 || v2Norm==0) {
      return 0;
    } else {

      final double factor1 = (fv1 * fv2) / (v1Norm * v2Norm);

      final double factor2 = (fv1 * fv1) * (1 / (v1Norm * v1Norm * v1Norm * v2Norm));

      final double factor3 = (fv2 * fv2) * (1 / (v1Norm * v2Norm * v2Norm * v2Norm));

      return factor1 - ((dotProduct / 2) * (factor2 + factor3));
    }
  }


  public double logLossDerivative(final PairedRealInstance x, final double fv1, final double fv2) {
    final double d = derivative(x, fv1, fv2);

    final double y = (double)x.getLabel();
    final double hx = hxValues.get(x.getIdPair());

    double loss = 0;
    if(y == hx) {
      loss = 0;
    } else if(hx > 0.999) {
      final double hx_p = 0.999;
      loss = ( (hx_p - y)/(hx_p*(1.0-hx_p)) ) * d;
    } else if(hx < 0.001) {
      final double hx_p = 0.001;
      loss = ( (hx_p - y)/(hx_p*(1.0-hx_p)) ) * d;
    } else {
      loss = ( (hx - y)/(hx*(1.0-hx)) ) * d;
    }

    return loss;
  }


  public double logLoss(final PairedRealInstance x, final double[] weights) {
    //final WeightedRealVector v1 = (WeightedRealVector) x.getFirstMember();
    //final WeightedRealVector v2 = (WeightedRealVector) x.getSecondMember();
    final double y = (double)x.getLabel();

    //double hx = value(x, weights);
    double hx = hxValues.get(x.getIdPair());

    if(hx < 0.001) {
      hx = 0.001;
    } else if(hx > 0.999) {
      hx = 0.999;
    }

    //log.info("y={} , hx={} , log(hx)={} , log(1-hx)={}", y, hx, Math.log(hx), Math.log(1-hx));

    return y*Math.log(hx) + (1-y)*Math.log(1-hx);
  }


}

