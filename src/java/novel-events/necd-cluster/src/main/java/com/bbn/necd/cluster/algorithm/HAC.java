package com.bbn.necd.cluster.algorithm;

import com.bbn.necd.cluster.common.Cluster;
import com.bbn.necd.cluster.common.ClusterMember;
import com.bbn.necd.common.metric.MemberSimilarity;

import com.google.common.base.Optional;
import com.google.common.collect.*;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.LinkedList;

public final class HAC {
  private static final Logger log = LoggerFactory.getLogger(HAC.class);

  private final Optional<Cluster> rootCluster;

  private HAC(final Cluster rootCluster) {
    this.rootCluster = Optional.fromNullable(rootCluster);
  }

  public static double calculateAverageGroupSimilarity(final Cluster c1, final Cluster c2, final double groupSimilarity) {
    final int c1Size = c1.size();
    final int c2Size = c2.size();
    return calculateAverageGroupSimilarity(c1Size+c2Size, groupSimilarity);
    //return ( ( 1.0/(double) ((c1Size+c2Size)*(c1Size+c2Size-1)) ) * groupSimilarity );
  }

  public static double calculateAverageGroupSimilarity(final int clusterSize, final double groupSimilarity) {
    if (clusterSize == 1) {
      return 1.0;
    }
    return ( ( 1.0/(double) ((clusterSize)*(clusterSize-1)) ) * groupSimilarity );
  }

  public static ImmutableList<Cluster> toSingletonClusters(
      final ImmutableList<ClusterMember> members, final double[] weights,
      final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity) {
    final ImmutableList.Builder<Cluster> ret = ImmutableList.builder();

    for (final ClusterMember member : members) {
      ret.add(Cluster.builder(calculateRealCentroid, memberSimilarity).withWeights(weights).withMember(member).withId(member.getId()).build());
    }

    return ret.build();
  }

  public ImmutableList<Cluster> getAllClusters() {
    final ImmutableList.Builder<Cluster> ret = ImmutableList.builder();

    if(rootCluster.isPresent()) {
      ret.add(rootCluster.get());
      ret.addAll(getAllChildrenClusters(rootCluster.get()));
    }

    return ret.build();
  }

  public ImmutableList<Cluster> getAllChildrenClusters(final Cluster parent) {
    final ImmutableList.Builder<Cluster> ret = ImmutableList.builder();

    for(final Cluster child : parent.getChildrenClusters()) {
      ret.add(child);
      if(child.getChildrenClusters().size() > 0) {
        ret.addAll(getAllChildrenClusters(child));
      }
    }

    return ret.build();
  }

  public ImmutableSet<String> getHACStructure() {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    if(rootCluster.isPresent()) {
//      ret.add(rootCluster.get().getId().asString());
      ret.addAll(getHACSubStructures(rootCluster.get(), "root"));
    }

    return ret.build();
  }

  private ImmutableSet<String> getHACSubStructures(final Cluster parent, String pathSoFar) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for(final Cluster child : parent.getChildrenClusters()) {
      ret.add(pathSoFar + "->" + child.getId().asString());
      if(child.getChildrenClusters().size() > 0) {
//        ret.addAll(getHACSubStructures(child, pathSoFar + "->" + child.getId().asString()));
        ret.addAll(getHACSubStructures(child, child.getId().asString()));
      }
    }

    return ret.build();
  }


  // will be absent if rootCluster is null
  public Optional<Cluster> getClusterWithMaxCohesion() {
    final ImmutableList<Cluster> clusters = getAllClusters();

    double maxCohesion = -1;
    Cluster maxCluster = null;
    for(final Cluster cluster : clusters) {
      final double cohesion = cluster.getCohesion();
      if(cohesion > maxCohesion) {
        maxCohesion = cohesion;
        maxCluster = cluster;
      }
    }

    return Optional.fromNullable(maxCluster);
  }


  public static Builder builder() {
    return new Builder();
  }

  public static class Builder {
    private final ImmutableList.Builder<ClusterMember> membersBuilder;
    private Cluster rootCluster;
    private double[] weights;

    private Builder() {
      this.membersBuilder = ImmutableList.builder();
      this.rootCluster = null;
      this.weights = null;
    }

    public Builder withWeights(final double[] weights) {
      this.weights = weights;
      return this;
    }

    public Builder withClusterMember(final ClusterMember member) {
      membersBuilder.add(member);
      return this;
    }

    public Builder withClusterMembers(final ImmutableList<ClusterMember> members) {
      this.membersBuilder.addAll(members);
      return this;
    }

    public Builder performClustering(final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity) {
      final ImmutableList<Cluster> singletons = toSingletonClusters(membersBuilder.build(), weights, calculateRealCentroid, memberSimilarity); // weights might be null

      //Set<Cluster> currentClusters = Sets.newHashSet(singletons);
      LinkedList<Cluster> currentClusters = new LinkedList<Cluster>(singletons);
      Table<Cluster, Cluster, Double> groupSimilarityCache = HashBasedTable.create();

      if(currentClusters.size() == 1) {
        rootCluster = ImmutableList.copyOf(currentClusters).get(0);
      }

      int clusterIndex = 0;
      while(currentClusters.size() > 1) {
        double maxAverageGroupSimilarity = 0;
        double maxGroupSimilarity = 0;
        double maxCohesion = 0;
        Cluster maxC1 = null;
        Cluster maxC2 = null;

        for(final Cluster c1 : currentClusters) {
          for(final Cluster c2 : currentClusters) {
            if(!c1.equals(c2)) {

              double groupSimilarity = 0;
              if(groupSimilarityCache.contains(c1, c2)) {
                groupSimilarity = groupSimilarityCache.get(c1, c2);
              }
              else if(groupSimilarityCache.contains(c2,  c1)) {
                groupSimilarity = groupSimilarityCache.get(c2, c1);
              }
              else {
                groupSimilarity = c1.groupSimilarity(c2, memberSimilarity);
                groupSimilarityCache.put(c1, c2, groupSimilarity);
              }

              double averageGroupSimilarity = calculateAverageGroupSimilarity(c1, c2, groupSimilarity);

              // NOTE : we should detect and break any ties , but this should rarely happen, so we'll leave this for now
              if(averageGroupSimilarity > maxAverageGroupSimilarity) {
                maxAverageGroupSimilarity = averageGroupSimilarity;
                maxGroupSimilarity = groupSimilarity;
                maxCohesion = Sets.union(c1.getMemberIds(), c2.getMemberIds()).size() * maxAverageGroupSimilarity;
                maxC1 = c1;
                maxC2 = c2;
              }
            }
          }
        }

        if(maxC1!=null && maxC2!=null) {
          final Cluster newCluster = maxC1
              .combine(maxC2, maxGroupSimilarity, maxAverageGroupSimilarity, maxCohesion, weights,
                  calculateRealCentroid, memberSimilarity, "c"+clusterIndex);
          clusterIndex += 1;
          currentClusters.remove(maxC1);
          currentClusters.remove(maxC2);
          currentClusters.add(newCluster);

          rootCluster = newCluster;
        } else {
          break;
        }
      }

      return this;
    }

    public HAC build() {
      return new HAC(rootCluster);
    }

  }
}
