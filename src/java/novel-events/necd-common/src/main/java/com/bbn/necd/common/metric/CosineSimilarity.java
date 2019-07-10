package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedRealVector;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;

import java.util.Map;

public final class CosineSimilarity {

  public static double similarity(final FactoredRealVector v1, final FactoredRealVector v2) {
    double dotProduct = 0;
    double v1Norm = 0;
    double v2Norm = 0;

    for(final Map.Entry<Symbol, RealVector> entry : v1.getFactors().entrySet()) {
      final Symbol factorId = entry.getKey();
      final RealVector v1Factor = entry.getValue();

      final Optional<RealVector> v2Factor = v2.getFactor(factorId);
      if(v2Factor.isPresent()) {
        dotProduct += dotProduct(v1Factor, v2Factor.get());
        v1Norm += v1Factor.getDotProduct();
        v2Norm += v2Factor.get().getDotProduct();
      }
    }

    if(dotProduct==0 || v1Norm==0 || v2Norm==0) {
      return 0;
    } else {
      return dotProduct / (Math.sqrt(v1Norm) * Math.sqrt(v2Norm));
    }
  }

  //if they are already unit vectors, then cosine is simply dot product. Else we need to normalize by their norms
  public static double similarity(final RealVector v1, final RealVector v2) {
    final double dotProduct = dotProduct(v1, v2);
    if(dotProduct==0 || v1.getNorm()==0 || v2.getNorm()==0) {
      return 0;
    } else {
      return (dotProduct / (v1.getNorm() * v2.getNorm()));
    }
  }

  public static double dotProduct(final RealVector v1, final RealVector v2) {
    final ImmutableMap<Integer, Double> e1 = v1.getElements();
    final ImmutableMap<Integer, Double> e2 = v2.getElements();

    final double dotProduct = (e1.size() < e2.size())? dotProduct(e1, e2) : dotProduct(e2, e1);
    return dotProduct;
  }

  // for efficiency, we iterate over the smaller map
  public static double dotProduct(final ImmutableMap<Integer, Double> smallerHash, final ImmutableMap<Integer, Double> largerHash) {
    double sim = 0;

    for(Map.Entry<Integer, Double> entry : smallerHash.entrySet()) {
      final int key = entry.getKey();
      if(largerHash.containsKey(key)) {
        sim += ( entry.getValue() * largerHash.get(key) );
      }
    }

    return sim;
  }

  public static double weightedSimilarity(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights) {
    double dotProduct = 0;
    double v1Norm = 0;
    double v2Norm = 0;

    for(final Map.Entry<Symbol, RealVector> entry : v1.getFactors().entrySet()) {
      final Symbol factorId = entry.getKey();
      final RealVector v1Factor = entry.getValue();

      final Optional<RealVector> v2Factor = v2.getFactor(factorId);
      if(v2Factor.isPresent()) {
        dotProduct += weightedDotProduct((WeightedRealVector)v1Factor, (WeightedRealVector)v2Factor.get(), weights);
        v1Norm += v1Factor.getDotProduct();
        v2Norm += v2Factor.get().getDotProduct();
      }
    }

    if(dotProduct==0 || v1Norm==0 || v2Norm==0) {
      return 0;
    } else {
      return dotProduct / (Math.sqrt(v1Norm) * Math.sqrt(v2Norm));
    }
  }

  public static double weightedSimilarity(final WeightedRealVector v1, final WeightedRealVector v2, final double[] weights) {
    final double dotProduct = weightedDotProduct(v1, v2, weights);
    if(dotProduct==0 || v1.getNorm()==0 || v2.getNorm()==0) {
      return 0;
    } else {
      return (dotProduct / (v1.getNorm() * v2.getNorm()));
    }
  }

  //public static double weightedSimilarity(final WeightedRealVector v1, final WeightedRealVector v2,
  //    final double dotProduct) {
  //   return (dotProduct/(v1.getNorm() * v2.getNorm()));
  //}

  public static double weightedDotProduct(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights) {
    double dotProduct = 0;

    for(final Map.Entry<Symbol, RealVector> entry : v1.getFactors().entrySet()) {
      final Symbol factorId = entry.getKey();
      final RealVector v1Factor = entry.getValue();

      final Optional<RealVector> v2Factor = v2.getFactor(factorId);
      if(v2Factor.isPresent()) {
        dotProduct += weightedDotProduct((WeightedRealVector)v1Factor, (WeightedRealVector)v2Factor.get(), weights);
      }
    }

    return dotProduct;
  }

  public static double weightedDotProduct(final WeightedRealVector v1, final WeightedRealVector v2, final double[] weights) {
    final ImmutableMap<Integer, Double> e1 = v1.getElements();
    final ImmutableMap<Integer, Double> e2 = v2.getElements();

    final double dotProduct = (e1.size() < e2.size())?  weightedDotProduct(e1, e2, weights) :  weightedDotProduct(e2, e1, weights);
    return dotProduct;
  }

  // for efficiency, we iterate over the smaller map
  public static double weightedDotProduct(final ImmutableMap<Integer, Double> smallerHash, final ImmutableMap<Integer, Double> largerHash,
      final double[] weights) {
    double sim = 0;

    for(Map.Entry<Integer, Double> entry : smallerHash.entrySet()) {
      final int key = entry.getKey();
      if(largerHash.containsKey(key)) {
        sim += ( entry.getValue() * largerHash.get(key) * weights[key] );
      }
    }

    return sim;
  }

  public static double calculateDotProduct(final double[] v1, final double[] v2) {
    double f = 0;
    for(int i=0; i<v1.length; i++) {
      f +=v1[i] * v2[i];
    }
    return f;
  }

  public static double calculateL2Norm(final double[] vector) {
    double f = 0;
    for(int i=0; i<vector.length; i++) {
      f += (vector[i] * vector[i]);
    }
    return Math.sqrt(f);
  }
}
