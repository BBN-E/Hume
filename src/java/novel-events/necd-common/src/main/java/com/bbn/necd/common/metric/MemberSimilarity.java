package com.bbn.necd.common.metric;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.CollectionUtils;
import com.bbn.necd.common.RealInstanceManager;
import com.bbn.necd.common.metric.SimilarityMetric.MetricType;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.FactoredRealVector;
import com.bbn.necd.common.theory.FactoredRealVectorPair;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Multimap;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.Map;
import java.util.Set;

public final class MemberSimilarity {

  private static final Logger log = LoggerFactory.getLogger(MemberSimilarity.class);

  // member pair similarity
  private final ImmutableTable<Symbol, Symbol, Double> interMemberSimilarity;

  // for each member, a ranked list (in descending order) of most similar other members along with similarity score
  private final ImmutableMap<Symbol, ImmutableList<Map.Entry<Symbol, Double>>>
      mostSimilarMembersSimilarity;


  private MemberSimilarity(final ImmutableTable<Symbol, Symbol, Double> interMemberSimilarity,
      final ImmutableMap<Symbol, ImmutableList<Map.Entry<Symbol, Double>>> mostSimilarMembersSimilarity) {
    this.interMemberSimilarity = interMemberSimilarity;
    this.mostSimilarMembersSimilarity = mostSimilarMembersSimilarity;
  }

  public ImmutableList<String> printMostSimilarMembers() {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    for(final Map.Entry<Symbol, ImmutableList<Map.Entry<Symbol, Double>>> member : mostSimilarMembersSimilarity.entrySet()) {
      final Symbol memberId = member.getKey();
      StringBuilder sb = new StringBuilder(memberId.asString());
      for(final Map.Entry<Symbol, Double> otherMembers : member.getValue()) {
        final Symbol otherId = otherMembers.getKey();
        final double similarity = otherMembers.getValue();
        sb.append(" " + otherId.asString()+":"+String.format("%.2f",similarity));
      }
      ret.add(sb.toString());
    }

    return ret.build();
  }

  public static MemberSimilarity from(final File similarityFile,
      final Optional<ImmutableSet<Symbol>> targetMemberIds,
      final Optional<Multimap<Symbol, Symbol>> lemmaMap) throws IOException {

    final ImmutableTable<Symbol, Symbol, Double> interMemberSimilarity =
        readInterMemberSimilarity(similarityFile, targetMemberIds, lemmaMap);
    log.info("Read interMemberSimilarity");

    final ImmutableMap<Symbol, ImmutableList<Map.Entry<Symbol, Double>>>
        mostSimilarMembersSimilarity = calculateMostSimilarMembers(interMemberSimilarity);
    log.info("calculated most similar members");

    return new MemberSimilarity(interMemberSimilarity, mostSimilarMembersSimilarity);
  }

  public ImmutableList<Map.Entry<Symbol, Double>> getMostSimilarMembers(final Symbol id) {
    if(!mostSimilarMembersSimilarity.containsKey(id)) {
      log.info("cannot find most similar members for {} in {} keys", id.asString(), mostSimilarMembersSimilarity.keySet().size());
      return ImmutableList.<Map.Entry<Symbol, Double>>builder().build();
    }
    return mostSimilarMembersSimilarity.get(id);
  }

  public Optional<Double> getSimilarity(final Symbol id1, final Symbol id2) {
    if (interMemberSimilarity.contains(id1, id2)) {
      return Optional.of(interMemberSimilarity.get(id1, id2));
    } else if (interMemberSimilarity.contains(id2, id1)) {
      return Optional.of(interMemberSimilarity.get(id2, id1));
    } else {
      return Optional.absent();
    }
  }

  // check that member pairs have similarity information
  public boolean hasInterSimilarity(final ImmutableSet<Symbol> members) {
    for (final Symbol m1 : members) {
      for (final Symbol m2 : members) {
        if (!m1.equalTo(m2)) {
          final Optional<Double> sim = getSimilarity(m1, m2);
          if (!sim.isPresent()) {
            log.error("Cannot find similarity info between {} {}", m1.asString(), m2.asString());
            return false;
          }
        }
      }
    }
    return true;
  }

  // ASSUMPTION: RealVectors are not normalized to be unit vectors
  public static ImmutableTable<Symbol, Symbol, Double> calculateInterSimilarity(
      final RealInstanceManager realInstanceManager, final MetricType metric) {
    final ImmutableTable.Builder<Symbol, Symbol, Double> ret = ImmutableTable.builder();

    final double[] weights = realInstanceManager.getWeights();

    //final ImmutableMap<Symbol, RealVector> members = realInstanceManager.getInstances();
    final ImmutableMap<SymbolPair, FactoredRealVectorPair> pairMembers = realInstanceManager.getPairInstances();

    for(final Map.Entry<SymbolPair, FactoredRealVectorPair> entry : pairMembers.entrySet()) {
      final Symbol id1 = entry.getKey().getFirstMember();
      final Symbol id2 = entry.getKey().getSecondMember();
      final FactoredRealVector v1 = entry.getValue().getFirstVector();
      final FactoredRealVector v2 = entry.getValue().getSecondVector();

      final double similarity = metric.similarity(v1, v2, weights);
      ret.put(id1, id2, similarity);
    }

    return ret.build();
  }

  private static ImmutableTable<Symbol, Symbol, Double> readInterMemberSimilarity(
      final File similarityFile,
      final Optional<ImmutableSet<Symbol>> targetMemberIds,
      final Optional<Multimap<Symbol, Symbol>> lemmaMap) throws IOException {
    final ImmutableTable.Builder<Symbol, Symbol, Double> ret = ImmutableTable.builder();

    int lineCount = 0;

    final BufferedReader br = new BufferedReader(new FileReader(similarityFile));
    String line;

    Set<String> readPairs = Sets.newHashSet();

    while((line = br.readLine())!=null) {
      final String[] tokens = line.split(" ");
      final Symbol item1 = Symbol.from(tokens[0]);
      final Symbol item2 = Symbol.from(tokens[1]);
      double score = Double.parseDouble(tokens[2]);

      if(lemmaMap.isPresent()) {
        if(lemmaMap.get().containsKey(item1) && lemmaMap.get().get(item1).equals(item2)) {
          score = 1.0;
        }
      }

      if (!item1.equalTo(item2)) {
        if (!targetMemberIds.isPresent() ||
            (targetMemberIds.isPresent() && targetMemberIds.get().contains(item1) && targetMemberIds
                .get().contains(item2))) {
          if(!readPairs.contains(item1.asString() + "__" + item2.asString()) && !readPairs.contains(item2.asString() + "__" + item1.asString())) {
            ret.put(item1, item2, score);
            ret.put(item2, item1, score);
          }

          readPairs.add(item1.asString() + "__" + item2.asString());
        }
      }

      lineCount += 1;
      if((lineCount % 50000)==0) {
        log.info("lineCount {}", lineCount);
      }
    }

    return ret.build();
  }

  private static ImmutableMap<Symbol, ImmutableList<Map.Entry<Symbol, Double>>> calculateMostSimilarMembers(
      final ImmutableTable<Symbol, Symbol, Double> interMemberSimilarity) {
    final ImmutableMap.Builder<Symbol, ImmutableList<Map.Entry<Symbol, Double>>> ret =
        ImmutableMap.builder();

    int count = 0;
    for (final Symbol item : interMemberSimilarity.rowKeySet()) {
      final ImmutableMap<Symbol, Double> memberSimilarity = interMemberSimilarity.row(item);
      ret.put(item,
          CollectionUtils.entryValueOrdering.immutableSortedCopy(memberSimilarity.entrySet()));

      count += 1;
      if((count % 500)==0) {
        log.info("calculated similar members for {} members", count);
      }
    }

    return ret.build();
  }

}
