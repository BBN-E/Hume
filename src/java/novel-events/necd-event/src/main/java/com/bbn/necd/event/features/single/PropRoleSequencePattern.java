package com.bbn.necd.event.features.single;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.SingleFeature;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.PropositionTreeFeatures;
import com.bbn.necd.event.propositions.PropositionEdge;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Lists;
import com.google.common.collect.Multiset;
import com.google.common.collect.Ordering;
import com.google.common.collect.Table;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Set;

/**
 * Created by ychan on 5/12/16.
 */
public final class PropRoleSequencePattern extends SingleFeature {
  private static final Logger log = LoggerFactory.getLogger(PropRoleSequencePattern.class);

  private PropRoleSequencePattern(final String featureName,
      final ImmutableTable<Symbol, Integer, Double> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
    return new Builder(featureName, runningIndex, sparsityThreshold);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableTable.Builder<Symbol, Integer, Double> features;
    private final BiMap<String, Integer> featureIndices;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final int sparsityThreshold;

    private Builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableTable.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
      this.sparsityThreshold = sparsityThreshold;
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<Symbol> ids,
        final ImmutableMap<Symbol, EventFeatures> examples) {

      final ImmutableTable.Builder<Symbol, String, Double> featuresCacheBuilder = ImmutableTable.builder();

      for (final Symbol item : ids) {
        final EventFeatures eg = examples.get(item);

        final ImmutableList<String> rolesSequence = getPropRolePatterns(eg);

        for(final String sequence : rolesSequence) {
          final String v = featureName + DELIMITER + sequence;
          featuresCacheBuilder.put(item, v, 1.0);
        }
      }
      final ImmutableTable<Symbol, String, Double> featuresCache = featuresCacheBuilder.build();

      final Multiset<String> featureCounts = getFeatureCount(featuresCache);

      for(final Table.Cell<Symbol, String, Double> cell : featuresCache.cellSet()) {
        final Symbol item = cell.getRowKey();
        final String v = cell.getColumnKey();
        final Double weight = cell.getValue();
        if(featureCounts.count(v) >= sparsityThreshold) {
          addFeatureValue(item, v, weight);
        }
      }

      return this;
    }

    private void addFeatureValue(final Symbol item, final String v, final Double weight) {
      if(existingFeatureIndices.isPresent()) {
        if(existingFeatureIndices.get().containsKey(v)) {
          final int index = existingFeatureIndices.get().get(v);
          featureIndices.put(v, index);
          features.put(item, index, weight);
        }
      } else {
        if(featureIndices.containsKey(v)) {
          features.put(item, featureIndices.get(v), weight);
        } else {
          featureIndices.put(v, runningIndex);
          features.put(item, runningIndex, weight);
          runningIndex++;
        }
      }
    }

    public PropRoleSequencePattern build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new PropRoleSequencePattern(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new PropRoleSequencePattern(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }

  public static ImmutableList<String> getPropRolePatterns(final EventFeatures eg) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();

    List<String> sourceRoles = Lists.newArrayList();    // source to root
    for(int i=0; i<propPathSourceToRoot.size(); i++) {
      sourceRoles.add(propPathSourceToRoot.get(i).label().name());
    }

    List<String> targetRoles = Lists.newArrayList();    // root to target
    for(int i=0; i<propPathRootToTarget.size(); i++) {
      targetRoles.add(propPathRootToTarget.get(i).label().name());
    }

    // source to root
    if(sourceRoles.size() >= 2) {
      for(int i=0; i<sourceRoles.size(); i++) {
        StringBuilder sb = new StringBuilder();
        for(int j=(sourceRoles.size()-1); j>=0; j--) {
          if(sb.length()>0) {
            sb.append("_");
          }
          if(i==j) {
            sb.append(PropositionTreeFeatures.ASTERISK);
          } else {
            sb.append(sourceRoles.get(j));
          }
        }
        ret.add(PropositionTreeFeatures.ROOT + DELIMITER + sb.toString() + DELIMITER + PropositionTreeFeatures.SOURCE);
        ret.add(PropositionTreeFeatures.ROOT + DELIMITER + sb.toString() + DELIMITER + PropositionTreeFeatures.ARGUMENT);
      }
    }

    // root to target
    if(targetRoles.size() >= 2) {
      for(int i=0; i<targetRoles.size(); i++) {
        StringBuilder sb = new StringBuilder();
        for(int j=0; j<targetRoles.size(); j++) {
          if(sb.length()>0) {
            sb.append("_");
          }
          if(i==j) {
            sb.append(PropositionTreeFeatures.ASTERISK);
          } else {
            sb.append(targetRoles.get(j));
          }
        }
        ret.add(PropositionTreeFeatures.ROOT + DELIMITER + sb.toString() + DELIMITER + PropositionTreeFeatures.TARGET);
        ret.add(PropositionTreeFeatures.ROOT + DELIMITER + sb.toString() + DELIMITER + PropositionTreeFeatures.ARGUMENT);
      }
    }

    List<String> sourceToTargetRoles = Lists.newArrayList();
    sourceToTargetRoles.addAll(sourceRoles);
    sourceToTargetRoles.addAll(targetRoles);
    if(sourceToTargetRoles.size() >= 2) {
      for(int i=0; i<sourceToTargetRoles.size(); i++) {
        StringBuilder sb = new StringBuilder();
        for(int j=0; j<sourceToTargetRoles.size(); j++) {
          if(sb.length()>0) {
            sb.append("_");
          }
          if(i==j) {
            sb.append(PropositionTreeFeatures.ASTERISK);
          } else {
            sb.append(sourceToTargetRoles.get(j));
          }
        }
        ret.add(PropositionTreeFeatures.ARGUMENT + DELIMITER + sb.toString() + DELIMITER + PropositionTreeFeatures.ARGUMENT);
      }
    }

    return ret.build();
  }

}
