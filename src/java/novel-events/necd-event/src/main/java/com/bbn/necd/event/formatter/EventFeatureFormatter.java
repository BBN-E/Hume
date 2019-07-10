package com.bbn.necd.event.formatter;

import com.bbn.necd.event.io.EventWriter;
import com.bbn.necd.event.io.LabelWriter;
import com.bbn.necd.event.io.LabeledIdWriter;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVPrinter;
import org.apache.commons.csv.CSVRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Map;

import static com.bbn.necd.event.io.CompressedFileUtils.openBufferedCompressedWriter;

/**
 * Created by ychan on 2/4/16.
 */
public final class EventFeatureFormatter {
  private static final Logger log = LoggerFactory.getLogger(EventFeatureFormatter.class);


  public static void filterInstanceFeatures(final File infile, final File outfile, final ImmutableSet<String> targetIds)
      throws IOException {

    final String[] EVENT_HEADER = new String[]{"Id", "Feature", "Value"};
    final CSVPrinter writer =
        new CSVPrinter(openBufferedCompressedWriter(outfile), CSVFormat.TDF.withHeader(EVENT_HEADER));

    final CSVParser parser = EventWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final String instanceId = row.get(0);
      final String featureType = row.get(1);
      final String featureValue = row.get(2);

      if(targetIds.contains(instanceId)) {
        writer.printRecord(instanceId, featureType, featureValue);
      }
    }

    writer.close();
  }

  public static void writeIdLabel(final File outfile, final Map<String, String> idLabels) throws IOException {
    final LabeledIdWriter writer = LabeledIdWriter.create(outfile);
    for(final Map.Entry<String, String> entry : idLabels.entrySet()) {
      writer.writeLabel(entry.getKey(), entry.getValue());
    }
    writer.close();
  }

  // read per instance features
  public static ImmutableMap<String, InstanceFeatures> readInstanceFeatures(final File infile)
      throws IOException {

    final Map<String, InstanceFeatures.Builder> instanceFeatures = Maps.newHashMap();
    final CSVParser parser = EventWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final String instanceId = row.get(0);
      final String featureType = row.get(1);
      final String featureValue = row.get(2);

      if (instanceFeatures.containsKey(instanceId)) {
        instanceFeatures.get(instanceId).addFeatureValue(featureType, featureValue);
      } else {
        instanceFeatures
            .put(instanceId, InstanceFeatures.builder().addFeatureValue(featureType, featureValue));
      }
    }

    // sort using instanceId
    final ImmutableMap.Builder<String, InstanceFeatures> ret = ImmutableMap.builder();
    for (final String instanceId : Ordering.natural()
        .immutableSortedCopy(instanceFeatures.keySet())) {
      ret.put(instanceId, instanceFeatures.get(instanceId).build());
    }

    return ret.build();
  }

  // read pairwise features
  public static ImmutableMap<StringPair, InstanceFeatures> readInstancePairFeatures(
      final File infile) throws IOException {

    final Map<StringPair, InstanceFeatures.Builder> instanceFeatures = Maps.newHashMap();
    final CSVParser parser = EventWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final StringPair idPair = StringPair.from(row.get(0), row.get(1));
      final String featureType = row.get(2);
      final String featureValue = row.get(3);

      if (instanceFeatures.containsKey(idPair)) {
        instanceFeatures.get(idPair).addFeatureValue(featureType, featureValue);
      } else {
        instanceFeatures
            .put(idPair, InstanceFeatures.builder().addFeatureValue(featureType, featureValue));
      }
    }

    // sort using pair of instance ids
    final ImmutableMap.Builder<StringPair, InstanceFeatures> ret = ImmutableMap.builder();
    for (final StringPair idPair : Ordering.natural()
        .immutableSortedCopy(instanceFeatures.keySet())) {
      ret.put(idPair, instanceFeatures.get(idPair).build());
    }

    return ret.build();
  }

  // read the set of instanceId pairs we are given
  public static ImmutableSet<StringPair> readIdPairs(final File infile) throws IOException {
    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final StringPair idPair = StringPair.from(row.get(0), row.get(1));
      ret.add(idPair);
    }

    return ret.build();
  }

  // instanceId -> event label
  public static ImmutableMap<String, String> readPairLabels(final File infile) throws IOException {
    final ImmutableMap.Builder<String, String> ret = ImmutableMap.builder();
    Map<String, String> labels = Maps.newHashMap();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final String id1 = row.get(0);
      final String label1 = row.get(2);
      if (labels.containsKey(id1)) {
        if (labels.get(id1).compareTo(label1) != 0) {
          log.error("Instance id {} has different labels: {} {}", id1, labels.get(id1), label1);
        }
      } else {
        ret.put(id1, label1);
        labels.put(id1, label1);
      }

      final String id2 = row.get(1);
      final String label2 = row.get(3);
      if (labels.containsKey(id2)) {
        if (labels.get(id2).compareTo(label2) != 0) {
          log.error("Instance id {} has different labels: {} {}", id2, labels.get(id2), label2);
        }
      } else {
        ret.put(id2, label2);
        labels.put(id2, label2);
      }
    }

    return ret.build();
  }

  public static ImmutableMap<String, String> readLabels(final File infile) throws IOException {
    final ImmutableMap.Builder<String, String> ret = ImmutableMap.builder();
    Map<String, String> labels = Maps.newHashMap();

    final CSVParser parser = LabelWriter.getParser(infile);
    for (CSVRecord row : parser) {
      final String id = row.get(0);
      final String label = row.get(1);
      if (labels.containsKey(id)) {
        if (labels.get(id).compareTo(label) != 0) {
          log.error("Instance id {} has different labels: {} {}", id, labels.get(id), label);
        }
      } else {
        ret.put(id, label);
        labels.put(id, label);
      }
    }

    return ret.build();
  }
}
