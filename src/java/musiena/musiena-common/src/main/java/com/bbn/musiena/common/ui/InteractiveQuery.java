package com.bbn.musiena.common.ui;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.musiena.common.bin.CalculatePairwiseSimilarity;
import com.bbn.musiena.common.embedding.Embeddings;
import com.bbn.musiena.common.metric.CosineSimilarity;
import com.bbn.musiena.common.nlp.NLPUtils;

import com.google.common.base.Charsets;
import com.google.common.base.Joiner;
import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;

public final class InteractiveQuery {
  private static final Logger log = LoggerFactory.getLogger(CalculatePairwiseSimilarity.class);

  public static void main(String[] argv) {
    // we wrap the main method in this way to
    // ensure a non-zero return value on failure
    try {
      trueMain(argv);
    } catch (Exception e) {
      e.printStackTrace();
      System.exit(1);
    }
  }

  public static void trueMain(final String[] argv) throws IOException, ClassNotFoundException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final int topK = params.getInteger("topK");

    final String fs = File.separator;
    log.info("fs = {}", fs);

    final ImmutableMap<String, String> lemmaDict = NLPUtils.readLemmatizationDictionary(params.getExistingFile("lemmatization.dictionary"));

    log.info("Loading embeddings");
    Embeddings embeddings = Embeddings.from(params);
    log.info("Loaded {} vectors", embeddings.getVectors().size());

    final ImmutableMap<String, Integer> vocab = embeddings.getVocab();

    log.info("Calculating L2 norms for embeddings");
    final ImmutableList<Double> norms = CosineSimilarity.calculateL2Norms(embeddings.getVectors());

    log.info("Mapping wordIdToIndex");
    final ImmutableMap<String, Integer> wordIdToIndex = embeddings.constructWordIdToIndex();
    final BiMap<Integer, String> indexToWordId = HashBiMap.create(wordIdToIndex).inverse();

    log.info("Reading pre-computed word pair similarities");
    final ImmutableTable<String, String, Double> wordPairSimilarity = NLPUtils.readWordPairSimilarityFromFiles(params.getExistingDirectory("similarityDirectory"), topK);

    final String domainListString = Joiner.on("\n").join(Files.asCharSource(params.getExistingFile("domains.list"), Charsets.UTF_8).readLines());

    System.out.println("\n" + UIUtils.printDomainTerms(domainListString));


    BufferedReader input = new BufferedReader(new InputStreamReader(System.in));

    while(true) {
      System.out.print("Enter a query word: ");
      final String word = UIUtils.lemmatizePhrase(input.readLine(), lemmaDict);

      if(word.length()==0) {
        final String msg = UIUtils.printDomainTerms(domainListString);
        System.out.println(msg);
      }
      else if(word.contains("_~_")) {
        final String msg = UIUtils.printPairSimilarityOnthefly(word, wordIdToIndex, embeddings);
        System.out.println(msg);
      }
      else if(wordPairSimilarity.containsRow(word) && vocab.containsKey(word)) {
        final Optional<ImmutableMap<String, Double>> sims = UIUtils.printPrecomputedSimilarity(word, vocab, wordPairSimilarity, topK);
        if(sims.isPresent()) {
          System.out.println(UIUtils.similaritiesToString(sims.get()));
        }
      } else if(wordIdToIndex.containsKey(word)) {
        final Optional<ImmutableMap<String, Double>> sims = UIUtils.printListSimilarityOnthefly(word, vocab, topK, wordIdToIndex, indexToWordId, embeddings, norms);
        if(sims.isPresent()) {
          System.out.println(UIUtils.similaritiesToString(sims.get()));
        }
      } else if(word.contains("_")) {
        final Optional<ImmutableMap<String, Double>> sims = UIUtils.printListSimilarityUsingAverageEmbeddings(word, topK, wordIdToIndex, indexToWordId, embeddings, norms);
        if(sims.isPresent()) {
          System.out.println(UIUtils.similaritiesToString(sims.get()));
        } else {
          System.out.println("* No embeddings for any of the words");
        }
      } else {
        System.out.println("** This is a single word, and it is not in vocabulary **");
      }

      System.out.println("\n");
    }
  }















}
