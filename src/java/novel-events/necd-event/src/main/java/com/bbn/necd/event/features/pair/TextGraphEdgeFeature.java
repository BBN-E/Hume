package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.FeatureUtils;
import com.bbn.necd.event.features.PropositionTreeFeatures;
import com.bbn.necd.event.formatter.StringPair;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Ordering;

import org.apache.commons.lang3.StringUtils;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 6/28/16.
 */
public final class TextGraphEdgeFeature extends PairFeature {
  private TextGraphEdgeFeature(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex) {
    return new Builder(featureName, runningIndex);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;

    private Builder(final String featureName, final int runningIndex) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {

      for (final SymbolPair idPair : idPairs) {
        final Symbol id1 = idPair.getFirstMember();
        final Symbol id2 = idPair.getSecondMember();

        final ImmutableMap.Builder<String, Double> featuresBuilder = ImmutableMap.builder();


        final String propRoleSequenceSourceToRoot1 = StringUtils.join(FeatureUtils.getPropRoleSequenceSourceToRoot(examples.get(id1)), "_");
        final ImmutableSet<String> sourceRoles1 = FeatureUtils.getSourcePropRoles(examples.get(id1));
        final ImmutableSet<String> sr1 = ImmutableSet.<String>builder().addAll(sourceRoles1).add(propRoleSequenceSourceToRoot1).build();

        final String propRoleSequenceSourceToRoot2 = StringUtils.join(FeatureUtils.getPropRoleSequenceSourceToRoot(examples.get(id2)), "_");
        final ImmutableSet<String> sourceRoles2 = FeatureUtils.getSourcePropRoles(examples.get(id2));
        final ImmutableSet<String> sr2 = ImmutableSet.<String>builder().addAll(sourceRoles2).add(propRoleSequenceSourceToRoot2).build();

        final ImmutableSet<StringPair> sourceRolePairs = StringPair.toStringPairs(sr1, sr2);
        for(final StringPair pair : sourceRolePairs) {
          if(pair.getFirstString().length()>0 && pair.getSecondString().length()>0) {
            final String s =
                featureName + DELIMITER + PropositionTreeFeatures.SOURCE + DELIMITER + pair
                    .getFirstString() + DELIMITER + pair.getSecondString();
            featuresBuilder.put(s, 1.0);
          }
        }

        final String propRoleSequenceRootToTarget1 = StringUtils.join(FeatureUtils.getPropRoleSequenceRootToTarget(examples.get(id1)), "_");
        final ImmutableSet<String> targetRoles1 = FeatureUtils.getTargetPropRoles(examples.get(id1));
        final ImmutableSet<String> tr1 = ImmutableSet.<String>builder().addAll(targetRoles1).add(propRoleSequenceRootToTarget1).build();

        final String propRoleSequenceRootToTarget2 = StringUtils.join(FeatureUtils.getPropRoleSequenceRootToTarget(examples.get(id2)), "_");
        final ImmutableSet<String> targetRoles2 = FeatureUtils.getTargetPropRoles(examples.get(id2));
        final ImmutableSet<String> tr2 = ImmutableSet.<String>builder().addAll(targetRoles2).add(propRoleSequenceRootToTarget2).build();

        final ImmutableSet<StringPair> targetRolePairs = StringPair.toStringPairs(tr1, tr2);
        for(final StringPair pair : targetRolePairs) {
          if(pair.getFirstString().length()>0 && pair.getSecondString().length()>0) {
            final String s =
                featureName + DELIMITER + PropositionTreeFeatures.TARGET + DELIMITER + pair
                    .getFirstString() + DELIMITER + pair.getSecondString();
            featuresBuilder.put(s, 1.0);
          }
        }

        final ImmutableMap<Integer, Double> indices = toFeatureIndices(featuresBuilder.build());

        features.put(idPair, WeightedIndicesPair.from(indices, indices));
      }

      return this;
    }

    private ImmutableMap<Integer, Double> toFeatureIndices(
        final ImmutableMap<String, Double> features) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for (final Map.Entry<String, Double> feature : features.entrySet()) {
        final String v = feature.getKey();
        final Double weight = feature.getValue();

        if (existingFeatureIndices.isPresent()) {
          if (existingFeatureIndices.get().containsKey(v)) {
            final int index = existingFeatureIndices.get().get(v);
            featureIndices.put(v, index);
            ret.put(index, weight);
          }
        } else {
          if (featureIndices.containsKey(v)) {
            ret.put(featureIndices.get(v), weight);
          } else {
            featureIndices.put(v, runningIndex);
            ret.put(runningIndex, weight);
            runningIndex++;
          }
        }
      }

      return ret.build();
    }

    public TextGraphEdgeFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new TextGraphEdgeFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new TextGraphEdgeFeature(featureName, features.build(), featureIndices, -1, -1);
      }

    }
  }

}
