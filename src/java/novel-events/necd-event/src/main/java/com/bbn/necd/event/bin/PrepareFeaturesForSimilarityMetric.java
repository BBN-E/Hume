package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.event.formatter.EventFeatureFormatter;
import com.bbn.necd.event.formatter.FeatureType;
import com.bbn.necd.event.formatter.InstanceFeatures;
import com.bbn.necd.event.formatter.LearningFeatureFormatter;
import com.bbn.necd.event.formatter.StringPair;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.base.Predicates;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multiset;
import com.google.common.io.Files;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Created by ychan on 2/20/16.
 */
public final class PrepareFeaturesForSimilarityMetric {
  private static final Logger log = LoggerFactory.getLogger(PrepareFeaturesForSimilarityMetric.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final PreparationPhase preparationPhase = params.getEnum("feature.preparationPhase", PreparationPhase.class);

    switch(preparationPhase) {
      case TRAIN:
        prepareFeaturesTrain(params);
        break;
      case PRE_TEST:
        prepareFeaturesPreTest(params);
        break;
      case TEST:
        prepareFeaturesTest(params);
        break;
      case SAMPLE_TRAIN:
        sampleTrain(params);
        break;
      default:
        throw new IllegalArgumentException("Unhandled feature preparation phase");
    }


  }

  private static void sampleTrain(final Parameters params) throws IOException {
    final Random rng = new Random(params.getInteger("randomSeed"));
    final int sampleSize = params.getInteger("sampleSize");

    // instanceid -> event label
    final ImmutableMap<String, String> instanceLabels = EventFeatureFormatter.readPairLabels(params.getExistingFile("pairLabelsTable"));

    List<String> ids = Lists.newArrayList(instanceLabels.keySet());
    Collections.shuffle(ids, rng);
    final ImmutableSet<String> sampledIds = ImmutableSet.copyOf(ids.subList(0, Math.min(ids.size(), sampleSize)));

    EventFeatureFormatter.filterInstanceFeatures(params.getExistingFile("eventFeaturesTable.input"), params.getCreatableFile("eventFeaturesTable.output"), sampledIds);
    EventFeatureFormatter.writeIdLabel(params.getCreatableFile("labelsTable"), Maps.filterKeys(instanceLabels, Predicates.in(sampledIds)));


  }

  private static void prepareFeaturesTest(final Parameters params) throws IOException {
    log.info("reading predict vectors");
    final PredictVectorManager predictVectorManager =
        PredictVectorManager.fromParams(params).build();

    final ImmutableMap<String, InstanceFeatures> instances =
        prepareInstances(params, predictVectorManager);

    final ImmutableSet<StringPair> idPairs = readIdPairs(params.getExistingFile("idPairs"));
    final ImmutableSet<String> ids = toSingleStrings(idPairs);

    final File labelsTable = params.getExistingFile("labelsTable");
    // instanceid -> event label
    final ImmutableMap<String, String> instanceLabels =
        ImmutableMap.copyOf(Maps.filterKeys(EventFeatureFormatter.readLabels(labelsTable), Predicates.in(ids)));

    log.info("calculating max sim words");
    calculateMaxSimWords(predictVectorManager, instances, idPairs, params.getCreatableFile("pair.maxSimWords"));

    log.info("generating sector singles");
    generateSectorSingles(instances, ids, params.getCreatableFile("single.sector"));

    log.info("generating sector pairs");
    generateSectorPairs(instances, idPairs, params.getCreatableFile("pair.sector"), params.getInteger("feature.sparsityThreshold"));

    LearningFeatureFormatter.writeInstancePairLabels(idPairs, instanceLabels, params.getCreatableFile("memberPair.label"));
    LearningFeatureFormatter.writeInstancePairIds(idPairs, params.getCreatableFile("memberPair.list"));

    LearningFeatureFormatter.writeInstanceLabels(ids, instanceLabels, params.getCreatableFile("targetMembers.label"));
    LearningFeatureFormatter.writeInstanceIds(ids, params.getCreatableFile("targetMembers"));

  }

  private static void prepareFeaturesPreTest(final Parameters params) throws IOException {
    log.info("reading predict vectors");
    final PredictVectorManager predictVectorManager =
        PredictVectorManager.fromParams(params).build();

    final ImmutableMap<String, InstanceFeatures> instances =
        prepareInstances(params, predictVectorManager);

    log.info("writing embeddings");
    writeEmbeddings(predictVectorManager, instances, params.getCreatableFile("predictVector"));

    final File outDir = params.getExistingFileOrDirectory("feature.outputDir");

    log.info("preparing id pairs");
    final int numberOfSets = params.getInteger("feature.numberOfSets");
    final ImmutableList<String> ids = instances.keySet().asList();
    final int sizePerSet =
        (int) Math.round( ((((float)ids.size()*(ids.size()-1) )/2 )/numberOfSets) +0.5 );

    int setCounter = 1;
    List<String> idPairs = Lists.newArrayList();
    for(int i=0; i<ids.size()-1; i++) {
      for(int j=(i+1); j<ids.size(); j++) {
        final StringPair idPair = StringPair.from(ids.get(i), ids.get(j));
        idPairs.add(idPair.getFirstString() + " " + idPair.getSecondString());

        if(idPairs.size() >= sizePerSet) {  // dump to file
          final File outfile = new File(outDir, "set"+setCounter+".idpair");
          Files.asCharSink(outfile, Charsets.UTF_8).writeLines(idPairs);
          setCounter += 1;
          idPairs.clear();
        }
      }
    }

    final File outfile = new File(outDir, "set"+setCounter+".idpair");
    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(idPairs);
  }

  private static void prepareFeaturesTrain(final Parameters params) throws IOException {
    log.info("reading predict vectors");
    final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();

    final ImmutableMap<String, InstanceFeatures> instances = prepareInstances(params, predictVectorManager);

    log.info("writing embeddings");
    writeEmbeddings(predictVectorManager, instances, params.getCreatableFile("predictVector"));



    final File pairLabelsTable = params.getExistingFile("pairLabelsTable");

    final ImmutableSet<StringPair> idPairs = filterPairBySingle(
        EventFeatureFormatter.readIdPairs(pairLabelsTable), instances.keySet());
    final ImmutableSet<String> ids = toSingleStrings(idPairs);

    // instanceid -> event label
    final ImmutableMap<String, String> instanceLabels =
        ImmutableMap.copyOf(Maps.filterKeys(EventFeatureFormatter.readPairLabels(pairLabelsTable), Predicates.in(ids)));

    log.info("calculating max sim words");
    calculateMaxSimWords(predictVectorManager, instances, idPairs, params.getCreatableFile("pair.maxSimWords"));

    log.info("generating sector singles");
    generateSectorSingles(instances, ids, params.getCreatableFile("single.sector"));

    log.info("generating sector pairs");
    generateSectorPairs(instances, idPairs, params.getCreatableFile("pair.sector"), params.getInteger("feature.sparsityThreshold"));

    LearningFeatureFormatter.writeInstancePairLabels(idPairs, instanceLabels, params.getCreatableFile("memberPair.label"));
    LearningFeatureFormatter.writeInstancePairIds(idPairs, params.getCreatableFile("memberPair.list"));

    LearningFeatureFormatter.writeInstanceLabels(ids, instanceLabels, params.getCreatableFile("targetMembers.label"));
    LearningFeatureFormatter.writeInstanceIds(ids, params.getCreatableFile("targetMembers"));
  }

  // Read in event instances where:
  // - mandatory feature types exist
  // - at least 1 predicate word with embeddings information
  private static ImmutableMap<String, InstanceFeatures> prepareInstances(final Parameters params,
      final PredictVectorManager predictVectorManager) throws IOException {

    final ImmutableSet<String> mandatoryFeatureTypes =
        ImmutableSet.copyOf(params.getStringList("feature.single.targetTypes"));

    final File eventFeaturesTable = params.getExistingFile("eventFeaturesTable");

    log.info("reading event features table");
    final ImmutableMap<String, InstanceFeatures> instances = getInstancesWithEmbeddings(
        filterForFeatureTypes(EventFeatureFormatter.readInstanceFeatures(eventFeaturesTable),
            mandatoryFeatureTypes), predictVectorManager);

    return instances;
  }

  private static void writeEmbeddings(final PredictVectorManager predictVectorManager,
      final ImmutableMap<String, InstanceFeatures> instances,
      final File outfile) throws IOException {
    final ImmutableList.Builder<String> outlines = ImmutableList.builder();

    final ImmutableSet<String> predicates = getPredicates(instances.values());
    for(final String predicate : predicates) {
      final Optional<PredictVectorManager.PredictVector> v = predictVectorManager.getVector(Symbol.from(predicate));
      if(v.isPresent()) {
        outlines.add(v.get().toString());
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outlines.build());
  }


  private static void generateSectorSingles(final ImmutableMap<String, InstanceFeatures> instances,
      final ImmutableSet<String> ids, final File outfile) throws IOException {
    final ImmutableList.Builder<String> outlines = ImmutableList.builder();

    for(final String id : ids) {
      final Optional<FeatureType> source = instances.get(id).getFeatureType("SourceSectors");
      if(source.isPresent()) {
        for(final String value : source.get().getValues()) {
          outlines.add(id + "\t" + "SourceSector:" + value.replaceAll(" ", "_") + "\t1.0");
        }
      }
      final Optional<FeatureType> target = instances.get(id).getFeatureType("TargetSectors");
      if(target.isPresent()) {
        for(final String value : target.get().getValues()) {
          outlines.add(id + "\t" + "TargetSector:" + value.replaceAll(" ", "_") + "\t1.0");
        }
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outlines.build());
  }

  private static void generateSectorPairs(final ImmutableMap<String, InstanceFeatures> instances,
      final ImmutableSet<StringPair> idPairs, final File outfile, final int countThreshold) throws IOException {
    final ImmutableList.Builder<String> outlines = ImmutableList.builder();

    final Multiset<StringPair> sourceSectors = HashMultiset.create();
    final Multiset<StringPair> targetSectors = HashMultiset.create();
    final ImmutableMultimap.Builder<StringPair, StringPair> sourceFeaturesBuilder = ImmutableMultimap.builder();
    final ImmutableMultimap.Builder<StringPair, StringPair> targetFeaturesBuilder = ImmutableMultimap.builder();
    for(final StringPair idPair : idPairs) {
      final String id1 = idPair.getFirstString();
      final String id2 = idPair.getSecondString();

      final Optional<FeatureType> source1 = instances.get(id1).getFeatureType("SourceSectors");
      final Optional<FeatureType> source2 = instances.get(id2).getFeatureType("SourceSectors");
      if(source1.isPresent() && source2.isPresent()) {
        for(final StringPair pair : InstanceFeatures.crossAllFeatureValues(source1.get(), source2.get())) {
          sourceFeaturesBuilder.put(idPair, pair);
          sourceSectors.add(pair);
        }
      }

      final Optional<FeatureType> target1 = instances.get(id1).getFeatureType("TargetSectors");
      final Optional<FeatureType> target2 = instances.get(id2).getFeatureType("TargetSectors");
      if(target1.isPresent() && target2.isPresent()) {
        for(final StringPair pair : InstanceFeatures.crossAllFeatureValues(target1.get(), target2.get())) {
          targetFeaturesBuilder.put(idPair, pair);
          targetSectors.add(pair);
        }
      }
    }
    final ImmutableMultimap<StringPair, StringPair> sourceFeatures = sourceFeaturesBuilder.build();
    final ImmutableMultimap<StringPair, StringPair> targetFeatures = targetFeaturesBuilder.build();

    for(final StringPair idPair : idPairs) {
      for(final StringPair sectorPair : sourceFeatures.get(idPair)) {
        if(sourceSectors.count(sectorPair) >= countThreshold) {
          StringBuilder sb = new StringBuilder();
          sb.append(idPair.getFirstString() + "\t" + idPair.getSecondString() + "\t");
          sb.append("SourceSector:" + sectorPair.getFirstString().replaceAll(" ", "_") + ":" + sectorPair.getSecondString().replaceAll(" ", "_"));
          sb.append("\t" + "1.0");
          outlines.add(sb.toString());
        }
      }
      for(final StringPair sectorPair : targetFeatures.get(idPair)) {
        if(targetSectors.count(sectorPair) >= countThreshold) {
          StringBuilder sb = new StringBuilder();
          sb.append(idPair.getFirstString() + "\t" + idPair.getSecondString() + "\t");
          sb.append("TargetSector:" + sectorPair.getFirstString().replaceAll(" ", "_") + ":" + sectorPair.getSecondString().replaceAll(" ", "_"));
          sb.append("\t" + "1.0");
          outlines.add(sb.toString());
        }
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outlines.build());
  }

  private static ImmutableMap<String, InstanceFeatures> getInstancesWithEmbeddings(final ImmutableMap<String, InstanceFeatures> instances, final PredictVectorManager predictVectorManager) {
    final ImmutableMap.Builder<String, InstanceFeatures> ret = ImmutableMap.builder();

    for(final Map.Entry<String, InstanceFeatures> entry : instances.entrySet()) {
      final String id = entry.getKey();
      final InstanceFeatures instance = entry.getValue();

      final ImmutableSet<String> predicates = getPredicates(instance);
      for(final String predicate : predicates) {
        if(predictVectorManager.getVector(Symbol.from(predicate)).isPresent()) {
          ret.put(id, instance);
          break;
        }
      }
    }

    return ret.build();
  }

  private static void calculateMaxSimWords(final PredictVectorManager predictVectorManager,
      final ImmutableMap<String, InstanceFeatures> instances,
      final ImmutableSet<StringPair> idPairs, final File outfile) throws IOException {

    final ImmutableList.Builder<String> outlines = ImmutableList.builder();

    final ImmutableSet<String> predicates = getPredicates(instances.values());

    final ImmutableMap.Builder<String, RealVector> predicateToRealVectorBuilder = ImmutableMap.builder();
    for(final String predicate : predicates) {
      final Optional<PredictVectorManager.PredictVector> predictVector = predictVectorManager.getVector(Symbol.from(predicate));
      if(predictVector.isPresent()) {
        final RealVector rv = RealVector.toRealVector(predictVector.get().getValues());
        predicateToRealVectorBuilder.put(predicate, rv);
      }
    }
    final ImmutableMap<String, RealVector> predicateToRealVector = predicateToRealVectorBuilder.build();

    // similarity between words
    Map<StringPair, Double> simCache = Maps.newHashMap();
    for(final StringPair idPair : idPairs) {
      final String id1 = idPair.getFirstString();
      final String id2 = idPair.getSecondString();

      final ImmutableSet<String> words1 = getAllPredicateWords(instances.get(id1));
      final ImmutableSet<String> words2 = getAllPredicateWords(instances.get(id2));
      double maxSim = 0;
      String maxWord1 = "";
      String maxWord2 = "";
      for(final String w1 : words1) {
        for(final String w2 : words2) {
          if(predicateToRealVector.containsKey(w1) && predicateToRealVector.containsKey(w2)) {
            double sim = 0;
            if(w1.equals(w2)) {
              sim = 1.0;
            } else {
              final StringPair wordPair = StringPair.from(w1, w2);
              if(simCache.containsKey(wordPair)) {
                sim = simCache.get(wordPair);
              } else {
                sim = CosineSimilarity.similarity(predicateToRealVector.get(w1), predicateToRealVector.get(w2));
                simCache.put(wordPair, sim);
              }
            }
            if(sim > maxSim) {
              maxSim = sim;
              maxWord1 = w1;
              maxWord2 = w2;
            }
          }
        }
      }

      if(maxSim > 0) {
        StringBuilder sb = new StringBuilder();
        sb.append(id1 + "\t" + id2 + "\t");
        sb.append(maxWord1 + "\t" + maxWord2);
        sb.append("\t" + String.valueOf(maxSim));
        outlines.add(sb.toString());
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outlines.build());
  }

  private static ImmutableSet<String> getAllPredicateWords(final InstanceFeatures instance) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for(final ImmutableSet<String> words : Iterables.transform(instance.getFeatureTypesStartingWithPrefix(PREDICATE_WORD_PREFIX), FeatureType.VALUES)) {
      ret.addAll(words);
    }

    return ret.build();
  }

  private static ImmutableSet<String> getPredicates(final InstanceFeatures instance) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for (final FeatureType featureType : instance.getFeatureTypes()) {
      if (featureType.getType().startsWith(PREDICATE_WORD_PREFIX)) {
        ret.addAll(featureType.getValues());
      }
    }

    return ret.build();
  }

  private static ImmutableSet<String> getPredicates(final ImmutableCollection<InstanceFeatures> instances) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for(final InstanceFeatures instance : instances) {
      ret.addAll(getPredicates(instance));
    }

    return ret.build();
  }

  private static ImmutableSet<String> toSingleStrings(final ImmutableSet<StringPair> pairs) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for (final StringPair pair : pairs) {
      ret.add(pair.getFirstString());
      ret.add(pair.getSecondString());
    }

    return ret.build();
  }

  private static ImmutableSet<StringPair> filterPairBySingle(final ImmutableSet<StringPair> pairs,
      final ImmutableSet<String> vocab) {
    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();

    for (final StringPair pair : pairs) {
      if (vocab.contains(pair.getFirstString()) && vocab.contains(pair.getSecondString())) {
        ret.add(pair);
      }
    }

    return ret.build();
  }

  private static ImmutableMap<String, InstanceFeatures> filterForFeatureTypes(
      final ImmutableMap<String, InstanceFeatures> instanceFeatures,
      final ImmutableSet<String> targetFeatureTypes) {
    final ImmutableMap.Builder<String, InstanceFeatures> ret = ImmutableMap.builder();

    for (final Map.Entry<String, InstanceFeatures> entry : instanceFeatures.entrySet()) {
      boolean useExample = true;
      for (final String type : targetFeatureTypes) {
        if (!entry.getValue().getFeatureType(type).isPresent()) {
          useExample = false;
          break;
        }
      }

      if (useExample) {
        ret.put(entry);
      }
    }

    return ret.build();
  }

  private static ImmutableSet<StringPair> readIdPairs(final File infile) throws IOException {
    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();

    final ImmutableList<String> lines = Files.asCharSource(infile, Charsets.UTF_8).readLines();

    for(final String line : lines) {
      final String[] tokens = line.split(" ");
      ret.add(StringPair.from(tokens[0], tokens[1]));
    }

    return ret.build();
  }

  final static String PREDICATE_WORD_PREFIX = new String("Lex:WordIdentity");

  public enum PreparationPhase {
    TRAIN,
    PRE_TEST,
    TEST,
    SAMPLE_TRAIN
  }
}
