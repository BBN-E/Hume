package com.bbn.necd.cluster.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.CollectionUtils;
import com.bbn.necd.common.metric.MemberSimilarity;
import com.bbn.necd.common.sampler.PairwiseSampler;
import com.bbn.necd.common.sampler.SamplerCluster;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.event.formatter.EventFeatureFormatter;
import com.bbn.necd.event.io.LabelWriter;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Created by ychan on 2/25/16.
 */
public final class TabulateClusterMistakes {
  private static final Logger log = LoggerFactory.getLogger(TabulateClusterMistakes.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final ClusterMistakePhase mistakePhase = params.getEnum("clusterMistake.phase", ClusterMistakePhase.class);

    switch (mistakePhase) {
      case FIND_MISTAKES:
        findClusteringMistakes(params);
        break;
      //case ORDER_MISTAKES:
      //  orderMistakesByConfidence(params);
      //  break;
      default:
        throw new IllegalArgumentException("Unhandled cluster mistake phase");
    }


  }

  private static void findClusteringMistakes(final Parameters params) throws IOException {
    final ImmutableMap<Symbol, Symbol> memberIdToLabel = RunCBC.readMemberLabel(params.getExistingFile("targetMembers.label"));

    final ImmutableSet<SamplerCluster> clusters = readClusters(params.getExistingFile("cluster.input"), params.getBoolean("cluster.isCommittee"));

    final ImmutableSet<SymbolPair> allIntraPairs = PairwiseSampler.getIntraPairsFromAllClusters(clusters);
    final ImmutableSet<SymbolPair> allInterPairs = PairwiseSampler.getInterPairsFromAllClusters(clusters);

    // remove pairs that are both intra and inter (this can occur if an id is in more than one cluster
    final ImmutableSet<SymbolPair> confusablePairs = Sets.intersection(allIntraPairs, allInterPairs).immutableCopy();
    final ImmutableSet<SymbolPair> intraPairs = Sets.difference(allIntraPairs, confusablePairs).immutableCopy();
    final ImmutableSet<SymbolPair> interPairs = Sets.difference(allInterPairs, confusablePairs).immutableCopy();

    log.info("allIntraPairs.size={} , allInterPairs.size={} , confusablePairs.size={}", allIntraPairs.size(), allInterPairs.size(), confusablePairs.size());

    //final ImmutableSet.Builder<SymbolPair> intraMistakesBuilder = ImmutableSet.builder();
    List<SymbolPair> interMistakes = Lists.newArrayList();  // rightfully is negative, but I predict positive
    for(final SymbolPair pair : intraPairs) {
      if(!memberIdToLabel.containsKey(pair.getFirstMember())) {
        log.info("Cannot find label for {}", pair.getFirstMember());
      }
      if(!memberIdToLabel.containsKey(pair.getSecondMember())) {
        log.info("Cannot find label for {}", pair.getSecondMember());
      }
      if(memberIdToLabel.containsKey(pair.getFirstMember()) && memberIdToLabel.containsKey(pair.getSecondMember())) {
        final int y = memberIdToLabel.get(pair.getFirstMember())
                          .equalTo(memberIdToLabel.get(pair.getSecondMember())) ? 1 : 0;
        if (y == 0) {
          interMistakes.add(pair);
        }
      }
    }
    //final ImmutableSet<SymbolPair> intraMistakes = intraMistakesBuilder.build();

    //final ImmutableSet.Builder<SymbolPair> interMistakesBuilder = ImmutableSet.builder();
    List<SymbolPair> intraMistakes = Lists.newArrayList();  // rightfully is positive, but I predict negative
    for(final SymbolPair pair : interPairs) {
      if(!memberIdToLabel.containsKey(pair.getFirstMember())) {
        log.info("Cannot find label for {}", pair.getFirstMember());
      }
      if(!memberIdToLabel.containsKey(pair.getSecondMember())) {
        log.info("Cannot find label for {}", pair.getSecondMember());
      }
      if(memberIdToLabel.containsKey(pair.getFirstMember()) && memberIdToLabel.containsKey(pair.getSecondMember())) {
        final int y = memberIdToLabel.get(pair.getFirstMember())
                          .equalTo(memberIdToLabel.get(pair.getSecondMember())) ? 1 : 0;
        if (y == 1) {
          intraMistakes.add(pair);
        }
      }
    }
    //final ImmutableSet<SymbolPair> interMistakes = interMistakesBuilder.build();

    log.info("intraMistakes.size={} , interMistakes.size={}", intraMistakes.size(), interMistakes.size());

    final double positiveRatio = params.getDouble("positiveRatio");
    final double negativeRatio = params.getDouble("negativeRatio");
    final int maxNumberOfMistakes = params.getInteger("cluster.maxNumberOfMistakes");

    int possiblePositiveSize = 0;
    int possibleNegativeSize = 0;
    if( (intraMistakes.size()*(negativeRatio*10)) <= interMistakes.size() ) {
      possiblePositiveSize = intraMistakes.size();
      possibleNegativeSize = (int)(intraMistakes.size()*(negativeRatio*10));
    } else {
      possiblePositiveSize = (int)(interMistakes.size()/(negativeRatio*10));
      possibleNegativeSize = interMistakes.size();
    }
    final int positiveSize = Math.min((int)Math.round(positiveRatio*maxNumberOfMistakes), possiblePositiveSize);
    final int negativeSize = Math.min((int)Math.round(negativeRatio*maxNumberOfMistakes), possibleNegativeSize);

    log.info("possiblePositiveSize={} , possibleNegativeSize={}", possiblePositiveSize, possibleNegativeSize);
    log.info("positiveSize={} , negativeSize={}", positiveSize, negativeSize);

    final Random rng = new Random(params.getInteger("randomSeed"));
    Collections.shuffle(intraMistakes, rng);
    Collections.shuffle(interMistakes, rng);

    final ImmutableSet<SymbolPair> positives = ImmutableSet.copyOf(intraMistakes.subList(0, positiveSize));
    final ImmutableSet<SymbolPair> negatives = ImmutableSet.copyOf(interMistakes.subList(0, negativeSize));

    //writePairsToFile(positives, params.getCreatableFile("cluster.sampled.positive"));
    //writePairsToFile(negatives, params.getCreatableFile("cluster.sampled.negative"));

    //final ImmutableSet<SymbolPair> idPairs = Sets.union(positives, negatives).immutableCopy();
    //writePairsToFile(idPairs, params.getCreatableFile("memberPair.list"));
    //writeSinglesToFile(pairsToSingles(idPairs), params.getCreatableFile("targetMembers"));


    final File pairLabelsTable = params.getExistingFile("pairLabelsTable.input");
    final ImmutableMap<String, String> instanceLabels = EventFeatureFormatter.readPairLabels(pairLabelsTable);

    final LabelWriter labelWriter = LabelWriter.create(params.getCreatableFile("pairLabelsTable.output"));
    // first, write out the pairLabelsTable.input
    final CSVParser parser = LabelWriter.getParser(pairLabelsTable);
    for (CSVRecord row : parser) {
      labelWriter
          .writeIdPair(Symbol.from(row.get(0)), Symbol.from(row.get(1)), Symbol.from(row.get(2)),
              Symbol.from(row.get(3)));
    }
    for(final SymbolPair pair : positives) {
      final Symbol id1 = pair.getFirstMember();
      final Symbol id2 = pair.getSecondMember();
      final Symbol code1 = Symbol.from(instanceLabels.get(pair.getFirstMember().asString()));
      final Symbol code2 = Symbol.from(instanceLabels.get(pair.getSecondMember().asString()));
      labelWriter.writeIdPair(id1, id2, code1, code2);
    }
    for(final SymbolPair pair : negatives) {
      final Symbol id1 = pair.getFirstMember();
      final Symbol id2 = pair.getSecondMember();
      final Symbol code1 = Symbol.from(instanceLabels.get(pair.getFirstMember().asString()));
      final Symbol code2 = Symbol.from(instanceLabels.get(pair.getSecondMember().asString()));
      labelWriter.writeIdPair(id1, id2, code1, code2);
    }
    labelWriter.close();

    /*
    final MemberSimilarity memberSimilarity = MemberSimilarity
        .from(params.getExistingFile("interMemberSimilarity"),
            Optional.<ImmutableSet<Symbol>>absent());
    log.info("Read member similarity");

    final ImmutableList<Map.Entry<SymbolPair, Double>> mistakeScores = toMistakeScores(intraMistakes, interMistakes, memberSimilarity, params.getInteger("cluster.maxNumberOfMistakes"));
    writeMistakePairsToFile(mistakeScores, params.getCreatableFile("memberPair.list"));
    writeMistakeSinglesToFile(mistakeScores, params.getCreatableFile("targetMembers"));
    logMistakesToFile(mistakeScores, params.getCreatableFile("memberPair.mistakeScores"));
    */




  }

  private static void logMistakesToFile(final ImmutableList<Map.Entry<SymbolPair, Double>> mistakeScores, final File outfile) throws IOException {
    final List<String> lines = Lists.newArrayList();
    for(final Map.Entry<SymbolPair, Double> entry : mistakeScores) {
      lines.add(entry.getKey().getFirstMember().asString() + "\t" + entry.getKey().getSecondMember().asString() + "\t" + entry.getValue().toString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines);
  }

  private static void writeMistakeSinglesToFile(final ImmutableList<Map.Entry<SymbolPair, Double>> mistakeScores, final File outfile) throws IOException {
    final ImmutableSet.Builder<Symbol> idsBuilder = ImmutableSet.builder();
    for(final Map.Entry<SymbolPair, Double> entry : mistakeScores) {
      idsBuilder.add(entry.getKey().getFirstMember());
      idsBuilder.add(entry.getKey().getSecondMember());
    }

    writeSinglesToFile(idsBuilder.build(), outfile);
  }

  private static void writeMistakePairsToFile(final ImmutableList<Map.Entry<SymbolPair, Double>> mistakeScores, final File outfile) throws IOException {
    final List<String> lines = Lists.newArrayList();
    for(final Map.Entry<SymbolPair, Double> entry : mistakeScores) {
      lines.add(entry.getKey().getFirstMember().asString() + "\t" + entry.getKey().getSecondMember().asString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines);
  }

  private static ImmutableList<Map.Entry<SymbolPair, Double>> toMistakeScores(final ImmutableSet<SymbolPair> intraMistakes, final ImmutableSet<SymbolPair> interMistakes, final MemberSimilarity memberSimilarity, final int maxSize) {
    final ImmutableMap.Builder<SymbolPair, Double> mistakeScoresBuilder = ImmutableMap.builder();

    for(final SymbolPair pair : intraMistakes) {  // hx=1, y=0
      Optional<Double> s = memberSimilarity.getSimilarity(pair.getFirstMember(), pair.getSecondMember());
      double sim = 0;
      if(s.isPresent()) {
        sim = s.get();
      }
      if(0<=sim && sim<=1) {
        mistakeScoresBuilder.put(pair, sim);
      }
    }

    for(final SymbolPair pair : interMistakes) {  // hx=0, y=1
      Optional<Double> s = memberSimilarity.getSimilarity(pair.getFirstMember(), pair.getSecondMember());
      double sim = 0;
      if(s.isPresent()) {
        sim = s.get();
      }
      if(0<=sim && sim<=1) {
        mistakeScoresBuilder.put(pair, (1.0-sim));
      }
    }

    final ImmutableMap<SymbolPair, Double> mistakeScores = mistakeScoresBuilder.build();

    return CollectionUtils.entryValueOrdering.immutableSortedCopy(mistakeScores.entrySet()).subList(0,
        Math.min(maxSize, mistakeScores.size()));
  }

  /*
  private static void orderMistakesByConfidence(final Parameters params) throws IOException {
    final RealInstanceManager realInstanceManager = RealInstanceManager.from(params);

    final SimilarityMetric.MetricType
        metricType = params.getEnum("metricType", SimilarityMetric.MetricType.class);

    final ImmutableTable<Symbol, Symbol, Double> memberSimilarity = MemberSimilarity.calculateInterSimilarity(
        realInstanceManager, metricType);
  }
  */

  private static ImmutableSet<SamplerCluster> readClusters(final File clusterFile, final boolean isCommitteeCluster) throws IOException {
    final ImmutableSet.Builder<SamplerCluster> ret = ImmutableSet.builder();

    final ImmutableList<String> lines = Files.asCharSource(clusterFile, Charsets.UTF_8).readLines();

    for(int i=0; i<lines.size(); i++) {
      final SamplerCluster.Builder clusterBuilder = SamplerCluster.builder(Symbol.from(String.valueOf(i)));

      //if(isCommitteeCluster) {
        final String[] tokens = lines.get(i).split(" ");
        final ImmutableSet.Builder<Symbol> idsBuilder = ImmutableSet.builder();
        for(int j=1; j<tokens.length; j++) {
          idsBuilder.add(Symbol.from(tokens[j]));
        }
        ret.add(clusterBuilder.withIds(idsBuilder.build()).build());
      //} else {
      //  ret.add(clusterBuilder.withIds(SymbolUtils.setFrom(lines.get(i).split(" "))).build());
      //}
    }

    return ret.build();
  }

  private static void writeSinglesToFile(final ImmutableSet<Symbol> ids, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    for(final Symbol id : ids) {
      lines.add(id.asString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static void writePairsToFile(final ImmutableList<SymbolPair> pairs, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    for(final SymbolPair pair : pairs) {
      lines.add(pair.getFirstMember().asString() + "\t" + pair.getSecondMember().asString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static void writePairsToFile(final ImmutableSet<SymbolPair> pairs, final File outfile) throws IOException {
    final ImmutableList.Builder<String> lines = ImmutableList.builder();

    for(final SymbolPair pair : pairs) {
      lines.add(pair.getFirstMember().asString() + "\t" + pair.getSecondMember().asString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(lines.build());
  }

  private static ImmutableSet<Symbol> pairsToSingles(final ImmutableSet<SymbolPair> pairs) {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();
    for(final SymbolPair pair : pairs) {
      ret.add(pair.getFirstMember());
      ret.add(pair.getSecondMember());
    }
    return ret.build();
  }

  public enum ClusterMistakePhase {
    FIND_MISTAKES,
    ORDER_MISTAKES
  }
}
