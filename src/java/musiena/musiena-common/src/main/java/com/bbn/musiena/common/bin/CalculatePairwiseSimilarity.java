package com.bbn.musiena.common.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.musiena.common.embedding.Embeddings;
import com.bbn.musiena.common.metric.CosineSimilarity;
import com.bbn.musiena.common.theory.RealVector;

import com.google.common.collect.ImmutableList;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;

public final class CalculatePairwiseSimilarity {
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

    log.info("Loading embeddings");
    Embeddings embeddings = Embeddings.from(params);
    log.info("Loaded {} vectors", embeddings.getVectors().size());

    //log.info("Performing random projections");
    //RandomProjection randomProjection = RandomProjection.from(embeddings.getVectors());
    //randomProjection.pairwiseSimilarity();

    final int numberOfThreads = params.getInteger("numberOfThreads");
    final String outputDir = params.getString("outputDir");
    final int topK = params.getInteger("topK");
    final double simThreshold = params.getDouble("simThreshold");
    final CosineSimilarity cosineSimilarity = CosineSimilarity.from(embeddings.getVectors(), numberOfThreads, outputDir, topK, simThreshold);
    cosineSimilarity.doTraining();

    //bruteForcePairwiseSimilarity(embeddings);
  }

  private static void bruteForcePairwiseSimilarity(final Embeddings embeddings) {
    final ImmutableList<RealVector> vectors = embeddings.getVectors();

    log.info("Calculating L2 norms");
    final ImmutableList<Double> norms = CosineSimilarity.calculateL2Norms(vectors);
    log.info("Done with L2 norms");

    for(int i=0; i<vectors.size(); i++) {
      final double[] v1 = vectors.get(i).vector();
      final double v1Norm = norms.get(i);

      for(int j=0; j<vectors.size(); j++) {
        if(i != j) {
          final double sim = CosineSimilarity.similarity(v1, v1Norm, vectors.get(j).vector(), norms.get(j));
        }
      }

      if(((i+1) % 100)==0) {
        log.info("Calculated {} out of {}", (i+1), vectors.size());
      }
    }
  }
}
