package com.bbn.musiena.common.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.musiena.common.CollectionUtils;
import com.bbn.musiena.common.embedding.Embeddings;
import com.bbn.musiena.common.metric.CosineSimilarity;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Maps;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.Collection;
import java.util.Map;

public final class CalculateSimilarityWithSeed {
  private static final Logger log = LoggerFactory.getLogger(CalculateSimilarityWithSeed.class);

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

    log.info("Loading embeddings");
    Embeddings embeddings = Embeddings.from(params);
    log.info("Loaded {} vectors", embeddings.getVectors().size());

    final ImmutableMap<String, Integer> wordIdToIndex = embeddings.constructWordIdToIndex();

    final ImmutableMultimap<String, String> seeds = readSeeds(params.getExistingFile("seeds"));

    // let's first compute the similarity of : seeds x vocab
    final ImmutableTable<String, String, Double> simTable =
        computeSimilarityBetweenSeedAndVocab(embeddings.getVectors(), seeds.values(),
            wordIdToIndex);

    // now assign each vocab to 1 cluster
    assignVocabToCluster(embeddings.getVectors(), seeds, simTable, params.getCreatableFile("cluster.output"));

  }

  private static void assignVocabToCluster(final ImmutableList<RealVector> vectors, final ImmutableMultimap<String, String> seeds, ImmutableTable<String, String, Double> simTable, final File outfile)
      throws IOException {
    final Writer writer = Files.asCharSink(outfile, Charsets.UTF_8).openBufferedStream();

    for(final RealVector v : vectors) {
      final String w = v.id();

      Map<String, Double> clusterSims = Maps.newHashMap();
      for(final Map.Entry<String, Collection<String>> cluster : seeds.asMap().entrySet()) {
        final String clusterId = cluster.getKey();

        double sim = 0;
        for(final String seed : cluster.getValue()) {
          sim += simTable.get(seed, w);
        }
        sim = sim/cluster.getValue().size();

        clusterSims.put(clusterId, sim);
      }

      for (final Map.Entry<String, Double> entry : CollectionUtils.entryValueOrdering
          .immutableSortedCopy(clusterSims.entrySet())) {
        final StringBuilder sb = new StringBuilder(w);
        sb.append(" ");
        sb.append(entry.getKey());
        sb.append(" ");
        sb.append(entry.getValue());
        sb.append("\n");
        writer.write(sb.toString());

        break;
      }
    }
  }

  private static ImmutableTable<String, String, Double> computeSimilarityBetweenSeedAndVocab(
      final ImmutableList<RealVector> vectors, final Collection<String> seeds,
      final ImmutableMap<String, Integer> wordIdToIndex) {
    final ImmutableTable.Builder<String, String, Double> ret = ImmutableTable.builder();

    final ImmutableList<Double> norms = CosineSimilarity.calculateL2Norms(vectors);

    for(final String seed : seeds) {
      final int seedId = wordIdToIndex.get(seed);
      final RealVector seedVector = vectors.get(seedId);
      final double seedNorm = norms.get(seedId);


      for(int i=0; i<vectors.size(); i++) {
        final RealVector otherVector = vectors.get(i);
        final double otherNorm = norms.get(i);

        final double sim = CosineSimilarity.similarity(seedVector.vector(), seedNorm, otherVector.vector(), otherNorm);
        ret.put(seed, otherVector.id(), sim);
      }
    }

    return ret.build();
  }

  private static ImmutableMultimap<String, String> readSeeds(final File infile) throws IOException {
    final ImmutableMultimap.Builder<String, String> ret = ImmutableMultimap.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();
    for(final String line : lines) {
      final String[] tokens = line.split("\t");
      final String clusterId = tokens[0];
      final String[] seeds = tokens[1].split(" ");

      for(int i=0; i<seeds.length; i++) {
        ret.put(clusterId, seeds[i]);
      }
    }

    return ret.build();
  }

}
