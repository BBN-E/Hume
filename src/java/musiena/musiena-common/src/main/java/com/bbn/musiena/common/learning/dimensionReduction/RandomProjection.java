package com.bbn.musiena.common.learning.dimensionReduction;

import com.bbn.musiena.common.theory.BinaryVector;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;


public final class RandomProjection {
  private static final Logger log = LoggerFactory.getLogger(RandomProjection.class);

  private final ImmutableList<BinaryVector> vectors;
  private final ImmutableSetMultimap<Integer, String> invertedIndex;

  private RandomProjection(final ImmutableList<BinaryVector> vectors, final ImmutableSetMultimap<Integer, String> invertedIndex) {
    this.vectors = ImmutableList.copyOf(vectors);
    this.invertedIndex = ImmutableSetMultimap.copyOf(invertedIndex);
  }

  public static RandomProjection from(final ImmutableList<RealVector> realVectors) {
    final ImmutableList.Builder<BinaryVector> binaryVectorsBuilder = ImmutableList.builder();
    final ImmutableSetMultimap.Builder<Integer, String> invertedIndexBuilder = ImmutableSetMultimap.builder();

    for(final RealVector realVector : realVectors) {
      final BinaryVector binaryVector = toBinaryVector(realVector);
      binaryVectorsBuilder.add(binaryVector);

      // construct the inverted index
      final String id = binaryVector.id();
      final boolean[] values = binaryVector.vector();
      for(int i=0; i<values.length; i++) {
        if(values[i]) {
          invertedIndexBuilder.put(i, id);
        }
      }
    }

    final ImmutableList<BinaryVector> binaryVectors = binaryVectorsBuilder.build();
    log.info("Converted to {} binary vectors", binaryVectors.size());

    return new RandomProjection(binaryVectors, invertedIndexBuilder.build());
  }


  public double calculateSavingsFromInvertedIndex() {
    double usageRate = 0;

    int counter = 0;
    for(final BinaryVector v : vectors) {
      final boolean[] values = v.vector();

      Set<String> ids = Sets.newHashSet();
      for(int i=0; i<values.length; i++) {
        if(values[i]){
          ids.addAll(invertedIndex.get(i));
        }
      }

      usageRate += (double)(ids.size() - 1)/vectors.size(); // minus myself

      counter += 1;
      if((counter % 10)==0) {
        log.info("calculated {} out of {}, rate so far = {}", counter, vectors.size(), usageRate/counter);
      }
    }

    return usageRate/vectors.size();
  }

  public void pairwiseSimilarity() {

    for(int i=0; i<vectors.size(); i++) {
      for(int j=0; j<vectors.size(); j++) {
        if(i != j) {
          final double distance = hammingDistance(vectors.get(i).vector(), vectors.get(j).vector());
          final double sim = Math.cos(Math.PI * distance);
        }
      }

      if(((i+1) % 100)==0) {
        log.info("Calculated {} out of {}", (i+1), vectors.size());
      }
    }
  }

  private static BinaryVector toBinaryVector(final RealVector realVector) {
    final double[] v = realVector.vector();
    final boolean[] ret = new boolean[v.length];

    for(int i=0; i<v.length; i++) {
      if(v[i] >= 0) {
        ret[i] = true;
      }
    }

    return BinaryVector.builder().id(realVector.id()).vector(ret).build();
  }

  private static int hammingDistance(final boolean[] a, final boolean[] b) {
    int ret = 0;

    for(int i=0; i<a.length; i++) {
      if(a[i] ^ b[i]) {
        ret += 1;
      }
    }

    return ret;
  }

}
