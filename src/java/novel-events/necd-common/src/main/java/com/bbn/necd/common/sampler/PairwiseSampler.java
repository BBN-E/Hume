package com.bbn.necd.common.sampler;

import com.bbn.bue.common.collections.ShufflingIterable;
import com.bbn.bue.common.symbols.Symbol;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Sets;
import com.google.common.math.DoubleMath;
import com.google.common.math.LongMath;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.math.RoundingMode;
import java.util.Iterator;
import java.util.Random;
import java.util.Set;

import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Preconditions.checkState;

/**
 * Created by ychan on 1/13/16.
 */
public final class PairwiseSampler {

  private static final Logger log = LoggerFactory.getLogger(PairwiseSampler.class);

  private final ImmutableSet<SymbolPair> intraPairs;
  private final ImmutableSet<SymbolPair> interPairs;

  private PairwiseSampler(final ImmutableSet<SymbolPair> intraPairs,
      final ImmutableSet<SymbolPair> interPairs) {
    this.intraPairs = intraPairs;
    this.interPairs = interPairs;
  }

  public ImmutableSet<SymbolPair> getIntraPairs() {
    return intraPairs;
  }

  public ImmutableSet<SymbolPair> getInterPairs() {
    return interPairs;
  }

  public static Builder builder(final ImmutableSet<SamplerCluster> clusters,
      final long requestedSampleCount, final double intraRatio, final Random rng) {
    return new Builder(clusters, requestedSampleCount, intraRatio, rng);
  }

  public static final class Builder {
    final Random rng;
    final ImmutableSet<SamplerCluster> clusters;
    final ImmutableSet.Builder<SymbolPair> intraPairsBuilder;
    final ImmutableSet.Builder<SymbolPair> interPairsBuilder;
    final long requestedSampleCount;
    final double intraRatio;

    private Builder(final ImmutableSet<SamplerCluster> clusters, final long requestedSampleCount,
        final double intraRatio, final Random rng) {
      this.rng = checkNotNull(rng);
      this.clusters = checkNotNull(clusters);
      this.requestedSampleCount = requestedSampleCount;
      this.intraRatio = intraRatio;
      this.intraPairsBuilder = ImmutableSet.builder();
      this.interPairsBuilder = ImmutableSet.builder();
    }

    public PairwiseSampler build() {
      return new PairwiseSampler(intraPairsBuilder.build(), interPairsBuilder.build());
    }

    public Builder sample() {
      // These are mutable as we need to check for membership as we build them and we do not care about the final value
      final Set<SymbolPair> intraPairsSeen = Sets.newHashSet();
      final Set<SymbolPair> interPairsSeen = Sets.newHashSet();

      final long maxPossibleIntraCount = tabulateIntraCount(clusters);    // max number of positives
      final long maxPossibleInterCount = tabulateInterCount(clusters);    // max number of negatives

      long intraCount = 0;   // the number of intra cluster samples we have thus far
      long interCount = 0;   // the number of inter clusters samples we have thus far

      // Compute requested amounts
      final long requestedIntraCount = DoubleMath.roundToLong(intraRatio * requestedSampleCount, RoundingMode.HALF_UP);
      final long requestedInterCount = requestedSampleCount - requestedIntraCount;

      // Adjust requested amounts based on what is possible
      long targetIntraCount = requestedIntraCount;
      long targetInterCount = requestedInterCount;
      boolean countsChanged = false;
      if (requestedIntraCount > maxPossibleIntraCount) {
        log.warn("{} intracluster samples requested, but only {} possible", requestedIntraCount, maxPossibleIntraCount);
        // Scale down the inter count by the same amount
        final double reductionRate = (double) maxPossibleIntraCount / requestedIntraCount;
        targetIntraCount = maxPossibleIntraCount;
        targetInterCount = DoubleMath.roundToLong(requestedInterCount * reductionRate, RoundingMode.HALF_UP);
        countsChanged = true;

      } else if (requestedInterCount > maxPossibleInterCount) {
        log.warn("{} intercluster samples requested, but only {} possible", targetInterCount, maxPossibleInterCount);
        // Scale down the intra count by the same amount
        final double reductionRate = (double) maxPossibleInterCount / requestedInterCount;
        targetInterCount = maxPossibleInterCount;
        targetIntraCount = DoubleMath.roundToLong(requestedIntraCount * reductionRate, RoundingMode.HALF_UP);
        countsChanged = true;
      }

      // Log the updated counts
      if (countsChanged) {
        log.info("New requested counts: {} intra, {} inter", targetIntraCount, targetInterCount);
      }

      // At this point the target should not be more than what is possible.
      checkState(targetIntraCount <= maxPossibleIntraCount);
      checkState(targetInterCount <= maxPossibleInterCount);

      // If we are requesting all the data in either condition, just dump it in. No sampling will occur for that
      // particular group (inter, intra). Note that because we previously checked, we cannot be asking for more data than
      // there is.
      if (targetIntraCount == maxPossibleIntraCount) {
        intraPairsBuilder.addAll(getIntraPairsFromAllClusters(clusters));
        intraCount = targetIntraCount;
      }
      if (targetInterCount == maxPossibleInterCount) {
        interPairsBuilder.addAll(getInterPairsFromAllClusters(clusters));
        interCount = targetInterCount;
      }

      ImmutableMap.Builder<Symbol, ImmutableList<Symbol>> labelToIdsBuilder = ImmutableMap.builder();
      for (final SamplerCluster c : clusters) {
        labelToIdsBuilder.put(c.getLabel(), ImmutableList.copyOf(c.getIds()));
      }
      final ImmutableMap<Symbol, ImmutableList<Symbol>> labelToIds = labelToIdsBuilder.build();

      int counter = 0;

      while (counter <= MAX_TRIES &&
          ((intraCount < targetIntraCount) || (interCount < targetInterCount))) {
        // Create a random generator for codes
        final ShufflingIterable<Symbol>
            codeShuffler = ShufflingIterable.from(labelToIds.keySet(), rng);

        // Draw two codes that are not the same by shuffling the list and taking the first two.
        final Iterator<Symbol> codeIterator = codeShuffler.iterator();
        final Symbol code1 = codeIterator.next();
        final Symbol code2 = codeIterator.next();

        counter += 1;

        if (intraCount < targetIntraCount) {        // select from code1
          final ImmutableList<Symbol> ids = labelToIds.get(code1);
          final Optional<SymbolPair> pair = getRandomPair(ids, rng, intraPairsSeen);
          if (pair.isPresent()) {
            intraPairsBuilder.add(pair.get());
            intraPairsSeen.add(pair.get());
            intraCount += 1;
            counter = 0;
          }
        }
        if (intraCount < targetIntraCount) {        // select from code2
          final ImmutableList<Symbol> ids = labelToIds.get(code2);
          final Optional<SymbolPair> pair = getRandomPair(ids, rng, intraPairsSeen);
          if (pair.isPresent()) {
            intraPairsBuilder.add(pair.get());
            intraPairsSeen.add(pair.get());
            intraCount += 1;
            counter = 0;
          }
        }

        if (interCount < targetInterCount) {        // select from code1 x code2
          final ImmutableList<Symbol> ids1 = labelToIds.get(code1);
          final ImmutableList<Symbol> ids2 = labelToIds.get(code2);
          final Optional<SymbolPair> pair = getRandomPair(ids1, ids2, rng, interPairsSeen);
          if (pair.isPresent()) {
            interPairsBuilder.add(pair.get());
            interPairsSeen.add(pair.get());
            interCount += 1;
            counter = 0;
          }
        }
        if (interCount < targetInterCount) {        // select from code1 x code2
          final ImmutableList<Symbol> ids1 = labelToIds.get(code1);
          final ImmutableList<Symbol> ids2 = labelToIds.get(code2);
          final Optional<SymbolPair> pair = getRandomPair(ids1, ids2, rng, interPairsSeen);
          if (pair.isPresent()) {
            interPairsBuilder.add(pair.get());
            interPairsSeen.add(pair.get());
            interCount += 1;
            counter = 0;
          }
        }
      }

      boolean error = false;
      if (counter >= MAX_TRIES) {
        log.warn("Sampling stopped after {} attempts to generate a new sample", MAX_TRIES);
        error = true;
      }
      if(intraCount != targetIntraCount) {
        log.warn("{} intracluster samples requested, but only {} returned", targetIntraCount, intraCount);
        error = true;
      }
      if (interCount != targetInterCount) {
        log.warn("{} intercluster samples requested, but only {} returned", targetInterCount, interCount);
        error = true;
      }

      // Give up if there was an error
      if (error) {
        throw new RuntimeException("Sampling failed, see most recently logged errors for cause");
      }

      return this;
    }
  }

  public static ImmutableSet<SymbolPair> getIntraPairsFromAllClusters(
      final ImmutableSet<SamplerCluster> clusters) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    for (final SamplerCluster c : clusters) {
      ret.addAll(getIntraPairs(c));
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> getIntraPairs(final SamplerCluster c) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    final ImmutableList<Symbol> list = ImmutableList.copyOf(c.getIds());

    for (int i = 0; i < (list.size() - 1); i++) {
      for (int j = (i + 1); j < list.size(); j++) {
        ret.add(SymbolPair.from(list.get(i), list.get(j)));
      }
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> getInterPairsFromAllClusters(
      final ImmutableSet<SamplerCluster> clusters) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    final ImmutableList<SamplerCluster> clusterList = ImmutableList.copyOf(clusters);

    for (int i = 0; i < (clusterList.size() - 1); i++) {
      for (int j = (i + 1); j < clusterList.size(); j++) {
        ret.addAll(getInterPairs(clusterList.get(i), clusterList.get(j)));
      }
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> getInterPairs(final SamplerCluster c1,
      final SamplerCluster c2) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    final ImmutableList<Symbol> list1 = ImmutableList.copyOf(c1.getIds());
    final ImmutableList<Symbol> list2 = ImmutableList.copyOf(c2.getIds());

    for (int i = 0; i < list1.size(); i++) {
      for (int j = 0; j < list2.size(); j++) {
        ret.add(SymbolPair.from(list1.get(i), list2.get(j)));
      }
    }

    return ret.build();
  }

  public static long tabulateIntraCount(final ImmutableSet<SamplerCluster> clusters) {
    long ret = 0;

    for (final SamplerCluster cluster : clusters) {
      final int s = cluster.getIds().size();
      ret = LongMath.checkedAdd(ret, (s * (s - 1)) / 2);
    }

    return ret;
  }

  public static long tabulateInterCount(final ImmutableSet<SamplerCluster> clusters) {
    long ret = 0;

    final ImmutableList<Integer> counts = ImmutableList.copyOf(
        Iterables.transform(clusters, SamplerCluster.SIZE));
    for (int i = 0; i < (counts.size() - 1); i++) {
      for (int j = (i + 1); j < counts.size(); j++) {
        ret = LongMath.checkedAdd(ret, counts.get(i) * counts.get(j));
      }
    }

    return ret;
  }

  public static Optional<SymbolPair> getRandomPair(final ImmutableList<Symbol> ids,
      final Random rng, Set<SymbolPair> seen) {

    final Symbol id1 = ids.get(rng.nextInt(ids.size()));
    final Symbol id2 = ids.get(rng.nextInt(ids.size()));
    if (!id1.equalTo(id2)) {
      final SymbolPair idPair = SymbolPair.from(id1, id2);
      if (!seen.contains(idPair)) {
        return Optional.of(idPair);
      }
    }

    return Optional.<SymbolPair>absent();
  }

  public static Optional<SymbolPair> getRandomPair(final ImmutableList<Symbol> ids1,
      final ImmutableList<Symbol> ids2, final Random rng, Set<SymbolPair> seen) {

    final Symbol id1 = ids1.get(rng.nextInt(ids1.size()));
    final Symbol id2 = ids2.get(rng.nextInt(ids2.size()));
    final SymbolPair idPair = SymbolPair.from(id1, id2);
    if (!seen.contains(idPair)) {
      return Optional.of(idPair);
    } else {
      return Optional.<SymbolPair>absent();
    }
  }


  // TODO: Make this configurable
  private static final int MAX_TRIES = 1000;
}
