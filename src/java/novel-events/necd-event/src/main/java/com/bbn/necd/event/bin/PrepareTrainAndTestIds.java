package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.event.features.EventFeatureType;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventFeaturesUtils;
import com.bbn.necd.event.io.LabelWriter;

import com.google.common.base.Charsets;
import com.google.common.base.Predicates;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
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
  We want to do 2 things.
  First, we might want to filter examples based on them having certain feature types we deem mandatory. E.g. have predicates
  Second, when we are doing testing, N choose 2 combinations can result in a large number of examples.
  Hence for testing, it is better to split up those combinations into multiple sets, and thereafter decoding these sets in parallel.

  Parameters:
  - feature.mandatoryTypes
  - eventFeatures

  - pairLabelsTable (if this is present, we are preparing for training)
    - memberPair.label
    - memberPair.list
    - targetMembers.label
    - targetMembers.list
  - Else, we are preparing for decoding:
    - labelsTable
    - feature.outputDir
    - feature.numberOfSets

  - * from PredictVectorManager
      - data.predictVectorFile
      - feature.minValue
 */
public final class PrepareTrainAndTestIds {
  private static final Logger log = LoggerFactory.getLogger(PrepareFeaturesForSimilarityMetric.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    // data.predictVectorFile: <embeddings-file>
    // feature.minValue: 0
    final PredictVectorManager predictVectorManager = PredictVectorManager.fromParams(params).build();

    // e.g. feature.mandatoryTypes: PREDICATES
    final List<EventFeatureType.HasFeatureType> mandatoryFeatureTypes =
        params.getEnumList("feature.mandatoryTypes", EventFeatureType.HasFeatureType.class);

    // e.g. eventFeatures: 1.featuretable.event.tsv.gz
    final ImmutableMap<Symbol, EventFeatures> eventFeatures = filterExamplesByFeatureTypes(
        EventFeaturesUtils.readEventFeatures(params.getExistingFile("eventFeatures")),
        mandatoryFeatureTypes, predictVectorManager);

    if(params.isPresent("pairLabelsTable")) {
      // this is training
      final File labelsTable = params.getExistingFile("pairLabelsTable");

      // filter the training id pairs by the event instances that survive filtering
      final ImmutableSet<SymbolPair> idPairs = filterPairBySingle(readIdPairs(labelsTable), eventFeatures.keySet());

      // instanceid -> event label
      final ImmutableMap<Symbol, Symbol> instanceLabels =
          ImmutableMap.copyOf(Maps.filterKeys(readLabelFromPairLabels(labelsTable), Predicates.in(toSingle(idPairs))));

      writeInstancePairLabels(idPairs, instanceLabels, params.getCreatableFile("memberPair.label"));
      writeInstancePairIds(idPairs, params.getCreatableFile("memberPair.list"));

      writeInstanceLabels(instanceLabels, params.getCreatableFile("targetMembers.label"));
      writeInstanceIds(instanceLabels.keySet(), params.getCreatableFile("targetMembers.list"));

    } else {
      // this is testing or decoding
      final File labelsTable = params.getExistingFile("labelsTable");
      final ImmutableMap<Symbol, Symbol> instanceLabels = readLabelFromLabels(labelsTable);


      final File outDir = params.getExistingFileOrDirectory("feature.outputDir");

      log.info("preparing id pairs");
      final int numberOfSets = params.getInteger("feature.numberOfSets");
      List<Symbol> ids = Lists.newArrayList(eventFeatures.keySet());
      Collections.shuffle(ids, new Random(params.getInteger("randomSeed")));
      //final ImmutableList<Symbol> ids = Collections.shuffle(eventFeatures.keySet().asList(), new Random(0));
      final int sizePerSet =
          (int) Math.round( ((((float)ids.size()*(ids.size()-1) )/2 )/numberOfSets) +0.5 );

      int setCounter = 1;
      List<SymbolPair> idPairsHolder = Lists.newArrayList();
      for(int i=0; i<ids.size()-1; i++) {
        for(int j=(i+1); j<ids.size(); j++) {
          idPairsHolder.add(SymbolPair.from(ids.get(i), ids.get(j)));

          if(idPairsHolder.size() >= sizePerSet) {  // dump to file
            final ImmutableSet<SymbolPair> idPairs = ImmutableSet.copyOf(idPairsHolder);
            final ImmutableSet<Symbol> singleIds = toSingle(idPairs);
            final ImmutableMap<Symbol, Symbol> instanceLabelsHolder = ImmutableMap.copyOf(Maps.filterKeys(instanceLabels, Predicates.in(singleIds)));

            writeInstancePairLabels(idPairs, instanceLabels, new File(outDir, "set"+setCounter+".memberPair.label"));
            writeInstancePairIds(idPairs, new File(outDir, "set"+setCounter+".memberPair.list"));

            writeInstanceLabels(instanceLabelsHolder, new File(outDir, "set"+setCounter+".targetMembers.label"));
            writeInstanceIds(instanceLabelsHolder.keySet(), new File(outDir, "set"+setCounter+".targetMembers.list"));

            setCounter += 1;
            idPairsHolder.clear();
          }
        }
      }

      final ImmutableSet<SymbolPair> idPairs = ImmutableSet.copyOf(idPairsHolder);
      final ImmutableSet<Symbol> singleIds = toSingle(idPairs);
      final ImmutableMap<Symbol, Symbol> instanceLabelsHolder = ImmutableMap.copyOf(Maps.filterKeys(instanceLabels, Predicates.in(singleIds)));

      writeInstancePairLabels(idPairs, instanceLabels, new File(outDir, "set"+setCounter+".memberPair.label"));
      writeInstancePairIds(idPairs, new File(outDir, "set"+setCounter+".memberPair.list"));

      writeInstanceLabels(instanceLabelsHolder, new File(outDir, "set"+setCounter+".targetMembers.label"));
      writeInstanceIds(instanceLabelsHolder.keySet(), new File(outDir, "set"+setCounter+".targetMembers.list"));

    }


  }

  public static ImmutableMap<Symbol, EventFeatures> filterExamplesByFeatureTypes(
      final ImmutableMap<Symbol, EventFeatures> examples,
      final List<EventFeatureType.HasFeatureType> mandatoryFeatureTypes,
      final PredictVectorManager predictVectorManager) {
    final ImmutableMap.Builder<Symbol, EventFeatures> ret = ImmutableMap.builder();

    for (final Map.Entry<Symbol, EventFeatures> entry : examples.entrySet()) {
      boolean useExample = true;

      final EventFeatures eg = entry.getValue();

      for (final EventFeatureType.HasFeatureType featureType : mandatoryFeatureTypes) {
        if (!featureType.hasValue(eg)) {
          useExample = false;
        }
      }

      /*
      if (useExample) {
        useExample = false;
        // does at least one of its predicate have embedding information
        for(final Symbol predicate : eg.predicates()) {
          if(predictVectorManager.getVector(predicate).isPresent()) {
            useExample = true;
            break;
          }
        }
      }
      */

      if(useExample) {
        ret.put(entry);
      }
    }

    return ret.build();
  }

  // instanceId -> event label
  public static ImmutableMap<Symbol, Symbol> readLabelFromPairLabels(final File infile) throws IOException {
    final ImmutableMap.Builder<Symbol, Symbol> ret = ImmutableMap.builder();
    Map<Symbol, Symbol> labels = Maps.newHashMap();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final Symbol id1 = Symbol.from(row.get(0));
      final Symbol label1 = Symbol.from(row.get(2));
      if (labels.containsKey(id1)) {
        if (!labels.get(id1).equalTo(label1)) {
          log.error("Instance id {} has different labels: {} {}", id1, labels.get(id1), label1);
        }
      } else {
        ret.put(id1, label1);
        labels.put(id1, label1);
      }

      final Symbol id2 = Symbol.from(row.get(1));
      final Symbol label2 = Symbol.from(row.get(3));
      if (labels.containsKey(id2)) {
        if (!labels.get(id2).equalTo(label2)) {
          log.error("Instance id {} has different labels: {} {}", id2, labels.get(id2), label2);
        }
      } else {
        ret.put(id2, label2);
        labels.put(id2, label2);
      }
    }

    return ret.build();
  }


  public static ImmutableMap<Symbol, Symbol> readLabelFromLabels(final File infile) throws IOException {
    final ImmutableMap.Builder<Symbol, Symbol> ret = ImmutableMap.builder();
    Map<Symbol, Symbol> labels = Maps.newHashMap();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final Symbol id = Symbol.from(row.get(0));
      final Symbol label = Symbol.from(row.get(1));
      if (labels.containsKey(id)) {
        if (!labels.get(id).equalTo(label)) {
          log.error("Instance id {} has different labels: {} {}", id, labels.get(id), label);
        }
      } else {
        ret.put(id, label);
        labels.put(id, label);
      }
    }

    return ret.build();
  }

  // read the set of instanceId pairs we are given
  public static ImmutableSet<SymbolPair> readIdPairs(final File infile) throws IOException {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final SymbolPair idPair = SymbolPair.from(Symbol.from(row.get(0)), Symbol.from(row.get(1)));
      ret.add(idPair);
    }

    return ret.build();
  }

  private static ImmutableSet<SymbolPair> filterPairBySingle(final ImmutableSet<SymbolPair> pairs,
      final ImmutableSet<Symbol> vocab) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    for (final SymbolPair pair : pairs) {
      if (vocab.contains(pair.getFirstMember()) && vocab.contains(pair.getSecondMember())) {
        ret.add(pair);
      }
    }

    return ret.build();
  }

  private static ImmutableSet<Symbol> toSingle(final ImmutableSet<SymbolPair> pairs) {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for (final SymbolPair pair : pairs) {
      ret.add(pair.getFirstMember());
      ret.add(pair.getSecondMember());
    }

    return ret.build();
  }


  // ids: set of instanceIds
  public static void writeInstanceIds(final ImmutableSet<Symbol> ids, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final Symbol id : ids) {
      outLines.add(id.asString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  public static void writeInstancePairIds(final ImmutableSet<SymbolPair> idPairs, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final SymbolPair idPair : idPairs) {
      outLines.add(idPair.getFirstMember().asString() + "\t" + idPair.getSecondMember().asString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  // instanceLabels: instanceId -> event code label
  // targetIds: the set of instanceIds I am interested in (e.g. filtered to a subset that satisfies some requirements
  public static void writeInstanceLabels(final ImmutableMap<Symbol, Symbol> instanceLabels, final File outfile) throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for(final Map.Entry<Symbol, Symbol> entry : instanceLabels.entrySet()) {
      if(!entry.getValue().equalTo(NA)) {
        final String line = entry.getKey().asString() + "\t" + entry.getValue().asString();
        outLines.add(line);
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  public static void writeInstancePairLabels(final ImmutableSet<SymbolPair> targetIds,
      final ImmutableMap<Symbol, Symbol> instanceLabels, final File outfile) throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final SymbolPair pair : targetIds) {
      final Symbol id1 = pair.getFirstMember();
      final Symbol id2 = pair.getSecondMember();
      final Symbol label1 = instanceLabels.get(id1);
      final Symbol label2 = instanceLabels.get(id2);

      if(!label1.equalTo(NA) && !label2.equalTo(NA)) {
        if (label1.equalTo(label2)) {
          final String line = id1.asString() + "\t" + id2.asString() + "\t" + "1";
          outLines.add(line);
        } else {
          final String line = id1.asString() + "\t" + id2.asString() + "\t" + "0";
          outLines.add(line);
        }
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  // We need to do some deterministic reordering of the ids. Because all the positives might be present before negatives.
  // Then, when we do N-choose-2 combinations, all the positive pairs will be generated first, then the negatives.
  // Thus, the latter sets will have no positive pairs.
  private static ImmutableList<Symbol> frontBackReordering(final ImmutableList<Symbol> ids) {
    final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

    int front = 0;
    int back = ids.size()-1;

    while(front < back) {
      ret.add(ids.get(front));
      ret.add(ids.get(back));
      front += 1;
      back -= 1;
    }
    if(front == back) {
      ret.add(ids.get(front));
    }

    return ret.build();
  }

  private final static Symbol NA = Symbol.from("NA");
}

