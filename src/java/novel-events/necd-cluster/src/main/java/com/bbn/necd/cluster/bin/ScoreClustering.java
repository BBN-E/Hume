package com.bbn.necd.cluster.bin;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;
import com.bbn.necd.common.metric.BCubed;
import com.bbn.necd.common.metric.EvaluationMetric;
import com.bbn.necd.common.metric.NormalizedMutualInformation;
import com.bbn.necd.common.metric.PairwiseF;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;

/**
 * Created by ychan on 3/10/16.
 */
public final class ScoreClustering {
  private static final Logger log = LoggerFactory.getLogger(ScoreClustering.class);

  public static void main(final String[] argv) throws IOException {


    final ImmutableSet<ImmutableSet<Symbol>> goldClusters = readClusters(new File(argv[0]));
    final ImmutableSet<ImmutableSet<Symbol>> predictClusters = readClusters(new File(argv[1]));

    StringBuilder sb = new StringBuilder();
    final EvaluationMetric.F1 pairwiseFScore = PairwiseF.score(goldClusters, predictClusters);
    sb.append("pairwiseF:" + String
        .format("%.4f R=%.4f P=%.4f", pairwiseFScore.getF1Score(), pairwiseFScore.getRecall(),
            pairwiseFScore.getPrecision()) + "\n");
    final EvaluationMetric.F1 bCubedScore = BCubed.score(goldClusters, predictClusters);
    sb.append("bCubed:" + String
        .format("%.4f R=%.4f P=%.4f", bCubedScore.getF1Score(), bCubedScore.getRecall(),
            bCubedScore.getPrecision()) + "\n");
    final double nmiScore = NormalizedMutualInformation.score(goldClusters, predictClusters);
    sb.append("NMI:" + String.format("%.4f", nmiScore) + "\n");


    Files.asCharSink(new File(argv[2]), Charsets.UTF_8).write(sb.toString());
  }

  private static ImmutableSet<ImmutableSet<Symbol>> readClusters(final File infile) throws IOException {
    final ImmutableSet.Builder<ImmutableSet<Symbol>> ret = ImmutableSet.builder();

    for(final String line : Files.asCharSource(infile, Charsets.UTF_8).readLines()) {
      ret.add(SymbolUtils.setFrom(line.split(" ")));
    }

    return ret.build();
  }

}
