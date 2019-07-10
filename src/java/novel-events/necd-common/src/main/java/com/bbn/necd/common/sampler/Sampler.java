package com.bbn.necd.common.sampler;

import com.bbn.bue.common.symbols.Symbol;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 1/12/16.
 */
public final class Sampler {


  // This can be used for diversity of predicates. There are many ways to do this, but here's a very simple and generic approach:
  // We assume the 'examples' are specific to a single event code or class
  // We provide a map of : event-instance-Id -> {list of associated predicates}
  // So long as the {list of associated predicates} is unique, we accept the example. If we've seen it before, we ignore the example.
  // There are many ways to define the {list of associated predicates} for each event instance,
  // e.g. intervening words on proposition connection between Source and Target
  public static ImmutableMap<Symbol, ImmutableList<Symbol>> uniquenessFiltering(
      final ImmutableMap<Symbol, ImmutableList<Symbol>> examples) {
    final ImmutableMap.Builder<Symbol, ImmutableList<Symbol>> ret = ImmutableMap.builder();

    final Set<ImmutableList<Symbol>> seen = Sets.newHashSet();

    for (final Map.Entry<Symbol, ImmutableList<Symbol>> eg : examples.entrySet()) {
      final ImmutableList<Symbol> value = eg.getValue();

      if (!seen.contains(value)) {
        ret.put(eg);
        seen.add(value);
      }
    }

    return ret.build();
  }

  public static ImmutableSet<SamplerCluster> selectDenseClusters(
      final ImmutableSet<SamplerCluster> samplerClusters, final int sampleSize) {
    final ImmutableSet.Builder<SamplerCluster> ret = ImmutableSet.builder();

    for (final SamplerCluster cluster : samplerClusters) {
      if (cluster.getIds().size() >= sampleSize) {
        ret.add(cluster);
      }
    }

    return ret.build();
  }


  // for instance, we want a max number of examples per class
  public static ImmutableSet<SamplerCluster> downSample(
      final ImmutableSet<SamplerCluster> samplerClusters, final int sampleSize) {
    final ImmutableSet.Builder<SamplerCluster> ret = ImmutableSet.builder();

    for (final SamplerCluster cluster : samplerClusters) {
      if (cluster.getIds().size() >= sampleSize) {
        final SamplerCluster.Builder clusterBuilder = SamplerCluster.builder(cluster.getLabel());
        final ImmutableSet<Symbol> sample = getRandomSamples(cluster.getIds(), sampleSize);
        ret.add(clusterBuilder.withIds(sample).build());
      }
    }

    return ret.build();
  }

  // select a random subset according to a given size
  public static ImmutableSet<Symbol> getRandomSamples(final ImmutableSet<Symbol> examples,
      final int sampleSize) {
    if (examples.size() <= sampleSize) {
      return examples;
    } else {
      final List<Symbol> egs = Lists.newArrayList(examples);
      Collections.shuffle(egs);
      return ImmutableSet.copyOf(egs.subList(0, sampleSize));
    }
  }
}
