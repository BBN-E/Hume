package com.bbn.necd.event.bin;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.necd.event.formatter.EventFeatureFormatter;
import com.bbn.necd.event.formatter.InstanceFeatures;
import com.bbn.necd.event.formatter.LearningFeatureFormatter;
import com.bbn.necd.event.formatter.StringPair;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.util.Map;

/**
 * Created by ychan on 2/2/16.
 * Convert feature tables from event generation to a format preferred by learning
 */
public final class FeatureConverter {
  private static final Logger log = LoggerFactory.getLogger(FeatureConverter.class);

  public static void main(final String[] argv) throws IOException {
    final String paramFilename = argv[0];

    final Parameters params = Parameters.loadSerifStyle(new File(paramFilename));
    log.info(params.dump());

    final File eventFeaturesTable = params.getExistingFile("eventFeaturesTable");
    final File pairFeaturesTable = params.getExistingFile("pairFeaturesTable");
    final File pairLabelsTable = params.getExistingFile("pairLabelsTable");

    // to consider an example, we require that this feature type exist
    final ImmutableSet<String> mandatoryFeatureTypes = ImmutableSet.copyOf(params.getStringList("feature.single.targetTypes"));
    for(final String type : mandatoryFeatureTypes) {
      log.info("feature.single.targetTypes: {}", type);
    }

    final ImmutableMap<String, InstanceFeatures> instanceFeatures =
        filterForFeatureTypes(
            EventFeatureFormatter.readInstanceFeatures(eventFeaturesTable),
            mandatoryFeatureTypes);

    final ImmutableMap<StringPair, InstanceFeatures> instancePairFeatures =
        EventFeatureFormatter.readInstancePairFeatures(pairFeaturesTable);

    // instanceid -> event label
    final ImmutableMap<String, String> instanceLabels =
        EventFeatureFormatter.readLabels(pairLabelsTable);

    final ImmutableSet<StringPair> idPairs = EventFeatureFormatter.readIdPairs(pairLabelsTable);

    // we will use filteredIds and filterdIdPairs as our final set of instances
    final ImmutableSet<StringPair> filteredIdPairs = filterPairBySingle(
        Sets.intersection(instancePairFeatures.keySet(), idPairs).immutableCopy(),
        instanceFeatures.keySet());
    final ImmutableSet<String> filteredIds = toSingleStrings(filteredIdPairs);


    LearningFeatureFormatter.writeInstanceFeatures(instanceFeatures, filteredIds, 1.0, params.getCreatableFile("feature.single.featureTable"));
    LearningFeatureFormatter.writeInstancePairFeatures(instancePairFeatures, filteredIdPairs, 1.0, params.getCreatableFile("feature.pairwise.featureTable"));

    LearningFeatureFormatter.writeInstancePairLabels(filteredIdPairs, instanceLabels, params.getCreatableFile("memberPair.label"));
    LearningFeatureFormatter.writeInstanceLabels(filteredIds, instanceLabels, params.getCreatableFile("targetMembers.label"));

    LearningFeatureFormatter.writeInstanceIds(filteredIds, params.getCreatableFile("targetMembers"));
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

}
