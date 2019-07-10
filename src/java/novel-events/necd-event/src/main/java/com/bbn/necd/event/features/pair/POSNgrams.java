package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.propositions.PropositionEdge;
import com.bbn.necd.event.wrappers.SynNodeInfo;
import com.bbn.nlp.WordAndPOS;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Ordering;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 6/30/16.
 */
public final class POSNgrams extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(POSNgrams.class);

  private POSNgrams(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final BackgroundInformation backgroundInformation) {
    return new Builder(featureName, runningIndex, backgroundInformation);
  }

  public static class Builder {

    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;


    private Builder(final String featureName, final int runningIndex,
        final BackgroundInformation backgroundInformation) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.docSentences = backgroundInformation.getDocSentences();
      this.existingFeatureIndices = Optional.absent();
    }

    public Builder withExistingFeatureIndices(
        final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {

      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        final ImmutableSet<String> ngrams1 = getPOSNgrams(examples.get(id1));
        final ImmutableSet<String> ngrams2 = getPOSNgrams(examples.get(id2));

        final ImmutableMap.Builder<String, Double> features1 = ImmutableMap.builder();
        for(final String ngram : ngrams1) {
          final String v = featureName + DELIMITER + ngram;
          features1.put(v, 1.0);
        }

        final ImmutableMap.Builder<String, Double> features2 = ImmutableMap.builder();
        for(final String ngram : ngrams2) {
          final String v = featureName + DELIMITER + ngram;
          features2.put(v, 1.0);
        }

        final ImmutableMap<Integer, Double> indices1 = toFeatureIndices(features1.build());
        final ImmutableMap<Integer, Double> indices2 = toFeatureIndices(features2.build());

        features.put(item, WeightedIndicesPair.from(indices1, indices2));

      }

      return this;
    }

    private ImmutableSet<String> getPOSNgrams(final EventFeatures eg) {
      final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

      final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
      final Optional<SynNodeInfo> sourceInfo = propPathSourceToRoot.get(0).node().head();

      final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();
      final Optional<SynNodeInfo> targetInfo = propPathRootToTarget.get(propPathRootToTarget.size()-1).node().head();

      if(sourceInfo.isPresent() && targetInfo.isPresent()) {
        final int sourceIndex = sourceInfo.get().getHeadTokenIndex();
        final int targetIndex = targetInfo.get().getHeadTokenIndex();

        int startIndex = 0;
        int endIndex = 0;
        if(sourceIndex < targetIndex) {
          startIndex = sourceIndex+1;
          endIndex = targetIndex-1;
        } else {
          startIndex = targetIndex+1;
          endIndex = sourceIndex-1;
        }

        if(docSentences.contains(eg.docId(), eg.sentenceIndex())) {
          final ImmutableList<WordAndPOS> tokens = docSentences.get(eg.docId(), eg.sentenceIndex()).wordAndPOS();
          if( 0<=startIndex && startIndex<tokens.size() && 0<=endIndex && endIndex<tokens.size()) {
            for(int i=startIndex; i<=(endIndex-1); i++) {
              ret.add(tokens.get(i).POS().asString() + "_" + tokens.get(i+1).POS().asString());
            }

            for(int i=startIndex; i<=(endIndex-2); i++) {
              ret.add(tokens.get(i).POS().asString() + "_" + tokens.get(i+1).POS().asString() + "_" + tokens.get(i+2).POS().asString());
            }
          }
        }
      }

      return ret.build();
    }

    private ImmutableMap<Integer, Double> toFeatureIndices(
        final ImmutableMap<String, Double> features) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for(final Map.Entry<String, Double> feature : features.entrySet()) {
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

    public POSNgrams build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new POSNgrams(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new POSNgrams(featureName, features.build(), featureIndices, -1, -1);
      }
    }




  }

}
