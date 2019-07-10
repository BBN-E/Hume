package com.bbn.necd.event.formatter;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;
import com.google.common.primitives.Doubles;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;

/**
 * Created by ychan on 2/4/16.
 */
public final class LearningFeatureFormatter {

  private static final Logger log = LoggerFactory.getLogger(LearningFeatureFormatter.class);

  // ids: set of instanceIds
  public static void writeInstanceIds(final ImmutableSet<String> ids, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final String id : ids) {
      outLines.add(id);
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  public static void writeInstancePairIds(final ImmutableSet<StringPair> idPairs, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final StringPair idPair : idPairs) {
      outLines.add(idPair.getFirstString() + "\t" + idPair.getSecondString());
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  // instanceLabels: instanceId -> event code label
  // targetIds: the set of instanceIds I am interested in (e.g. filtered to a subset that satisfies some requirements
  public static void writeInstanceLabels(final ImmutableSet<String> targetIds,
      final ImmutableMap<String, String> instanceLabels, final File outfile) throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final String id : targetIds) {
      final String label = instanceLabels.get(id);
      if(label.compareTo(NA)!=0) {
        final String line = id + "\t" + label;
        outLines.add(line);
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  public static void writeInstancePairLabels(final ImmutableSet<StringPair> targetIds,
      final ImmutableMap<String, String> instanceLabels, final File outfile) throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final StringPair pair : targetIds) {
      final String id1 = pair.getFirstString();
      final String id2 = pair.getSecondString();
      final String label1 = instanceLabels.get(id1);
      final String label2 = instanceLabels.get(id2);

      if(label1.compareTo(NA)!=0 && label2.compareTo(NA)!=0) {
        if (label1.compareTo(label2) == 0) {
          final String line = id1 + "\t" + id2 + "\t" + "1";
          outLines.add(line);
        } else {
          final String line = id1 + "\t" + id2 + "\t" + "0";
          outLines.add(line);
        }
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  public static void writeInstancePairFeatures(
      final ImmutableMap<StringPair, InstanceFeatures> instancePairFeatures,
      final ImmutableSet<StringPair> targetIds, final double defaultWeight, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final StringPair idPair : targetIds) {
      final InstanceFeatures features = instancePairFeatures.get(idPair);
      for (final FeatureType featureType : features.getFeatureTypes()) {
        final String type = featureType.getType();
        for (final String featureValue : featureType.getValues()) {
          final Double number = Doubles.tryParse(featureValue);
          if (number != null) {
            final String line =
                idPair.getFirstString() + "\t" + idPair.getSecondString() + "\t" + type + "\t"
                    + number.toString();
            outLines.add(line);
          } else {
            final String line =
                idPair.getFirstString() + "\t" + idPair.getSecondString() + "\t" + type + ":"
                    + featureValue + "\t" + defaultWeight;
            outLines.add(line);
          }
        }
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }


  public static void writeInstanceFeatures(
      final ImmutableMap<String, InstanceFeatures> instanceFeatures,
      final ImmutableSet<String> targetIds, final double defaultWeight, final File outfile)
      throws IOException {
    final ImmutableList.Builder<String> outLines = ImmutableList.builder();

    for (final String instanceId : targetIds) {
      final InstanceFeatures features = instanceFeatures.get(instanceId);
      for (final FeatureType featureType : features.getFeatureTypes()) {
        final String type = featureType.getType();
        for (final String featureValue : featureType.getValues()) {
          final String line = instanceId + "\t" + type + ":" + featureValue + "\t" + defaultWeight;
          outLines.add(line);
        }
      }
    }

    Files.asCharSink(outfile, Charsets.UTF_8).writeLines(outLines.build());
  }

  private static final String NA = new String("NA");

}
