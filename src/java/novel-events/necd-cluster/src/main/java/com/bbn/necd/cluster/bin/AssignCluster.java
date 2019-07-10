package com.bbn.necd.cluster.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.cluster.common.Cluster;
import com.bbn.necd.cluster.common.ClusterMember;
import com.bbn.necd.cluster.common.ClusterMemberManager;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.metric.MemberSimilarity;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimap;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public final class AssignCluster {
  private static final Logger log = LoggerFactory.getLogger(AssignCluster.class);


  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final ImmutableSet<Symbol> membersToCluster =
        RealInstanceManager.readTargetMembers(params.getExistingFile("targetMembers.list"));

    final MemberSimilarity memberSimilarity = MemberSimilarity
        .from(params.getExistingFile("interMemberSimilarity"), Optional.<ImmutableSet<Symbol>>absent(),
            Optional.<Multimap<Symbol,Symbol>>absent());
    log.info("Read member similarity");

    final ClusterMemberManager
        clusterMemberManager = ClusterMemberManager.builder().withClusterMembers(membersToCluster).build();

    Map<Symbol, ClusterMember> idToClusterMember = Maps.newHashMap();
    for(ClusterMember c : clusterMemberManager.getClusterMembers()) {
      idToClusterMember.put(c.getId(), c);
    }

    // read cluster file, this would probably be cbc.finalClustering
    ImmutableList<Cluster> cbcClusters = readFileToClusters(params.getExistingFile("cluster.cbc"),
        params.getBoolean("cbc.calculateRealCentroid"), memberSimilarity, clusterMemberManager,
        idToClusterMember);

    ImmutableList<Cluster> ontologyClusters = readOntologyFileToClusters(params.getExistingFile("cluster.ontology"),
        params.getBoolean("cbc.calculateRealCentroid"), memberSimilarity, clusterMemberManager,
        idToClusterMember);

    List<String> outlines = Lists.newArrayList();
    // for each ontologyCluster, we find the most similar cbcCluster
    for(final Cluster oc : ontologyClusters) {
      final StringBuilder sb = new StringBuilder("");
      for(Symbol id : oc.getMemberIds()) {
        if(sb.length() > 0) {
          sb.append(" ");
        }
        sb.append(id.asString());
      }
      System.out.println("Looking at Cluster: " + sb.toString());

      Cluster maxCbcCluster = null;
      double maxScore = 0;
      for(final Cluster cc : cbcClusters) {
        double sim = oc.similarityWithCluster(cc, memberSimilarity);
        if(sim > maxScore) {
          maxScore = sim;
          maxCbcCluster = cc;
        }
      }
      if(maxScore > 0) {
        outlines.add(oc.getId().asString() + "\t" + oc.getMemberIdsAsString() + "\t" + maxScore
            + "\t" + maxCbcCluster.getCentroid().getId().asString() + "\t" + maxCbcCluster.getMemberIdsAsString());
      } else {
        System.out.println("Cannot find a most similar CBC cluster, for ontology cluster " + oc.getId().asString());
      }
    }

    Files.asCharSink(params.getCreatableFile("ontology.output"), Charsets.UTF_8).writeLines(outlines);
  }

  private static ImmutableList<Cluster> readOntologyFileToClusters(final File infile,
      final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity,
      final ClusterMemberManager clusterMemberManager, Map<Symbol, ClusterMember> idToClusterMember)
      throws IOException {
    ImmutableList.Builder<Cluster> ret = ImmutableList.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    int clusterCount = 0;
    for (final String line : lines) {
      final String[] tokens = line.split("\t");
      if(tokens.length < 2) {
        continue;
      }
      //System.out.println("len=" + tokens.length + " line=" + line);
      Symbol id = Symbol.from(tokens[0]); // this is the ontology class label

      Cluster.Builder clusterBuilder = Cluster.builder(calculateRealCentroid, memberSimilarity)
          .withId(id).withWeights(clusterMemberManager.getWeights());

      ImmutableSet.Builder<ClusterMember> membersBuilder = ImmutableSet.builder();
      final String[] memberStrings = tokens[1].replaceAll("\"", "").replaceAll(",", "").replaceAll(" ", "").split(" ");
      for (int i = 0; i < memberStrings.length; i++) {
        Symbol word = Symbol.from(memberStrings[i]);
        if(idToClusterMember.containsKey(word)) {
          membersBuilder.add(idToClusterMember.get(word));
        } else {
          System.out.println("idToClusterMember does not contain ontology keyword " + word.asString());
        }
      }
      ImmutableSet<ClusterMember> members = membersBuilder.build();

      if(members.size() == 0) {
        System.out.println("Skipping ontology class " + id.asString() + " because we have no info on [" + tokens[1] + "]");
      } else {
        ret.add(clusterBuilder.withMembers(members).build());
      }
    }

    return ret.build();
  }

  private static ImmutableList<Cluster> readFileToClusters(final File infile,
      final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity,
      final ClusterMemberManager clusterMemberManager, Map<Symbol, ClusterMember> idToClusterMember)
      throws IOException {
    ImmutableList.Builder<Cluster> ret = ImmutableList.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    int clusterCount = 0;
    for (final String line : lines) {
      Cluster.Builder clusterBuilder = Cluster.builder(calculateRealCentroid, memberSimilarity)
          .withId(Symbol.from("c" + clusterCount))
          .withWeights(clusterMemberManager.getWeights());

      ImmutableSet.Builder<ClusterMember> members = ImmutableSet.builder();
      final String[] tokens = line.split(" ");
      Symbol centriod = Symbol.from(tokens[0]);
      for (int i = 2; i < tokens.length; i++) {
        Symbol word = Symbol.from(tokens[i]);
        if(idToClusterMember.containsKey(word)) {
          members.add(idToClusterMember.get(word));
        } else {
          System.out.println("ERROR: idToClusterMember does not contain " + word.asString());
        }
      }

      ret.add(clusterBuilder.withMembers(members.build()).build());
    }

    return ret.build();
  }




}
