package com.bbn.musiena.common.ui;


import com.bbn.musiena.common.embedding.EmbeddingUtils;
import com.bbn.musiena.common.embedding.Embeddings;
import com.bbn.musiena.common.metric.CosineSimilarity;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.base.Joiner;
import com.google.common.base.Optional;
import com.google.common.base.Splitter;
import com.google.common.collect.BiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Lists;
import com.google.common.collect.Multimap;
import com.google.common.collect.Sets;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class UIUtils {
  public static String printDomainTerms(final String domainListString) {
    final StringBuilder sb = new StringBuilder();
    sb.append("* Sample Scientific domains terms *\n");
    sb.append(domainListString);
    return sb.toString();
  }

  public static Optional<ImmutableMap<String, Double>> printListSimilarityUsingAverageEmbeddings(final String word, final int topK, final ImmutableMap<String, Integer> wordIdToIndex, final BiMap<Integer, String> indexToWordId, final Embeddings embeddings, final ImmutableList<Double> norms) {
    //final StringBuilder sb = new StringBuilder();

    //sb.append("** No embeddings for the phrase \"" + word.replace("_", " ") + "\". Averaging the embeddings of each individual word to calculate similarities.\n");

    final Optional<RealVector> rv = EmbeddingUtils
        .calculateAverageEmbeddings(word, embeddings, wordIdToIndex);

    if(rv.isPresent()) {
      final double queryNorm = CosineSimilarity.calculateL2Norm(rv.get().vector());
      final RealVector queryVector = RealVector.of(rv.get().id(), rv.get().vector());

      final ImmutableList<String> tokens = ImmutableList.copyOf(Splitter.on("_").split(word));
      Set<Integer> indices = Sets.newHashSet();
      for (int tokenIndex = 0; tokenIndex < tokens.size(); tokenIndex++) {
        final String w = tokens.get(tokenIndex);
        if (wordIdToIndex.containsKey(w)) {
          indices.add(wordIdToIndex.get(w));
        }
      }

      final Multimap<Double, String> sims =
          EmbeddingUtils
              .calculateSimilarityToOtherEmbeddings(indices, queryVector, queryNorm, indexToWordId,
                  embeddings, norms);

      return Optional.of(printTopKSimilarItems(sims, topK, false));
    } else {
      //sb.append("* No embeddings for any of the words");
      return Optional.absent();
    }

    //return sb.toString();
  }

  public static Optional<ImmutableMap<String, Double>> printListSimilarityOnthefly(final String word, final ImmutableMap<String, Integer> vocab, final int topK, final ImmutableMap<String, Integer> wordIdToIndex, final BiMap<Integer, String> indexToWordId, final Embeddings embeddings, final ImmutableList<Double> norms) {
    //final ImmutableMap.Builder<String, Double> ret = ImmutableMap.builder();
    //final StringBuilder sb = new StringBuilder();

    //sb.append("** No precomputed similarities for \"" + word.replace("_", " ") + "\" (" + vocab.get(word) + "), but we do have embeddings for the ");
    //if(word.contains("_")) {
    //  sb.append("phrase");
    //} else {
    //  sb.append("word");
    //}
    //sb.append(". Calculating similarities on-the-fly now.\n");

    final Multimap<Double, String> sims = EmbeddingUtils.calculateSimilarityToOtherEmbeddings(word, wordIdToIndex, indexToWordId, embeddings, norms);
    //sb.append(printTopKSimilarItems(sims, topK, false));
    return Optional.of(printTopKSimilarItems(sims, topK, false));

    //return sb.toString();

  }

  public static Optional<ImmutableMap<String, Double>> printPrecomputedSimilarity(final String word, final ImmutableMap<String, Integer> vocab, final ImmutableTable<String, String, Double> wordPairSimilarity, final int topK) {
    final ImmutableMap.Builder<String, Double> ret = ImmutableMap.builder();

    //final StringBuilder sb = new StringBuilder();
    //sb.append("** We have precomputed similarities for \"" + word.replace("_", " ") + "\" (" + vocab.get(word) + "), showing them below.\n");

    int counter = 0;
    for(final Map.Entry<String, Double> entry : wordPairSimilarity.row(word).entrySet()) {
      //System.out.println(String.format("%.3f",entry.getValue()) + " " + String.format("%s", entry.getKey().replace("_", " ")));
      //sb.append(String.format("%.3f",entry.getValue()) + " " + String.format("%s", entry.getKey().replace("_", " ")) + "\n");
      ret.put(entry.getKey().replace("_", " "), entry.getValue());
      counter += 1;
      if(counter >= topK) {
        break;
      }
    }

    //return sb.toString();

    return Optional.of(ret.build());
  }

  public static String printPairSimilarityOnthefly(final String word, final ImmutableMap<String, Integer> wordIdToIndex, final Embeddings embeddings) {
    String ret = "";

    final ImmutableList<String> terms = ImmutableList.copyOf(Splitter.on("_~_").split(word.replace("\"", "")));
    if(terms.size()==2) {
      final String term1 = terms.get(0);
      final String term2 = terms.get(1);

      Optional<RealVector> v1;
      Optional<RealVector> v2;

      if(wordIdToIndex.containsKey(term1)) {
        //System.out.println("* Retrieving embeddings for \"" + term1.replace("_", " ") + "\"");
        v1 = Optional.of(embeddings.getVectorByIndex(wordIdToIndex.get(term1)));
      } else {
        v1 = EmbeddingUtils.calculateAverageEmbeddings(term1, embeddings, wordIdToIndex);
      }

      if(wordIdToIndex.containsKey(term2)) {
        //System.out.println("* Retrieving embeddings for \"" + term2.replace("_", " ") + "\"");
        v2 = Optional.of(embeddings.getVectorByIndex(wordIdToIndex.get(term2)));
      } else {
        v2 = EmbeddingUtils.calculateAverageEmbeddings(term2, embeddings, wordIdToIndex);
      }

      if(!v1.isPresent() && !v2.isPresent()) {
        ret = "* No embeddings for the both term";
      }
      else if(!v1.isPresent()) {
        ret = "* No embeddings for the first term";
      } else if(!v2.isPresent()) {
        ret = "* No embeddings for the second term";
      } else {
        final double sim = CosineSimilarity.similarity(v1.get(), v2.get());
        ret = String.format("%.3f", sim);
      }

    } else {
      ret = "Error: There should exactly be 2 terms separated by ~ , e.g.: a_b ~ c";
    }

    return ret;
  }

  private static ImmutableMap<String, Double> printTopKSimilarItems(final Multimap<Double, String> sims, final int topK, final boolean ignoreSingleWords) {
    final ImmutableMap.Builder<String, Double> ret = ImmutableMap.builder();

    //final StringBuilder sb = new StringBuilder();

    boolean toBreak = false;
    int counter = 0;
    for (final Double sim : sims.keySet()) {
      for (final String w : sims.get(sim)) {
        if(!ignoreSingleWords || (ignoreSingleWords && w.contains("_"))) {
          //sb.append(String.format("%.3f", sim) + " " + w.replace("_", " ") + "\n");
          ret.put(w.replace("_", " "), sim);
          counter += 1;
          if (counter >= topK) {
            toBreak = true;
            break;
          }
        }
      }
      if (toBreak) {
        break;
      }
    }

    //return sb.toString();

    return ret.build();
  }

  public static String lemmatizePhrase(final String phrase, final ImmutableMap<String, String> lemmaDict) {
    final ImmutableList<String> tokens = ImmutableList.copyOf(Splitter.on(" ").trimResults().omitEmptyStrings().split(phrase));

    List<String> lemmas = Lists.newArrayList();
    for(final String token : tokens) {
      if(lemmaDict.containsKey(token)) {
        lemmas.add(lemmaDict.get(token));
      } else {
        lemmas.add(token);
      }
    }

    return Joiner.on("_").join(lemmas);
  }



  public static String similaritiesToString(ImmutableMap<String, Double> map) {
    final StringBuilder sb = new StringBuilder();

    for(final Map.Entry<String, Double> entry : map.entrySet()) {
      sb.append(entry.getKey() + " " + String.format("%.3f", entry.getValue()) + "\n");
    }

    return sb.toString();
  }

  public static ImmutableList<String> readResourceAsStrings(Class myclass, String resourceName) throws IOException {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    InputStream is = myclass.getResourceAsStream(resourceName);
    BufferedReader reader = new BufferedReader(new InputStreamReader(is, "UTF-8"));

    String line = "";
    while((line = reader.readLine())!=null) {
      ret.add(line);
    }

    return ret.build();
  }

}
