package com.bbn.necd.cluster.algorithm;


import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.cluster.common.Cluster;
import com.bbn.necd.cluster.common.ClusterMember;
import com.bbn.necd.cluster.common.ClusterMemberManager;
import com.bbn.necd.common.CollectionUtils;
import com.bbn.necd.common.metric.MemberSimilarity;
import com.bbn.necd.common.metric.SimilarityMetric.MetricType;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.List;
import java.util.Map;

/*
  Parameters:
  - cbc.topSimilarMembersThreshold
  - cbc.committeeThreshold
  - cbc.residueThreshold
  - cbc.calculateRealCentroid
  - cbc.committeeSimilarityMethod
  - metricType (optional)
*/
public final class CBC {

  private static final Logger log = LoggerFactory.getLogger(CBC.class);

  private final ImmutableSet<Cluster> committees;
  private final int topSimilarMembersThreshold;
  private final double committeeThreshold;
  private final double residueThreshold;

  private final MemberSimilarity memberSimilarity;
  private final double[] weights;   // if calculateRealCentroid is true, this must be non null

  private final Optional<MetricType> metricType;  // must be present if calculateRealCentroid is true
  private final boolean calculateRealCentroid;
  private final CommitteeSimilarityMethod committeeSimilarityMethod;

  private CBC(final ImmutableSet<Cluster> committees,
      final int topSimilarMembersThreshold, final double committeeThreshold,
      final double residueThreshold,
      final MemberSimilarity memberSimilarity, final double[] weights,
      final Optional<MetricType> metricType, final boolean calculateRealCentroid,
      final CommitteeSimilarityMethod committeeSimilarityMethod) {
    this.committees = ImmutableSet.copyOf(committees);
    this.topSimilarMembersThreshold = topSimilarMembersThreshold;
    this.committeeThreshold = committeeThreshold;
    this.residueThreshold = residueThreshold;

    this.memberSimilarity = memberSimilarity;
    this.weights = weights;
    this.metricType = metricType;
    this.calculateRealCentroid = calculateRealCentroid;
    this.committeeSimilarityMethod = committeeSimilarityMethod;
  }

  public ImmutableSet<Cluster> getCommittees() {
    return committees;
  }

  public int getTopSimilarMembersThreshold() {
    return topSimilarMembersThreshold;
  }

  public double getCommitteeThreshold() {
    return committeeThreshold;
  }

  public double getResidueThreshold() {
    return residueThreshold;
  }

  private Cluster getMostSimilarCommitteeByCentroid(final ClusterMember member) {
    double maxSim = 0;
    Cluster maxCommittee = null;

    for (final Cluster committee : committees) {
      double sim = 0;
      if (calculateRealCentroid) {
        sim = metricType.get().similarity(member.getUnNormalizedVector().get(),
            committee.getCentroid().getUnNormalizedVector().get(), weights);
      } else {
        if (member.getId().equalTo(committee.getCentroid().getId())) {
          sim = 1.0;
        } else {
          Optional<Double> s = memberSimilarity.getSimilarity(member.getId(), committee.getCentroid().getId());
          if(s.isPresent()) {
            sim += s.get();
          }
        }
      }

      if (sim > maxSim) {
        maxSim = sim;
        maxCommittee = committee;
      }
    }

    return maxCommittee;
  }

  private Cluster getMostSimilarCommitteeByAverage(final ClusterMember member) {
    double maxSim = 0;
    Cluster maxCommittee = null;

    for (final Cluster committee : committees) {
      double sim = 0;

      for(final ClusterMember m : committee.getMembers()) {
        if(member.getId().equalTo(m.getId())) {
          sim += 1.0;
        } else {
          Optional<Double> s = memberSimilarity.getSimilarity(member.getId(), m.getId());
          if(s.isPresent()) {
            sim += s.get();
          }
        }
      }
      sim = sim/(double)committee.size();

      if (sim > maxSim) {
        maxSim = sim;
        maxCommittee = committee;
      }
    }

    return maxCommittee;
  }

  private Cluster getMostSimilarCommitteeByMax(final ClusterMember member) {
    double maxSim = 0;
    Cluster maxCommittee = null;

    for (final Cluster committee : committees) {

      for(final ClusterMember m : committee.getMembers()) {
        double sim = 0;
        if(member.getId().equalTo(m.getId())) {
          sim = 1.0;
        } else {
          Optional<Double> s = memberSimilarity.getSimilarity(member.getId(), m.getId());
          if(s.isPresent()) {
            sim = s.get();
          } else {
            sim = 0;
          }
        }

        if (sim > maxSim) {
          maxSim = sim;
          maxCommittee = committee;
        }
      }
    }

    return maxCommittee;
  }

  public Cluster getMostSimilarCommittee(final ClusterMember member) {
    switch (committeeSimilarityMethod) {
      case CENTROID:
        return getMostSimilarCommitteeByCentroid(member);
      case AVERAGE:
        return getMostSimilarCommitteeByAverage(member);
      case MAX:
        return getMostSimilarCommitteeByMax(member);
      default:
        throw new IllegalStateException("Unhandled committee similarity method");
    }
  }

  public static Builder from(final Parameters params, final MemberSimilarity memberSimilarity,
      final ClusterMemberManager clusterMemberManager) throws IOException {
    return new Builder(params, memberSimilarity, clusterMemberManager);
  }

  public static class Builder {

    private final ImmutableSet.Builder<Cluster> committeesBuilder;
    private final int topSimilarMembersThreshold;
    private final double committeeThreshold;
    private final double residueThreshold;

    private final MemberSimilarity memberSimilarity;
    private final ClusterMemberManager clusterMemberManager;
    private final double[] weights;   // if calculateRealCentroid is true, this must be non null

    private final Optional<MetricType> metricType;  // must be present if calculateRealCentroid is true
    private final boolean calculateRealCentroid;
    private final CommitteeSimilarityMethod committeeSimilarityMethod;
    //private final boolean filterCommittees;         // whether to filter via 1 standard deviation from mean

    private Map<Symbol, ClusterMember> membersMap = Maps.newHashMap();  // instance-id -> instance

    private int clusterIndex;

    private Builder(final Parameters params, final MemberSimilarity memberSimilarity,
        final ClusterMemberManager clusterMemberManager) throws IOException {
      this.committeesBuilder = ImmutableSet.builder();

      this.topSimilarMembersThreshold = params.getInteger("cbc.topSimilarMembersThreshold");
      this.committeeThreshold = params.getDouble("cbc.committeeThreshold");
      this.residueThreshold = params.getDouble("cbc.residueThreshold");

      this.memberSimilarity = memberSimilarity;
      this.clusterMemberManager = clusterMemberManager;
      this.weights = clusterMemberManager.getWeights();

      this.metricType = params.isPresent("metricType") ? Optional
          .of(params.getEnum("metricType", MetricType.class)) : Optional.<MetricType>absent();
      this.calculateRealCentroid = params.getBoolean("cbc.calculateRealCentroid");
      this.committeeSimilarityMethod = params.getEnum("cbc.committeeSimilarityMethod", CommitteeSimilarityMethod.class);
      //this.filterCommittees = params.getBoolean("cbc.filterCommittees");
    }

    public Builder performClustering() {
      clusterIndex = 0;   // initialize

      final ImmutableList<ClusterMember> clusterMembers = clusterMemberManager.getClusterMembers();

      final ImmutableMap.Builder<Symbol, ClusterMember> membersMapBuilder = ImmutableMap.builder();
      for (final ClusterMember member : clusterMembers) {
        membersMapBuilder.put(member.getId(), member);
      }
      this.membersMap.putAll(membersMapBuilder.build());

      committeesBuilder.addAll(recursiveClustering(clusterMembers));
      return this;
    }

    public static double getCohesionStd(final ImmutableSet<Cluster> clusters, final double mean) {
      double deviation = 0;
      for(final Cluster c : clusters) {
        deviation += (c.getCohesion() - mean) * (c.getCohesion() - mean);
      }
      return Math.sqrt(deviation/clusters.size());
    }

    public static double getCohesionMean(final ImmutableSet<Cluster> clusters) {
      double cohesion = 0;
      for(final Cluster c : clusters) {
        cohesion += c.getCohesion();
      }
      return cohesion/clusters.size();
    }

    public static ImmutableSet<Cluster> filterUsingCohesionStd(final ImmutableSet<Cluster> clusters) {
      final ImmutableSet.Builder<Cluster> ret = ImmutableSet.builder();

      final double mean = getCohesionMean(clusters);
      final double std = getCohesionStd(clusters, mean);
      final double lowerThreshold = Math.max(mean - std, 0);

      for(final Cluster c : clusters) {
        if(c.getCohesion() >= lowerThreshold) {
          ret.add(c);
        }
      }

      return ret.build();
    }

    public CBC build() {
      //if(filterCommittees) {
      //  return new CBC(filterUsingCohesionStd(committeesBuilder.build()), topSimilarMembersThreshold, committeeThreshold,
      //      residueThreshold, memberSimilarity, weights, metricType, calculateRealCentroid,
      //      committeeSimilarityMethod);
      //} else {
        return new CBC(committeesBuilder.build(), topSimilarMembersThreshold, committeeThreshold,
            residueThreshold, memberSimilarity, weights, metricType, calculateRealCentroid,
            committeeSimilarityMethod);
      //}
    }

    public ImmutableList<Cluster> recursiveClustering(
        final ImmutableCollection<ClusterMember> clusterMembers) {
      log.info("Clustering {} members", clusterMembers.size());

      // these clusters are sorted in descending order of the cohesion
      final ImmutableList<Cluster> maxCohesionClusters =
          computeSortedMostCohesiveClusters(clusterMembers);

      List<Cluster> committees = Lists.newArrayList();
      for (final Cluster cluster : maxCohesionClusters) {
        //log.info("cbc.recursiveClustering, considering cluster: {}:({})", cluster.getCentroid().getId(), StringUtils.SpaceJoiner.join(cluster.getMemberIds()));
        boolean addToCommittee = true;
        for (final Cluster committee : committees) {
          double sim = 0;
          if (calculateRealCentroid) {
            sim = metricType.get().similarity(cluster.getCentroid().getUnNormalizedVector().get(),
                committee.getCentroid().getUnNormalizedVector().get(), weights);
          } else {
            // similarity based on just centriod
            if (cluster.getCentroid().getId().equalTo(committee.getCentroid().getId())) {
              sim = 1.0;
            } else {
              Optional<Double> s = memberSimilarity
                  .getSimilarity(cluster.getCentroid().getId(), committee.getCentroid().getId());
              if(s.isPresent()) {
                sim = s.get();
              } else {
                sim = 0;
              }
            }

            /*
            // average of all pairwise similarity
            int pairCount = 0;
            for(final Symbol id1 : cluster.getMemberIds()) {
              for(final Symbol id2 : committee.getMemberIds()) {
                if(id1.equalTo(id2)) {
                  sim += 1.0;
                  pairCount += 1;
                } else {
                  final Optional<Double> pairSim = memberSimilarity.getSimilarity(id1, id2);
                  if(pairSim.isPresent()) {
                    sim += pairSim.get();
                    pairCount += 1;
                  }
                }
              }
            }
            sim = sim/(double)pairCount;
            */
          }
          if (sim > committeeThreshold) {
            addToCommittee = false;
            break;
          }
        }
        if (addToCommittee) {
          committees.add(Cluster.copyWithId(Symbol.from("c"+clusterIndex), cluster));
          clusterIndex += 1;
        }
      }

      // Step 4. If no committees are added, CBC is done.
      if (committees.size() == 0) {
        return ImmutableList.of();
      } else {
        log.info("Adding {} committees", committees.size());
        //for (final Cluster cluster : committees) {
        //  log.info(" - {}", StringUtils.SpaceJoiner.join(cluster.getMemberIds()));
        //}
      }

      final ImmutableList.Builder<ClusterMember> residuesBuilder = ImmutableList.builder();
      for (final ClusterMember clusterMember : clusterMembers) {
        boolean addToResidue = true;
        for (final Cluster committee : committees) {
          double sim = 0;
          if (calculateRealCentroid) {
            sim = metricType.get().similarity(clusterMember.getUnNormalizedVector().get(),
                committee.getCentroid().getUnNormalizedVector().get(), weights);
          } else {
            // similarity based on just centroid
            if (clusterMember.getId().equalTo(committee.getCentroid().getId())) {
              sim = 1.0;
            } else {
              Optional<Double> s = memberSimilarity
                  .getSimilarity(clusterMember.getId(), committee.getCentroid().getId());
              if(s.isPresent()) {
                sim = s.get();
              } else {
                sim = 0;
              }
            }

            /*
            int pairCount = 0;
            for(final Symbol id : committee.getMemberIds()) {
              if(clusterMember.getId().equalTo(id)) {
                sim += 1.0;
                pairCount += 1;
              } else {
                final Optional<Double> pairSim = memberSimilarity.getSimilarity(id, clusterMember.getId());
                if(pairSim.isPresent()) {
                  sim += pairSim.get();
                  pairCount += 1;
                }
              }
            }
            sim = sim/(double)pairCount;
            */
          }
          if (sim > residueThreshold) {
            addToResidue = false;
            break;
          }
        }
        if (addToResidue) {
          residuesBuilder.add(clusterMember);
        }
      }

      final ImmutableList<ClusterMember> residues = residuesBuilder.build();
      // Step 6. If no residues are found, CBC is done.
      if (residues.size() <= 1) {
        return ImmutableList.copyOf(committees);
      } else {
        final ImmutableList.Builder<Cluster> retBuilder = ImmutableList.builder();
        retBuilder.addAll(committees);

        return retBuilder.addAll(recursiveClustering(residues)).build();
      }
    }

    /*
     * This is steps 1 and 2 of the CBC algorithm. For each member:
     * - we apply HAC clustering on its top similar members
     * - from the resulting HAC clustering, we store the cluster with the highest cohesion
     * - return the clusters, sorted in descending order of cohesion
     */
    private ImmutableList<Cluster> computeSortedMostCohesiveClusters(
        final ImmutableCollection<ClusterMember> clusterMembers) {
      final ImmutableMultimap.Builder<Cluster, Double> cohesiveClustersBuilder =
          ImmutableMultimap.builder();
      for (final ClusterMember member : clusterMembers) {
        final HAC hacResult =
            computeHacOverMostSimilarMembers(member, clusterMembers, topSimilarMembersThreshold);

        final Optional<Cluster> mostCohesiveCluster = hacResult.getClusterWithMaxCohesion();
        if (mostCohesiveCluster.isPresent()) {
          cohesiveClustersBuilder
              .put(mostCohesiveCluster.get(), mostCohesiveCluster.get().getCohesion());
        }
      }

      final ImmutableMultimap<Cluster, Double> cohesiveClusters = cohesiveClustersBuilder.build();

      final ImmutableList.Builder<Cluster> sortedListBuilder = ImmutableList.builder();
      for (final Map.Entry<Cluster, Double> entry : CollectionUtils.entryValueOrdering
          .immutableSortedCopy(cohesiveClusters.entries())) {
        sortedListBuilder.add(entry.getKey());
      }

      return sortedListBuilder.build();
    }

    // the most similar members to 'member' are restricted to the set in similarMemberCandidates
    private HAC computeHacOverMostSimilarMembers(final ClusterMember member,
        final ImmutableCollection<ClusterMember> similarMemberCandidates,
        final int topSimilarMembersThreshold) {
      final Symbol memberId = member.getId();

      final ImmutableSet<Symbol> similarMemberCandidateIds = Sets.difference(
          ImmutableSet.copyOf(Iterables.transform(similarMemberCandidates, ClusterMember.ID)),
          ImmutableSet.of(member.getId()))
          .immutableCopy();

      final ImmutableList<Map.Entry<Symbol, Double>> membersRanked =
          memberSimilarity.getMostSimilarMembers(memberId);

      final ImmutableList.Builder<Map.Entry<Symbol, Double>> membersRankedPrunedBuilder =
          ImmutableList.builder();
      for (final Map.Entry<Symbol, Double> m : membersRanked) {
        if (similarMemberCandidateIds.contains(m.getKey())) {
          membersRankedPrunedBuilder.add(m);
        }
      }
      final ImmutableList<Map.Entry<Symbol, Double>> membersRankedPruned =
          membersRankedPrunedBuilder.build();

      final ImmutableList<Map.Entry<Symbol, Double>> topMostSimilarMembers = membersRankedPruned
          .subList(0, Math.min(topSimilarMembersThreshold, membersRankedPruned.size()));

      final HAC.Builder hacBuilder = HAC.builder().withWeights(weights);
      for (final Map.Entry<Symbol, Double> entry : topMostSimilarMembers) {
        final Symbol id = entry.getKey();
        hacBuilder.withClusterMember(membersMap.get(id));
      }

      return hacBuilder.performClustering(calculateRealCentroid, memberSimilarity).build();
    }


  }

  public enum CommitteeSimilarityMethod {
    CENTROID,
    AVERAGE,
    MAX
  }
}

