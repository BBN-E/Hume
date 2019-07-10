package com.bbn.necd.cluster.common;

import com.bbn.bue.common.primitives.DoubleUtils;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.metric.MemberSimilarity;
import com.bbn.necd.common.theory.WeightedRealVector;

import com.google.common.base.Objects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableListMultimap;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

import static com.google.common.base.Preconditions.checkNotNull;

public final class Cluster {
  private static final Logger log = LoggerFactory.getLogger(Cluster.class);

  private final Symbol id;
  private final ImmutableSet<ClusterMember> members;
  private final ImmutableSet<Symbol> memberIds;
  private final ClusterMember centroid;
  private final ImmutableSet<Cluster> childrenClusters;  // if we are doing HAC
  private final double groupSimilarity; // summation of pairwise similarity between all members in cluster
  private final double averageGroupSimilarity;
  private final double cohesion;

  private Cluster(final Symbol id,
      final ImmutableSet<ClusterMember> members, final ImmutableSet<Symbol> memberIds,
      final ClusterMember centroid,
      final ImmutableSet<Cluster> childrenClusters,
      final double groupSimilarity, final double averageGroupSimilarity, final double cohesion) {
    this.id = id;
    this.members = ImmutableSet.copyOf(members);
    this.memberIds = ImmutableSet.copyOf(memberIds);
    this.centroid = checkNotNull(centroid);
    this.childrenClusters = ImmutableSet.copyOf(childrenClusters);
    this.groupSimilarity = groupSimilarity;
    this.averageGroupSimilarity = averageGroupSimilarity;
    this.cohesion = cohesion;
  }

  public static Cluster copyWithId(final Symbol id, final Cluster c) {
    return new Cluster(id, c.getMembers(), c.getMemberIds(), c.getCentroid(),
        c.getChildrenClusters(), c.getGroupSimilarity(), c.getAverageGroupSimilarity(), c.getCohesion());
  }

  public Symbol getId() {
    return id;
  }

  public ImmutableSet<ClusterMember> getMembers() {
    return members;
  }

  public ImmutableSet<Symbol> getMemberIds() {
    return memberIds;
  }

  public String getMemberIdsAsString() {
    final StringBuilder sb = new StringBuilder();
    for(final Symbol id : memberIds) {
      if(sb.length() > 0) {
        sb.append(" ");
      }
      sb.append(id.asString());
    }
    return sb.toString();
  }

  public ClusterMember getCentroid() {
    return centroid;
  }

  public ImmutableSet<Cluster> getChildrenClusters() {
    return childrenClusters;
  }

  public double getGroupSimilarity() {
    return groupSimilarity;
  }

  public double getAverageGroupSimilarity() {
    return averageGroupSimilarity;
  }

  public double getCohesion() {
    return cohesion;
  }

  public boolean hasMember(final ClusterMember member) {
    return members.contains(member);
  }

  public boolean hasMemberId(final Symbol id) {
    return memberIds.contains(id);
  }

  public int size() {
    return members.size();
  }

  public static ClusterMember calculateCentroid(final ImmutableSet<ClusterMember> members, final double[] weights) {
    final int numberOfMembers = members.size();

    final ImmutableListMultimap.Builder<Integer, Double> elementsBuilder = ImmutableListMultimap.builder();
    for(final ClusterMember member : members) {
      for(final Map.Entry<Integer, Double> entry : member.getUnNormalizedVector().get().getElements().entrySet()) {
        elementsBuilder.put(entry.getKey(), entry.getValue());
      }
    }
    final ImmutableListMultimap<Integer, Double> elements = elementsBuilder.build();

    final ImmutableMap.Builder<Integer, Double> averagedElementsBuilder = ImmutableMap.builder();
    for(final Integer index : elements.keySet()) {
      final double average = DoubleUtils.sum(elements.get(index))/(double)numberOfMembers;
      averagedElementsBuilder.put(index, average);
    }

    final WeightedRealVector v = WeightedRealVector.weightedBuilder(false, weights).withElements(averagedElementsBuilder.build()).build();
    //final RealVector v = RealVector.builder(true).withElements(averagedElementsBuilder.build()).build();
    return ClusterMember.from(CENTROID, v);
  }

  // find the member that is the most similar to all other members.
  // we use this instead of the above method, when we have no representation of the individual members
  public static ClusterMember calculateCentroid(final ImmutableSet<ClusterMember> members, final MemberSimilarity memberSimilarity) {
    ClusterMember ret = null;
    final int numberOfMembers = members.size();

    if(members.size() >= 2) {
      double maxSumSimilarity = 0;
      Symbol centroidCandidate = null;
      final ImmutableList<Symbol>
          ids = ImmutableList.copyOf(Iterables.transform(members, ClusterMember.ID));

      for(final Symbol id : ids) {
        double sumSimilarity = 0;

        for(final Symbol otherId : ids) {
          if(!id.equalTo(otherId)) {
            final Optional<Double> sim = memberSimilarity.getSimilarity(id, otherId);
            if (sim.isPresent()) {
              sumSimilarity += sim.get();
            } else {
              log.error("ERROR: Cluster.calculateCentroid, cannot find similarity between {} {}",
                  id, otherId);
            }
          }
        }

        sumSimilarity = sumSimilarity/(members.size()-1);
        if(sumSimilarity > maxSumSimilarity) {
          maxSumSimilarity = sumSimilarity;
          centroidCandidate = id;
        }
      }

      for(ClusterMember m : members) {
        if(m.getId().equalTo(centroidCandidate)) {
          ret = m;
          break;
        }
      }
    } else if(members.size()==1) {
      ret = members.asList().get(0);
    } else {
      return null;
    }

    return ret;
  }

  // group similarity over this and other
  public double groupSimilarity(final Cluster other, final MemberSimilarity memberSimilarity) {
    double interSimilarity = 0;

    final ImmutableSet<Symbol> otherIds = other.getMemberIds();
    for(final Symbol id : memberIds) {
      for(final Symbol otherId : otherIds) {
        if(!id.equalTo(otherId)) {
          final Optional<Double> sim = memberSimilarity.getSimilarity(id, otherId);
          if (sim.isPresent()) {
            interSimilarity += sim.get();
          } else {
            log.error("ERROR: Cluster.groupSimilarity, cannot find similarity between {} {}", id,
                otherId);
          }
        }
      }
    }

    return (groupSimilarity + other.getGroupSimilarity() + interSimilarity);
  }

  public double similarityWithCluster(final Cluster other, final MemberSimilarity memberSimilarity) {
    double interSimilarity = 0;

    int count = 0;
    final ImmutableSet<Symbol> otherIds = other.getMemberIds();
    for(final Symbol id : memberIds) {
      for(final Symbol otherId : otherIds) {
        if(!id.equalTo(otherId)) {
          final Optional<Double> sim = memberSimilarity.getSimilarity(id, otherId);
          if (sim.isPresent()) {
            interSimilarity += sim.get();
            count += 1;
          } else {
            log.error("ERROR: Cluster.groupSimilarity, cannot find similarity between {} {}", id,
                otherId);
          }
        } else {
          interSimilarity += 1.0;
        }
      }
    }

    return interSimilarity/(double)count;
  }

  // combine this and other to produce a new cluster
  public Cluster combine(final Cluster other, final double similarity, final double averageSimilarity, final double cohesion, final double[] weights,
      final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity, final String id) {
    return Cluster.builder(calculateRealCentroid, memberSimilarity).withWeights(weights).withMembers(this.members).withMembers(other.getMembers())
        .withChildrenCluster(this).withChildrenCluster(other)
        .withGroupSimilarity(similarity)
        .withAverageGroupSimilarity(averageSimilarity)
        .withCohesion(cohesion).withId(Symbol.from(id)).build();
  }

  public static Builder builder(final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity) {
    return new Builder(calculateRealCentroid, memberSimilarity);
  }

  public static class Builder {
    private final ImmutableSet.Builder<ClusterMember> membersBuilder;
    private final ImmutableSet.Builder<Symbol> memberIdsBuilder;
    private final ImmutableSet.Builder<Cluster> childrenClustersBuilder;
    private double groupSimilarity;
    private double averageGroupSimilarity;
    private double cohesion;
    private double[] weights;
    private final MemberSimilarity memberSimilarity;
    private final boolean calculateRealCentroid;
    private Symbol id;

    private Builder(final boolean calculateRealCentroid, final MemberSimilarity memberSimilarity) {
      this.id = DEFAULT_ID;
      this.membersBuilder = ImmutableSet.builder();
      this.memberIdsBuilder = ImmutableSet.builder();
      this.childrenClustersBuilder = ImmutableSet.builder();
      this.groupSimilarity = 0;
      this.averageGroupSimilarity = 0;
      this.cohesion = 0;
      this.weights = null;
      this.memberSimilarity = memberSimilarity;
      this.calculateRealCentroid = calculateRealCentroid;
    }

    public Builder withId(final Symbol id) {
      this.id = id;
      return this;
    }

    public Builder withWeights(final double[] weights) {
      this.weights = weights;
      return this;
    }

    public Builder withMember(final ClusterMember member) {
      checkNotNull(member);
      this.membersBuilder.add(member);
      this.memberIdsBuilder.add(member.getId());
      return this;
    }

    public Builder withMembers(final ImmutableSet<ClusterMember> members) {
      for(final ClusterMember member : members) {
        membersBuilder.add(member);
        memberIdsBuilder.add(member.getId());
      }
      return this;
    }

    public Builder withChildrenCluster(final Cluster child) {
      this.childrenClustersBuilder.add(child);
      return this;
    }

    public Builder withGroupSimilarity(final double similarity) {
      this.groupSimilarity = similarity;
      return this;
    }

    public Builder withAverageGroupSimilarity(final double averageSimilarity) {
      this.averageGroupSimilarity = averageSimilarity;
      return this;
    }

    public Builder withCohesion(final double cohesion) {
      this.cohesion = cohesion;
      return this;
    }

    public ImmutableSet<ClusterMember> getMembers() {
      return membersBuilder.build();
    }

    public Cluster build() {
      final ImmutableSet<ClusterMember> members = this.membersBuilder.build();
      if(members.size() >= 1) {
        ClusterMember centroid = calculateRealCentroid ?
                                       calculateCentroid(members, weights) :
                                       calculateCentroid(members, memberSimilarity);

        // the centroid could be null in the edge case where all members are not similar to each other.
        // In this case, just randomly choose a member as the centroid
        if(centroid==null) {
          centroid = members.asList().get(0);
        }

        return new Cluster(id, members, memberIdsBuilder.build(), centroid,
            childrenClustersBuilder.build(), groupSimilarity, averageGroupSimilarity, cohesion);
      } else {
        return null;
      }
    }
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(members);
  }

  @Override
  public boolean equals(final Object obj) {
    if(this == obj) {
      return true;
    }
    if(obj == null) {
      return false;
    }
    if(getClass() != obj.getClass()) {
      return false;
    }
    final Cluster other = (Cluster) obj;
    return Objects.equal(members, other.members);
  }

  private static final Symbol CENTROID = Symbol.from("centroid");

  public static final Symbol DEFAULT_ID = Symbol.from("c0");
}


