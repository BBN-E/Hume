package com.bbn.musiena.common.nlp;


import com.google.common.base.Charsets;
import com.google.common.base.Splitter;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Multimap;
import com.google.common.collect.Multiset;
import com.google.common.io.Files;
import com.google.common.io.PatternFilenameFilter;
import com.google.common.primitives.Doubles;

import java.io.BufferedReader;
import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.io.Writer;
import java.util.Map;
import java.util.regex.Pattern;

public final class NLPUtils {
  public static void constructVocabFile(final File embeddingFile, final File corpusFile, final File vocabFile, final int alphabetThreshold, final int freqThreshold) throws
                                                                                                                                                                     IOException {
    final ImmutableSet<String>
        vocabCandidates = getVocabCandidateFromEmbeddingFile(embeddingFile, alphabetThreshold);
    final ImmutableMap<String, Integer>
        freqCounts = countFreqInCorpus(vocabCandidates, corpusFile, freqThreshold);

    final Writer writer = Files.asCharSink(vocabFile, Charsets.UTF_8).openBufferedStream();
    for(final Map.Entry<String, Integer> entry : freqCounts.entrySet()) {
      writer.write(entry.getKey() + " " + entry.getValue() + "\n");
    }
    writer.close();
  }

  private static ImmutableMap<String, Integer> countFreqInCorpus(final ImmutableSet<String> vocab, final File corpusFile, final int freqThreshold) throws IOException {
    final BufferedReader reader = Files.asCharSource(corpusFile, Charsets.UTF_8).openBufferedStream();

    final Splitter splitter = Splitter.on(" ").trimResults().omitEmptyStrings();

    final ImmutableMultiset.Builder<String> multiSetBuilder = ImmutableMultiset.builder();

    String line;
    while((line = reader.readLine())!=null) {
      for(final String w : splitter.split(line)) {
        if(vocab.contains(w)) {
          multiSetBuilder.add(w);
        }
      }
    }
    reader.close();

    final ImmutableMap.Builder<String, Integer> ret = ImmutableMap.builder();
    for(final Multiset.Entry<String> entry : multiSetBuilder.build().entrySet()) {
      if(entry.getCount() >= freqThreshold) {
        ret.put(entry.getElement(), entry.getCount());
      }
    }

    return ret.build();
  }

  private static ImmutableSet<String> getVocabCandidateFromEmbeddingFile(final File embeddingFile, final int alphabetThreshold) throws IOException {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    final BufferedReader reader = Files.asCharSource(embeddingFile, Charsets.UTF_8).openBufferedStream();

    String line;
    while((line = reader.readLine())!=null) {
      final String w = line.substring(0, line.indexOf(" "));
      if(countAlphabets(w) >= alphabetThreshold) {
        ret.add(w);
      }
    }
    reader.close();

    return ret.build();
  }

  private static int countAlphabets(final String s) {
    int ret = 0;

    final char[] chars = s.toCharArray();
    for(int i=0; i<chars.length; i++) {
      if(chars[i]>='a' && chars[i]<='z') {
        ret += 1;
      }
    }

    return ret;
  }

  public static ImmutableMap<String, String> readLemmatizationDictionary(final File infile) throws
                                                                                            IOException {
    final ImmutableMap.Builder<String, String> ret = ImmutableMap.builder();

    final Splitter spaceSplitter = Splitter.on(" ");

    for(final String line : Files.asCharSource(infile, Charsets.UTF_8).readLines()) {
      final ImmutableList<String> tokens = ImmutableList.copyOf(spaceSplitter.split(line));
      ret.put(tokens.get(0), tokens.get(1));
    }

    return ret.build();
  }

  public static ImmutableTable<String, String, Double> readWordPairSimilarityFromFiles(final File dir, final int topK) throws IOException {
    final ImmutableTable.Builder<String, String, Double> ret = ImmutableTable.builder();

    Pattern pattern = Pattern.compile("^.*.sim");
    FilenameFilter filterByExtension = new PatternFilenameFilter(pattern);

    final File[] files = dir.listFiles(filterByExtension);
    for(int i=0; i<files.length; i++) {
      final File file = files[i];
      //log.info("Reading similarity from file {} of {}, {}", (i+1), files.length, file.getName());
      ret.putAll(readWordPairSimilarityFromFile(file, topK));
    }

    return ret.build();
  }

  private static ImmutableTable<String, String, Double> readWordPairSimilarityFromFile(final File infile, final int topK) throws IOException {
    final ImmutableTable.Builder<String, String, Double> ret = ImmutableTable.builder();

    final BufferedReader reader = Files.asCharSource(infile, Charsets.UTF_8).openBufferedStream();
    String line;

    Multimap<String, String> pairCounter = ArrayListMultimap.create();

    while((line = reader.readLine()) !=null) {
      final String[] tokens = line.split(" ");

      if (!pairCounter.containsKey(tokens[0]) || pairCounter.get(tokens[0]).size() < topK) {
        ret.put(tokens[0], tokens[1], Doubles.tryParse(tokens[2]));
        pairCounter.put(tokens[0], tokens[1]);
      }
    }

    return ret.build();
  }

  private static ImmutableList<String> getTopKSimilarItems(final Multimap<Double, String> sims, final int topK) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    boolean toBreak = false;
    int counter = 0;
    for (final Double sim : sims.keySet()) {
      for (final String w : sims.get(sim)) {
        ret.add(w);
        counter += 1;
        if (counter >= topK) {
          toBreak = true;
          break;
        }
      }
      if (toBreak) {
        break;
      }
    }

    return ret.build();
  }


}
