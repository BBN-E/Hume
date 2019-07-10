package com.bbn.necd.event.features.single;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.theory.SingleFeature;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.PropositionTreeFeatures;
import com.bbn.nlp.WordAndPOS;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Multiset;
import com.google.common.collect.Ordering;
import com.google.common.collect.Table;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;

/**
 * Created by ychan on 5/13/16.
 */
public final class WordsOnPath extends SingleFeature {
  private static final Logger log = LoggerFactory.getLogger(WordsOnPath.class);

  private WordsOnPath(final String featureName,
      final ImmutableTable<Symbol, Integer, Double> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final int sparsityThreshold, final BackgroundInformation backgroundInformation) {
    return new Builder(featureName, runningIndex, sparsityThreshold, backgroundInformation);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableTable.Builder<Symbol, Integer, Double> features;
    private final BiMap<String, Integer> featureIndices;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final int sparsityThreshold;
    private final BackgroundInformation backgroundInformation;

    private Builder(final String featureName, final int runningIndex, final int sparsityThreshold,
        final BackgroundInformation backgroundInformation) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableTable.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
      this.sparsityThreshold = sparsityThreshold;
      this.backgroundInformation = backgroundInformation;
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

        // sequence of (lemma,POS) on path from source to target. Excludes source and target themselves.
        final ImmutableList<WordAndPOS> wordPosOnPath =
            PropositionTreeFeatures.getWordPosOnPathSourceToTarget(eg, backgroundInformation);

        final ImmutableList<WordAndPOS> verbsOnPath =
            PropositionTreeFeatures.getVerbs(wordPosOnPath, backgroundInformation.getLanguage());

        // feature
        final ImmutableSet<Symbol> nonAuxiliaryVerbLemmaOnPath = PropositionTreeFeatures.toWords(
            PropositionTreeFeatures.getNonAuxiliaryVerbs(verbsOnPath, backgroundInformation));

        for(final Symbol w : nonAuxiliaryVerbLemmaOnPath) {
          final String v = featureName + DELIMITER + w.asString();
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

    public WordsOnPath build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new WordsOnPath(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new WordsOnPath(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }
}
