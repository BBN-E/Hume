package com.bbn.necd.cluster.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.RealVector;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

public final class ClusterMemberManager {

  private static final Logger log = LoggerFactory.getLogger(ClusterMemberManager.class);

  private final ImmutableList<ClusterMember> clusterMembers;
  private final double[] weights;   // could be null

  private ClusterMemberManager(final ImmutableList<ClusterMember> clusterMembers,
      final double[] weights) {
    this.clusterMembers = clusterMembers;
    this.weights = weights;
  }

  public ImmutableList<ClusterMember> getClusterMembers() {
    return clusterMembers;
  }

  public double[] getWeights() {
    return weights;
  }

  public static Builder builder() {
    return new Builder();
  }

  public static final class Builder {

    private final ImmutableList.Builder<ClusterMember> clusterMembersBuilder =
        ImmutableList.builder();
    private double[] weights;

    private Builder() {
      this.weights = null;
    }

    public Builder withClusterMembers(final ImmutableMap<Symbol, RealVector> realVectors) {
      for (final Map.Entry<Symbol, RealVector> entry : realVectors.entrySet()) {
        this.clusterMembersBuilder.add(ClusterMember.from(entry.getKey(), entry.getValue()));
      }
      return this;
    }

    public Builder withClusterMembers(final ImmutableSet<Symbol> ids) {
      for (final Symbol id : ids) {
        this.clusterMembersBuilder.add(ClusterMember.from(id, null));
      }
      return this;
    }

    public Builder withWeights(final double[] weights) {
      this.weights = weights;
      return this;
    }

    public ClusterMemberManager build() {
      return new ClusterMemberManager(clusterMembersBuilder.build(), weights);
    }
  }


}
