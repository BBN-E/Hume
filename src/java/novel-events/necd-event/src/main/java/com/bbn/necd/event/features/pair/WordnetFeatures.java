package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventPairFeatures;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;

/**
 * Created by ychan on 5/23/16.
 */
public final class WordnetFeatures extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(WordnetFeatures.class);

  private WordnetFeatures(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final int sparsityThreshold) {
    return new Builder(featureName, runningIndex, sparsityThreshold);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final int sparsityThreshold;

    private Builder(final String featureName, final int runningIndex, final int sparsityThreshold) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.existingFeatureIndices = Optional.absent();
      this.sparsityThreshold = sparsityThreshold;
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<SymbolPair, EventPairFeatures> examples) {

      final ImmutableTable.Builder<Symbol, String, Double> featuresCacheBuilder = ImmutableTable.builder();
      Set<Symbol> seenIds = Sets.newHashSet();

      for (final SymbolPair idPair : idPairs) {
        if(!examples.containsKey(idPair)) {
          log.info("Cannot find a particular idPair in examples, which is not correct");
        } else {
          final EventPairFeatures eg = examples.get(idPair);

          double wuPalmerMaxScore = 0;
          for(final Double v : eg.wuPalmerConSimCombinations()) {
            if(v.doubleValue() > wuPalmerMaxScore) {
              wuPalmerMaxScore = v.doubleValue();
            }
          }

          final String sameStem = hasTrue(eg.sameStemCombinations())? TRUE : FALSE;
          final String sameWord = hasTrue(eg.sameWordCombinations())? TRUE : FALSE;
          final String shareSynset = hasTrue(eg.shareSynsetCombinations())? TRUE : FALSE;

          final String v1 = featureName + DELIMITER + WUPALMER;
          final String v2 = featureName + DELIMITER + SAMESTEM + DELIMITER + sameStem;
          final String v3 = featureName + DELIMITER + SAMEWORD + DELIMITER + sameWord;
          final String v4 = featureName + DELIMITER + SHARESYNSET + DELIMITER + shareSynset;
          final ImmutableList<String> featureStrings = ImmutableList.<String>builder().add(v1).add(v2).add(v3).add(v4).build();
          final ImmutableList<Double> featureWeights = ImmutableList.<Double>builder().add(wuPalmerMaxScore).add(1.0).add(1.0).add(1.0).build();

          final ImmutableMap.Builder<Integer, Double> indicesBuilder = ImmutableMap.builder();
          final ImmutableMap.Builder<Integer, Double> indicesDummyBuilder = ImmutableMap.builder();

          for(int i=0; i<featureStrings.size(); i++) {
            final String v = featureStrings.get(i);
            final double w = featureWeights.get(i);

            if (existingFeatureIndices.isPresent()) {
              if (existingFeatureIndices.get().containsKey(v)) {
                final int index = existingFeatureIndices.get().get(v);
                indicesBuilder.put(index, w);
                indicesDummyBuilder.put(index, 1.0);
                featureIndices.put(v, index);
              }
            } else {
              if (featureIndices.containsKey(v)) {
                indicesBuilder.put(featureIndices.get(v), w);
                indicesDummyBuilder.put(featureIndices.get(v), 1.0);
              } else {
                indicesBuilder.put(runningIndex, w);
                indicesDummyBuilder.put(runningIndex, 1.0);
                featureIndices.put(v, runningIndex++);
              }
            }
          }
          final ImmutableMap<Integer, Double> indices = indicesBuilder.build();
          final ImmutableMap<Integer, Double> indicesDummy = indicesDummyBuilder.build();

          features.put(idPair, WeightedIndicesPair.from(indices, indicesDummy));
        }
      }

      return this;
    }

    /*
    private ImmutableMap<Integer, Double> toFeatureIndices(
        final ImmutableMap<String, Double> features, final Multiset<String> featureCounts) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for(final Map.Entry<String, Double> feature : features.entrySet()) {
        final String v = feature.getKey();
        final Double weight = feature.getValue();

        if(featureCounts.count(v) >= sparsityThreshold) {
          if(existingFeatureIndices.isPresent()) {
            if(existingFeatureIndices.get().containsKey(v)) {
              final int index = existingFeatureIndices.get().get(v);
              featureIndices.put(v, index);
              ret.put(index, weight);
            }
          } else {
            if(featureIndices.containsKey(v)) {
              ret.put(featureIndices.get(v), weight);
            } else {
              featureIndices.put(v, runningIndex);
              ret.put(runningIndex, weight);
              runningIndex++;
            }
          }
        }
      }

      return ret.build();
    }
    */

    public boolean hasTrue(final ImmutableList<Boolean> values) {
      for(final Boolean v : values) {
        if(v.booleanValue()==true) {
          return true;
        }
      }
      return false;
    }

    public WordnetFeatures build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new WordnetFeatures(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new WordnetFeatures(featureName, features.build(), featureIndices, -1, -1);
      }

    }
  }



  private final static String TRUE = "TRUE";
  private final static String FALSE = "FALSE";

  private final static String WUPALMER = "WUPALMER";
  private final static String SAMESTEM = "SAMESTEM";
  private final static String SAMEWORD = "SAMEWORD";
  private final static String SHARESYNSET = "SHARESYNSET";

}
