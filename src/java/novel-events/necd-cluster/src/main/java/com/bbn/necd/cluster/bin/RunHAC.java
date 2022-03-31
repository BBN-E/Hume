package com.bbn.necd.cluster.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.cluster.algorithm.HAC;
import com.bbn.necd.cluster.common.ClusterMemberManager;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.metric.MemberSimilarity;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Multimap;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;


public final class RunHAC {
  private static final Logger log = LoggerFactory.getLogger(RunHAC.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final ImmutableSet<Symbol> membersToCluster =
        RealInstanceManager.readTargetMembers(params.getExistingFile("targetMembers.list"));

    // we want to know which word pairs are just grammatical variants
    Multimap<Symbol, Symbol> lemmaMap = ArrayListMultimap.create();
//    readLemmaFile(params.getExistingFile("lemma.noun"), lemmaMap, membersToCluster);
//    readLemmaFile(params.getExistingFile("lemma.verb"), lemmaMap, membersToCluster);

    final MemberSimilarity memberSimilarity = MemberSimilarity
        .from(params.getExistingFile("interMemberSimilarity"), Optional.of(membersToCluster),
            Optional.of(lemmaMap));
    log.info("Read member similarity");

    final ClusterMemberManager
        clusterMemberManager =
        ClusterMemberManager.builder().withClusterMembers(membersToCluster).build();
    log.info("prepared ClusterMemberManager");

    final HAC.Builder hacBuilder = HAC.builder().withWeights(clusterMemberManager.getWeights())
        .withClusterMembers(clusterMemberManager.getClusterMembers());
    final HAC hac = hacBuilder.performClustering(false, memberSimilarity).build();

    final ImmutableSet<String> hacStructure = hac.getHACStructure();
    Files.asCharSink(params.getCreatableFile("hac.output"), Charsets.UTF_8).writeLines(hacStructure);

  }

  private static void readLemmaFile(final File infile, Multimap<Symbol, Symbol> lemmaMap, ImmutableSet<Symbol> targetWords) throws IOException {
    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      final String[] tokens = line.split(" ");
      Symbol w1 = Symbol.from(tokens[0]);
      Symbol w2 = Symbol.from(tokens[1]);
      if(targetWords.contains(w1) && targetWords.contains(w2)) {
        lemmaMap.put(w1, w2);
        lemmaMap.put(w2, w1);
      }
    }
  }
}
