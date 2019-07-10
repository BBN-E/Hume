package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.RealVector;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;

import java.util.Map;

public final class ManhattanDistance {

  public static double distance(final ImmutableMap<Integer, Double> smallerHash, final ImmutableMap<Integer, Double> largerHash) {
    double sum = 0;

    for(Map.Entry<Integer, Double> entry : smallerHash.entrySet()) {
      final int key = entry.getKey();
      if(largerHash.containsKey(key)) {
        if(key == 0) {
          sum += 1;
        } else {
          sum += Math.abs(entry.getValue() - largerHash.get(key));
        }
      //} else {
      //  sum += Math.abs(entry.getValue());
      }
    }

    //for(final Integer index : Sets.difference(largerHash.keySet(), smallerHash.keySet())) {
    //  sum += Math.abs(largerHash.get(index));
    //}

    return sum;
  }

  public static double weightedDistance(final FactoredRealVector v1, final FactoredRealVector v2, final double[] weights) {
    double distance = 0;

    for(final Map.Entry<Symbol, RealVector> entry : v1.getFactors().entrySet()) {
      final Symbol factorId = entry.getKey();
      final RealVector v1Factor = entry.getValue();

      final Optional<RealVector> v2Factor = v2.getFactor(factorId);
      if(v2Factor.isPresent()) {
        distance += weightedDistance(v1Factor, v2Factor.get(), weights);
      }
    }

    return distance;
  }

  public static double weightedDistance(final RealVector v1, final RealVector v2, final double[] weights) {
    final ImmutableMap<Integer, Double> e1 = v1.getElements();
    final ImmutableMap<Integer, Double> e2 = v2.getElements();

    final double distance = (e1.size() < e2.size())? weightedDistance(e1, e2, weights) :
                            weightedDistance(e2, e1, weights);

    return distance;
  }

  public static double weightedDistance(final ImmutableMap<Integer, Double> smallerHash, final ImmutableMap<Integer, Double> largerHash,
      final double[] weights) {
    double sum = 0;

    for(Map.Entry<Integer, Double> entry : smallerHash.entrySet()) {
      final int key = entry.getKey();
      if(largerHash.containsKey(key)) {
        if(key == 0) {      // distance at index 0 is always 1 (this is the bias term)
          sum += weights[key];
        } else {
          sum += Math.abs(entry.getValue() - largerHash.get(key)) * weights[key];
        }
        //} else {
      //  sum += Math.abs(entry.getValue() * weights[key]);
      }
    }

    //for(final Integer index : Sets.difference(largerHash.keySet(), smallerHash.keySet())) {
    //  sum += Math.abs(largerHash.get(index) * weights[index]);
    //}

    return sum;
  }

  // distance on a specific index
  public static Optional<Double> distanceForIndex(final ImmutableMap<Integer, Double> e1, final ImmutableMap<Integer, Double> e2,
      final int index) {
    if(e1.containsKey(index) && e2.containsKey(index)) {
      if(index == 0) {
        return Optional.of(1.0);
      } else {
        return Optional.of(Math.abs(e1.get(index) - e2.get(index)));
      }
    //} else if(e1.containsKey(index)) {
    //  return Optional.of(Math.abs(e1.get(index)));
    //} else if(e2.containsKey(index)) {
    //  return Optional.of(Math.abs(e2.get(index)));
    } else {
      return Optional.absent();
    }
  }

  public static Optional<Double> weightedDistanceForIndex(final FactoredRealVector v1, final FactoredRealVector v2,
      final int index, final double weight) {
    final Optional<Double> distance = distanceForIndex(v1, v2, index);
    if(distance.isPresent()) {
      return Optional.of(distance.get() * weight);
    } else {
      return Optional.absent();
    }
  }

  public static Optional<Double> distanceForIndex(final FactoredRealVector v1, final FactoredRealVector v2,
      final int index) {
    final Optional<Double> value1 = v1.getValueByIndex(index);
    final Optional<Double> value2 = v2.getValueByIndex(index);

    if(value1.isPresent() && value2.isPresent()) {
      if(index == 0) {
        return Optional.of(1.0);
      } else {
        return Optional.of(Math.abs(value1.get() - value2.get()));
      }
    } else {
      return Optional.absent();
    }
  }

  public static Optional<Double> weightedDistanceForIndex(final ImmutableMap<Integer, Double> e1, final ImmutableMap<Integer, Double> e2,
      final int index, final double weight) {
    final Optional<Double> distance = distanceForIndex(e1, e2, index);
    if(distance.isPresent()) {
      return Optional.of(distance.get() * weight);
    } else {
      return Optional.absent();
    }
  }

}
