package com.bbn.musiena.common.embedding;


import com.bbn.musiena.common.metric.CosineSimilarity;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.base.Optional;
import com.google.common.base.Splitter;
import com.google.common.collect.BiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Multimap;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;
import com.google.common.collect.TreeMultimap;

import java.util.Set;

public final class EmbeddingUtils {
  public static Multimap<Double, String> calculateSimilarityToOtherEmbeddings(
      final Set<Integer> omitIndices,
      final RealVector queryVector, final double queryNorm,
      final BiMap<Integer, String> indexToWordId,
      final Embeddings embeddings, final ImmutableList<Double> norms) {

    Multimap<Double, String> sims =
        TreeMultimap.create(Ordering.natural().reverse(), Ordering.natural());
    for (int i = 0; i < embeddings.numberOfVectors(); i++) {
      if (!omitIndices.contains(i)) {
        final String w = indexToWordId.get(i);

        final RealVector v = embeddings.getVectorByIndex(i);
        final double vNorm = norms.get(i);
        final double sim =
            CosineSimilarity.similarity(queryVector.vector(), queryNorm, v.vector(), vNorm);

        sims.put(sim, w);
      }
    }

    return sims;
  }

  public static Multimap<Double, String> calculateSimilarityToOtherEmbeddings(final String word,
      final ImmutableMap<String, Integer> wordIdToIndex, final BiMap<Integer, String> indexToWordId,
      final Embeddings embeddings, final ImmutableList<Double> norms) {

    final int queryIndex = wordIdToIndex.get(word);
    final RealVector queryVector = embeddings.getVectorByIndex(queryIndex);
    final double queryNorm = norms.get(queryIndex);

    return calculateSimilarityToOtherEmbeddings(Sets.newHashSet(queryIndex), queryVector, queryNorm, indexToWordId, embeddings, norms);
  }

  public static Optional<RealVector> calculateAverageEmbeddings(final String word, final Embeddings embeddings, final ImmutableMap<String, Integer> wordIdToIndex) {
    final ImmutableList<String> tokens = ImmutableList.copyOf(Splitter.on("_").split(word));

    double[] newV = new double[embeddings.getDimensionSize()];
    double totalWeight = 0;

    Set<Integer> indices = Sets.newHashSet();

    for(int tokenIndex=0; tokenIndex<tokens.size(); tokenIndex++) {
      final String w = tokens.get(tokenIndex);

      if (wordIdToIndex.containsKey(w)) {
        System.out.println("** Using embeddings of '" + w + "'");

        final int queryIndex = wordIdToIndex.get(w);
        indices.add(queryIndex);

        final double[] v = embeddings.getVectorByIndex(queryIndex).vector();

        for (int i = 0; i < newV.length; i++) {
          newV[i] += v[i];
        }
        totalWeight += 1.0;
      }
    }

    if(totalWeight > 0) {
      for (int i = 0; i < newV.length; i++) {
        newV[i] = newV[i] / totalWeight;
      }

      return Optional.of(RealVector.of(word, newV));
    } else {
      return Optional.absent();
    }
  }

  public static RealVector calculateAverageEmbeddings(final ImmutableList<String> items, final Embeddings embeddings, final ImmutableMap<String, Integer> wordIdToIndex) {
    double[] newV = new double[embeddings.getDimensionSize()];

    for(final String word : items) {
      final double[] v = embeddings.getVectorByIndex(wordIdToIndex.get(word)).vector();

      for(int i=0; i<newV.length; i++) {
        newV[i] += v[i];
      }
    }

    for(int i=0; i<newV.length; i++) {
      newV[i] = newV[i]/items.size();
    }

    return RealVector.of("AVERAGE", newV);
  }

}
