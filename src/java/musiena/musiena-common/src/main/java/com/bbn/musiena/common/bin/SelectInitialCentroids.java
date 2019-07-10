package com.bbn.musiena.common.bin;


import com.bbn.bue.common.parameters.Parameters;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Sets;
import com.google.common.io.Files;
import com.google.common.io.PatternFilenameFilter;
import com.google.common.primitives.Doubles;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.Set;
import java.util.regex.Pattern;

public final class SelectInitialCentroids {
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


    final ImmutableTable<String, String, Double> wordPairSimilarity = readWordPairSimilarityFromFiles(params.getExistingDirectory("similarityDirectory"));

    final ImmutableSet<String> vocab = wordPairSimilarity.rowKeySet();


    final String initialCentroid = getInitialCentroid(wordPairSimilarity, vocab);
    log.info("Initial centroid : {}", initialCentroid);

    final ImmutableList<String> logLines = getAllCentroid(wordPairSimilarity, vocab, initialCentroid);

    Files.asCharSink(params.getCreatableFile("centroids.output"), Charsets.UTF_8).writeLines(logLines);
  }


  private static ImmutableList<String> getAllCentroid(final ImmutableTable<String, String, Double> wordPairSimilarity, final ImmutableSet<String> vocab, final String initialCentroid) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    ret.add(initialCentroid);
    final String[] tokens = initialCentroid.split(" ");

    Set<String> centroids = Sets.newHashSet();

    centroids.add(tokens[0]);

    while(centroids.size() < NumberOfCentroids) {
      double minSim = 1;
      String candidateNextCentroid = "";
      for(final String query : vocab) {
        if(!centroids.contains(query)) {

          // average similarity to existing centroids
          double sim = 0;
          int count = 0;
          for(final String centroid : centroids) {
            if(wordPairSimilarity.contains(query, centroid)) {
              sim += wordPairSimilarity.get(query, centroid);
              count += 1;
            } else if(wordPairSimilarity.contains(centroid, query)) {
              sim += wordPairSimilarity.get(centroid, query);
              count += 1;
            }
          }

          if(count == centroids.size()) {
            if ((sim / count) < minSim) {
              minSim = (sim / count);
              candidateNextCentroid = query;
            }
          }
        }
      }
      centroids.add(candidateNextCentroid);

      log.info("centriods.size={}, adding {} {}", centroids.size(), candidateNextCentroid, minSim);

      ret.add(candidateNextCentroid + " " + minSim);
    }

    return ret.build();
  }

  // find the initial centroid, i.e. the word that is the most similar to all other words
  private static String getInitialCentroid(final ImmutableTable<String, String, Double> wordPairSimilarity, final ImmutableSet<String> vocab) {
    double maxSim = 0;
    String maxWord = "";

    int counter = 0;
    for(final String query : vocab) {
      double sim = 0;
      int count = 0;
      for(final String w : vocab) {
        if(!query.equals(w)) {
          if(wordPairSimilarity.contains(query, w)) {
            sim += wordPairSimilarity.get(query, w);
            count += 1;
          } else if(wordPairSimilarity.contains(w, query)) {
            sim += wordPairSimilarity.get(w, query);
            count += 1;
          }
        }
      }
      if((sim/count) > maxSim) {
        maxSim = (sim/count);
        maxWord = query;
      }

      counter += 1;
      if((counter % 500)==0) {
        log.info("Get initial centroid, processed {} out of {}", counter, vocab.size());
      }
    }

    return (maxWord + " " + maxSim);
  }

  private static ImmutableTable<String, String, Double> readWordPairSimilarityFromFiles(final File dir) throws IOException {
    final ImmutableTable.Builder<String, String, Double> ret = ImmutableTable.builder();

    Pattern pattern = Pattern.compile("^.*.sim");
    FilenameFilter filterByExtension = new PatternFilenameFilter(pattern);

    final File[] files = dir.listFiles(filterByExtension);
    for(int i=0; i<files.length; i++) {
      final File file = files[i];
      log.info("Reading similarity from file {} of {}, {}", (i+1), files.length, file.getName());
      ret.putAll(readWordPairSimilarityFromFile(file));
    }

    return ret.build();
  }

  private static ImmutableTable<String, String, Double> readWordPairSimilarityFromFile(final File infile) throws IOException {
    final ImmutableTable.Builder<String, String, Double> ret = ImmutableTable.builder();

    final BufferedReader reader = Files.asCharSource(infile, Charsets.UTF_8).openBufferedStream();
    String line;

    while((line = reader.readLine()) !=null) {
      final String[] tokens = line.split(" ");
      ret.put(tokens[0], tokens[1], Doubles.tryParse(tokens[2]));
    }

    return ret.build();
  }


  private static final int NumberOfCentroids = 500;
}
