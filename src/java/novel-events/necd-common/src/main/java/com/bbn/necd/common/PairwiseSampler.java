package com.bbn.necd.common;

import com.bbn.bue.common.symbols.Symbol;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/*
 * A generic class for pairwise sampling. The logic here is very simple:
 * - create all possible positive pairs
 * - create all possible negative pairs. Then randomly sample to get a subset.
 */
public final class PairwiseSampler {
  private static final Logger log = LoggerFactory.getLogger(PairwiseSampler.class);

  private final ImmutableSet<ImmutableSet<Symbol>> clusters;
  private final ImmutableSet<SymbolPair> positives;
  private final ImmutableSet<SymbolPair> negatives;

  private PairwiseSampler(final ImmutableSet<ImmutableSet<Symbol>> clusters,
      final ImmutableSet<SymbolPair> positives, final ImmutableSet<SymbolPair> negatives) {
    this.clusters = clusters;
    this.positives = positives;
    this.negatives = negatives;
  }

  public ImmutableSet<ImmutableSet<Symbol>> getClusters() {
    return clusters;
  }

  public ImmutableSet<SymbolPair> getPositives() {
    return positives;
  }

  public ImmutableSet<SymbolPair> getNegatives() {
    return negatives;
  }

  /*
   * The caller would invoke this method with:
   * - a map of instanceId to class label
   * - negativeRatio : if this is 1, we gather as many negative pairs as positive pairs. If this is 2, we gather twice as many negative pairs, and so on.
   */
  public static PairwiseSampler from(final ImmutableMap<Symbol, Symbol> idToLabel, final double negativeRatio) {
    final ImmutableSet<ImmutableSet<Symbol>> clusters = clusterByLabel(idToLabel);

    StringBuffer s = new StringBuffer("");
    for(final ImmutableSet<Symbol> cluster : clusters) {
      s.append(" " + cluster.size());
    }
    log.info("Cluster sizes:{}", s.toString());

    // get positives
    final ImmutableSet.Builder<SymbolPair> positivesBuilder = ImmutableSet.builder();
    for(final ImmutableSet<Symbol> cluster : clusters) {
      positivesBuilder.addAll(getIntraPairs(cluster));
    }
    final ImmutableSet<SymbolPair> positives = positivesBuilder.build();

    // get negatives
    final ImmutableSet.Builder<SymbolPair> negativesBuilder = ImmutableSet.builder();
    final ImmutableList<ImmutableSet<Symbol>> clustersList = ImmutableList.copyOf(clusters);
    for(int i=0; i<(clustersList.size()-1); i++) {
      for(int j=(i+1); j<clustersList.size(); j++) {
        negativesBuilder.addAll(getInterPairs(clustersList.get(i), clustersList.get(j)));
      }
    }
    final ImmutableSet<SymbolPair> negatives = negativesBuilder.build();

    final int N = (int)Math.round((double)positives.size() * negativeRatio);
    final ImmutableSet<SymbolPair> negativeSamples = getRandomSamples(negatives, N);

    log.info("{} positives", positives.size());
    log.info("Sampled {} out of {} negatives", negativeSamples.size(), negatives.size());

    return new PairwiseSampler(clusters, positives, negativeSamples);
  }


  public static ImmutableSet<SymbolPair> getRandomSamples(final ImmutableSet<SymbolPair> instances, final int sampleSize) {
    if(instances.size() <= sampleSize) {
      return instances;
    } else {
      final List<SymbolPair> egs = Lists.newArrayList(instances);
      Collections.shuffle(egs);
      return ImmutableSet.copyOf(egs.subList(0, sampleSize));
    }
  }

  public static ImmutableSet<SymbolPair> getIntraPairs(final ImmutableSet<Symbol> c) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    final ImmutableList<Symbol> list = ImmutableList.copyOf(c);

    for(int i=0; i<(list.size()-1); i++) {
      for(int j=(i+1); j<list.size(); j++) {
        ret.add(SymbolPair.from(list.get(i), list.get(j)));
      }
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> getIntraPairsFromClusters(final ImmutableSet<ImmutableSet<Symbol>> clusters) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    for(final ImmutableSet<Symbol> cluster : clusters) {
      ret.addAll(getIntraPairs(cluster));
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> getInterPairs(final ImmutableSet<Symbol> c1, final ImmutableSet<Symbol> c2) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    final ImmutableList<Symbol> list1 = ImmutableList.copyOf(c1);
    final ImmutableList<Symbol> list2 = ImmutableList.copyOf(c2);

    for(int i=0; i<list1.size(); i++) {
      for(int j=0; j<list2.size(); j++) {
        ret.add(SymbolPair.from(list1.get(i), list2.get(j)));
      }
    }

    return ret.build();
  }

  public static ImmutableSet<ImmutableSet<Symbol>> clusterByLabel(final ImmutableMap<Symbol, Symbol> idToLabel) {
    final ImmutableSet.Builder<ImmutableSet<Symbol>> ret = ImmutableSet.builder();

    final ImmutableMultimap.Builder<Symbol, Symbol> labelToIdBuilder = ImmutableMultimap.builder();
    for(final Map.Entry<Symbol, Symbol> entry : idToLabel.entrySet()) {
      labelToIdBuilder.put(entry.getValue(), entry.getKey());
    }
    final ImmutableMultimap<Symbol, Symbol> labelToId = labelToIdBuilder.build();

    for(final Collection<Symbol> ids : labelToId.asMap().values()) {
      ret.add(ImmutableSet.copyOf(ids));
    }

    return ret.build();
  }

  public static class SymbolPair {
    private final Symbol id1;
    private final Symbol id2;

    private SymbolPair(final Symbol id1, final Symbol id2) {
      this.id1 = id1;
      this.id2 = id2;
    }

    public static SymbolPair from(final Symbol id1, final Symbol id2) {
      return new SymbolPair(id1, id2);
    }

    public Symbol getFirstMember() {
      return id1;
    }

    public Symbol getSecondMember() {
      return id2;
    }

    @Override
    public int hashCode() {
      return Objects.hashCode(id1, id2);
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

      // we assume symmetry, i.e. order does not matter
      final SymbolPair other = (SymbolPair) obj;
      return (Objects.equal(id1, other.id1) && Objects.equal(id2, other.id2)) ||
          (Objects.equal(id1, other.id2) && Objects.equal(id2, other.id1));
    }
  }

}
