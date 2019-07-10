package com.bbn.necd.cluster.bin;

import com.bbn.bue.common.StringUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.cluster.algorithm.CBC;
import com.bbn.necd.cluster.algorithm.HAC;
import com.bbn.necd.cluster.common.Cluster;
import com.bbn.necd.cluster.common.ClusterMember;
import com.bbn.necd.cluster.common.ClusterMemberManager;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.metric.BCubed;
import com.bbn.necd.common.metric.EvaluationMetric;
import com.bbn.necd.common.metric.MemberSimilarity;
import com.bbn.necd.common.metric.NormalizedMutualInformation;
import com.bbn.necd.common.metric.PairwiseF;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.base.Predicates;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimap;
import com.google.common.collect.Multisets;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Set;

/*
  Parameters:
  - interMemberSimilarity
  - targetMembers.list
  - cbc.calculateRealCentroid

  - * from CBC
      - cbc.topSimilarMembersThreshold
      - cbc.committeeThreshold
      - cbc.residueThreshold
      - cbc.calculateRealCentroid
      - cbc.committeeSimilarityMethod
      - metricType (optional)

  - cbc.committees
  - cbc.finalClustering

  - if targetMembers.label is present:
    - scoring.scoreOutput
    - labelDistribution.finalClustering
    - scoring.scoreCommittee
    - labelDistribution.committee
*/
public final class RunCBC {

  private static final Logger log = LoggerFactory.getLogger(RunCBC.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final ImmutableSet<Symbol> membersToCluster =
        RealInstanceManager.readTargetMembers(params.getExistingFile("targetMembers.list"));

    // we want to know which word pairs are just grammatical variants
    Multimap<Symbol, Symbol> lemmaMap = ArrayListMultimap.create();
    readLemmaFile(params.getExistingFile("lemma.noun"), lemmaMap, membersToCluster);
    readLemmaFile(params.getExistingFile("lemma.verb"), lemmaMap, membersToCluster);

    final MemberSimilarity memberSimilarity = MemberSimilarity
        .from(params.getExistingFile("interMemberSimilarity"), Optional.of(membersToCluster), Optional.of(lemmaMap));
    log.info("Read member similarity");


    //final boolean hasInterSimilarity = memberSimilarity.hasInterSimilarity(membersToCluster);

    //if (!hasInterSimilarity) {
    //  log.error("All member pairs must have similarity information before running CBC");
    //  System.exit(1);
    //}

    /*
    final Optional<RealInstanceManager> realInstanceManager =
        params.getBoolean("cbc.calculateRealCentroid") ?
        Optional.of(RealInstanceManager.from(params)) :
        Optional.<RealInstanceManager>absent();
    log.info("prepared RealInstanceManager");

    final ClusterMemberManager clusterMemberManager = realInstanceManager.isPresent() ?
        ClusterMemberManager.builder().withClusterMembers(realInstanceManager.get().getInstances())
            .withWeights(realInstanceManager.get().getWeights()).build() :
        ClusterMemberManager.builder().withClusterMembers(membersToCluster).build();
    */

    if(params.getBoolean("cbc.calculateRealCentroid")) {
      log.error("Clustering with real centroid is currently disabled");
      System.exit(1);
    }

    final ClusterMemberManager clusterMemberManager = ClusterMemberManager.builder().withClusterMembers(membersToCluster).build();
    log.info("prepared ClusterMemberManager");

    final CBC cbc = CBC.from(params, memberSimilarity, clusterMemberManager).performClustering().build();

    writeCommitteesToFile(cbc, params.getCreatableFile("cbc.committees"));

    final ImmutableSet<Cluster> finalClustering =
        assignMembersToCommittees(cbc, clusterMemberManager, memberSimilarity, params.getBoolean("cbc.calculateRealCentroid"));
    writeClustersToFile(finalClustering, params.getCreatableFile("cbc.finalClustering"));

    if(params.isPresent("targetMembers.label")) {
      final ImmutableMap<Symbol, Symbol> memberIdToLabel = readMemberLabel(params.getExistingFile("targetMembers.label"));

      score(finalClustering, memberIdToLabel, params.getCreatableFile("scoring.scoreOutput"));
      writeLabelDistributionToFile(finalClustering, memberIdToLabel, params.getCreatableFile("labelDistribution.finalClustering"));

      score(cbc.getCommittees(), memberIdToLabel, params.getCreatableFile("scoring.scoreCommittee"));
      writeLabelDistributionToFile(cbc.getCommittees(), memberIdToLabel, params.getCreatableFile("labelDistribution.committee"));
    }
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

  private static void writeLabelDistributionToFile(final ImmutableSet<Cluster> clustering,
      final ImmutableMap<Symbol, Symbol> memberIdToLabel, final File outfile) throws IOException {
    int clusterIndex = 0;
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    final ImmutableSet<Symbol> membersWithLabel = memberIdToLabel.keySet();

    for (final Cluster cluster : clustering) {
      final ImmutableMultiset.Builder<Symbol> labelsBuilder = ImmutableMultiset.builder();
      for (final Symbol id : Iterables.filter(cluster.getMemberIds(), Predicates.in(membersWithLabel)) ) {
        final Symbol label = memberIdToLabel.get(id);
        labelsBuilder.add(label);
      }
      final ImmutableMultiset<Symbol> labels = labelsBuilder.build();

      final StringBuilder sb = new StringBuilder(String.valueOf(clusterIndex));
      for (final Symbol label : Multisets.copyHighestCountFirst(labels).elementSet()) {
        sb.append(" " + label.asString() + ":" + labels.count(label));
      }
      lines.add(sb.toString());

      clusterIndex += 1;
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static void score(final ImmutableSet<Cluster> clustering, final ImmutableMap<Symbol, Symbol> memberIdToLabel, final File outfile)
      throws IOException {

    final ImmutableSet<Symbol> membersWithLabel = memberIdToLabel.keySet();

    final ImmutableSet.Builder<Symbol> predictIdsBuilder = ImmutableSet.builder();
    for(final Cluster cluster : clustering) {
      predictIdsBuilder.addAll(cluster.getMemberIds());
    }
    final ImmutableSet<Symbol> predictIds = predictIdsBuilder.build();

    final ImmutableMultimap.Builder<Symbol, Symbol> labelToId = ImmutableMultimap.builder();
    for (final Map.Entry<Symbol, Symbol> entry : memberIdToLabel.entrySet()) {
      final Symbol id = entry.getKey();
      final Symbol label = entry.getValue();
      if(predictIds.contains(id)) {
        labelToId.put(label, id);
      }
    }

    final ImmutableSet.Builder<ImmutableSet<Symbol>> goldClustersBuilder = ImmutableSet.builder();
    for (final Map.Entry<Symbol, Collection<Symbol>> entry : labelToId.build().asMap().entrySet()) {
      goldClustersBuilder.add(ImmutableSet.copyOf(entry.getValue()));
    }
    final ImmutableSet<ImmutableSet<Symbol>> goldClusters = goldClustersBuilder.build();

    final ImmutableSet.Builder<ImmutableSet<Symbol>> predictClustersBuilder =
        ImmutableSet.builder();
    for (final Cluster cluster : clustering) {
      final ImmutableSet<Symbol> c = ImmutableSet.copyOf(Iterables.filter(cluster.getMemberIds(), Predicates.in(membersWithLabel)));
      if(c.size() > 0) {
        predictClustersBuilder.add(c);
      }
    }
    final ImmutableSet<ImmutableSet<Symbol>> predictClusters = predictClustersBuilder.build();

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


    Files.asCharSink(outfile, Charsets.UTF_8).write(sb.toString());
  }

  public static ImmutableMap<Symbol, Symbol> readMemberLabel(final File infile)
      throws IOException {
    final ImmutableMap.Builder<Symbol, Symbol> ret = ImmutableMap.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      ret.put(Symbol.from(tokens[0]), Symbol.from(tokens[1]));
    }

    return ret.build();
  }

  private static ImmutableSet<Cluster> assignMembersToCommittees(final CBC cbc,
      final ClusterMemberManager clusterMemberManager, final MemberSimilarity memberSimilarity,
      final boolean calculateRealCentroid) {
    final ImmutableSet.Builder<Cluster> ret = ImmutableSet.builder();

    Set<Symbol> committeeIds = Sets.newHashSet();   // store ids of all committees
    for (final Cluster committee : cbc.getCommittees()) {
      committeeIds.addAll(committee.getMemberIds());
    }

    Map<Cluster, Cluster.Builder> committeeToClusterBuilder = Maps.newHashMap();
    for (final Cluster committee : cbc.getCommittees()) {
      committeeToClusterBuilder
          .put(committee, Cluster.builder(calculateRealCentroid, memberSimilarity)
              .withId(committee.getId()).withWeights(clusterMemberManager.getWeights()));
    }

    // assign each member to the committee it is most similar to
    for (final ClusterMember member : clusterMemberManager.getClusterMembers()) {
      if(!committeeIds.contains(member.getId())) {
        final Cluster maxCommittee = cbc.getMostSimilarCommittee(member);
        if(maxCommittee==null) {
          log.info("WARNING: member {} is not similar to any committee, dropping it", member.getId().asString());
        } else {
          committeeToClusterBuilder.get(maxCommittee).withMember(member);
        }
      }
    }

    for(final Map.Entry<Cluster, Cluster.Builder> entry : committeeToClusterBuilder.entrySet()) {
      List<ClusterMember> members = Lists.newArrayList();
      members.addAll(entry.getKey().getMembers().asList());
      members.addAll(entry.getValue().getMembers().asList());

      double groupSim = 0;
      for (int i = 0; i < (members.size() - 1); i++) {
        for (int j = (i + 1); j < members.size(); j++) {
          final Optional<Double> pairSim =
              memberSimilarity.getSimilarity(members.get(i).getId(), members.get(j).getId());
          if (pairSim.isPresent()) {
            groupSim += pairSim.get();
          }
        }
      }

      final double avgGroupSim = HAC.calculateAverageGroupSimilarity(members.size(), groupSim);
      final double cohesion = members.size() * avgGroupSim;

      log.info("Building a new cluster with {} members, {} groupSim, {} avgGroupSim, {} cohesion", members.size(), groupSim, avgGroupSim, cohesion);


      final Cluster cluster = Cluster.builder(calculateRealCentroid, memberSimilarity).withId(entry.getKey().getId())
          .withWeights(clusterMemberManager.getWeights()).withGroupSimilarity(groupSim)
          .withAverageGroupSimilarity(avgGroupSim).withCohesion(cohesion).withMembers(ImmutableSet.copyOf(members)).build();
      cluster.getCentroid();

      if(cluster != null) {
        ret.add(cluster);
      }
    }

    /*
    for (final Cluster.Builder clusterBuilder : committeeToClusterBuilder.values()) {
      final ImmutableList<ClusterMember> members = clusterBuilder.getMembers().asList();

      double groupSim = 0;
      for (int i = 0; i < (members.size() - 1); i++) {
        for (int j = (i + 1); j < members.size(); j++) {
          final Optional<Double> pairSim =
              memberSimilarity.getSimilarity(members.get(i).getId(), members.get(j).getId());
          if (pairSim.isPresent()) {
            groupSim += pairSim.get();
          }
        }
      }

      final double avgGroupSim = HAC.calculateAverageGroupSimilarity(members.size(), groupSim);
      final double cohesion = members.size() * avgGroupSim;

      log.info("Building a new cluster with {} members, {} groupSim, {} avgGroupSim, {} cohesion", members.size(), groupSim, avgGroupSim, cohesion);

      final Cluster cluster =
          clusterBuilder.withGroupSimilarity(groupSim).withAverageGroupSimilarity(avgGroupSim)
              .withCohesion(cohesion).build();
      if(cluster != null) {
        ret.add(cluster);
      }
    }
    */

    return ret.build();
  }

  private static void writeClustersToFile(final ImmutableSet<Cluster> clusters, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    for (final Cluster cluster : clusters) {
      // instead of the previous cluster.getId() , we now get the centriod id
      lines.add(cluster.getCentroid().getId().asString() + " " + cluster.getCohesion() + " " + StringUtils.SpaceJoiner.join(cluster.getMemberIds()));
    }
    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static void writeCommitteesToFile(final CBC cbc, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    final ImmutableMultiset.Builder<Symbol> idsBuilder = ImmutableMultiset.builder();
    for (final Cluster cluster : cbc.getCommittees()) {
      idsBuilder.addAll(cluster.getMemberIds());
      // instead of the previous cluster.getId() , we now get the centriod id
      lines.add(cluster.getCentroid().getId().asString() + " " + cluster.getCohesion() + " " + StringUtils.SpaceJoiner.join(cluster.getMemberIds()));
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());

    final ImmutableMultiset<Symbol> ids = idsBuilder.build();
    log.info("Committees contain {} members, of which {} are distinct", ids.size(),
        ids.elementSet().size());
  }


}
