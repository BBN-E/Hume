package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.EventFeatures;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 7/20/16.
 */
public final class SectorEmbeddings extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(SectorEmbeddings.class);

  private SectorEmbeddings(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final PredictVectorManager pvManager) {
    return new Builder(featureName, runningIndex, pvManager);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private final PredictVectorManager pvManager;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;

    private Builder(final String featureName, final int runningIndex,
        final PredictVectorManager pvManager) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.pvManager = pvManager;
      this.existingFeatureIndices = Optional.absent();
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      // assign (running) feature indices to the embeddings
      final ImmutableList<Integer> pvIndicesSource = getPvIndices(SS);
      final ImmutableList<Integer> pvIndicesTarget = getPvIndices(TS);

      Map<Symbol, ImmutableSet<Symbol>> egSourceSectors = Maps.newHashMap();
      Map<Symbol, ImmutableSet<Symbol>> egTargetSectors = Maps.newHashMap();
      final ImmutableSet.Builder<Symbol> allSectors = ImmutableSet.builder();
      for(final Map.Entry<Symbol, EventFeatures> entry : examples.entrySet()) {
        final Symbol id = entry.getKey();
        final ImmutableSet<Symbol> sourceSectors = toSectorHeads(entry.getValue().sourceSectors());
        final ImmutableSet<Symbol> targetSectors = toSectorHeads(entry.getValue().targetSectors());

        egSourceSectors.put(id, sourceSectors);
        egTargetSectors.put(id, targetSectors);

        allSectors.addAll(sourceSectors);
        allSectors.addAll(targetSectors);
      }

      // convert the predicates to embeddings vectors. We do this so that we can calculate pairwise similarity
      final ImmutableMap<Symbol, RealVector> predicateToRealVector = toRealVectors(allSectors.build());

      // similarity between words
      Map<SymbolPair, Double> simCache = Maps.newHashMap();
      Map<Symbol, ImmutableMap<Integer, Double>> sourceFeaturesCache = Maps.newHashMap();
      Map<Symbol, ImmutableMap<Integer, Double>> targetFeaturesCache = Maps.newHashMap();

      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        double maxSourceSim = 0;
        Symbol maxSourceWord1 = null;
        Symbol maxSourceWord2 = null;
        for (final Symbol w1 : egSourceSectors.get(id1)) {
          for (final Symbol w2 : egSourceSectors.get(id2)) {
            if (predicateToRealVector.containsKey(w1) && predicateToRealVector.containsKey(w2)) {
              double sim = 0;
              if (w1.equalTo(w2)) {
                sim = 1.0;
              } else {
                final SymbolPair wordPair = SymbolPair.from(w1, w2);
                if (simCache.containsKey(wordPair)) {
                  sim = simCache.get(wordPair);
                } else {
                  sim = CosineSimilarity
                      .similarity(predicateToRealVector.get(w1), predicateToRealVector.get(w2));
                  simCache.put(wordPair, sim);
                }
              }
              if (sim > maxSourceSim) {
                maxSourceSim = sim;
                maxSourceWord1 = w1;
                maxSourceWord2 = w2;
              }
            }
          }
        }

        double maxTargetSim = 0;
        Symbol maxTargetWord1 = null;
        Symbol maxTargetWord2 = null;
        for (final Symbol w1 : egTargetSectors.get(id1)) {
          for (final Symbol w2 : egTargetSectors.get(id2)) {
            if (predicateToRealVector.containsKey(w1) && predicateToRealVector.containsKey(w2)) {
              double sim = 0;
              if (w1.equalTo(w2)) {
                sim = 1.0;
              } else {
                final SymbolPair wordPair = SymbolPair.from(w1, w2);
                if (simCache.containsKey(wordPair)) {
                  sim = simCache.get(wordPair);
                } else {
                  sim = CosineSimilarity
                      .similarity(predicateToRealVector.get(w1), predicateToRealVector.get(w2));
                  simCache.put(wordPair, sim);
                }
              }
              if (sim > maxTargetSim) {
                maxTargetSim = sim;
                maxTargetWord1 = w1;
                maxTargetWord2 = w2;
              }
            }
          }
        }


        // notice that this will only be true if maxWord1 and maxWord2 are in predicateToRealVector
        if (maxSourceSim>0 || maxTargetSim>0) {
          final ImmutableMap.Builder<Integer, Double> indicesBuilder = ImmutableMap.builder();
          final ImmutableMap.Builder<Integer, Double> indicesDummyBuilder = ImmutableMap.builder();

          final String v1 = featureName + DELIMITER + SOURCE;
          final String v2 = featureName + DELIMITER + TARGET;
          final ImmutableList<String> featureStrings = ImmutableList.<String>builder().add(v1).add(v2).build();
          final ImmutableList<Double> featureWeights = ImmutableList.<Double>builder().add(maxSourceSim).add(maxTargetSim).build();

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

          features.put(item, WeightedIndicesPair.from(indices, indicesDummy));

          /*
          final ImmutableMap.Builder<Integer, Double> word1Features = ImmutableMap.builder();
          final ImmutableMap.Builder<Integer, Double> word2Features = ImmutableMap.builder();

          // the following is just a map from feature-index to feature-value (which is a real number)
          ImmutableMap<Integer, Double> sourceWord1Features = null;
          ImmutableMap<Integer, Double> sourceWord2Features = null;
          if(maxSourceSim > 0) {
            if (sourceFeaturesCache.containsKey(maxSourceWord1)) {
              sourceWord1Features = sourceFeaturesCache.get(maxSourceWord1);
            } else {
              sourceWord1Features = toWeightedFeatures(maxSourceWord1, pvIndicesSource);
              sourceFeaturesCache.put(maxSourceWord1, sourceWord1Features);
            }
            if (sourceFeaturesCache.containsKey(maxSourceWord2)) {
              sourceWord2Features = sourceFeaturesCache.get(maxSourceWord2);
            } else {
              sourceWord2Features = toWeightedFeatures(maxSourceWord2, pvIndicesSource);
              sourceFeaturesCache.put(maxSourceWord2, sourceWord2Features);
            }
            word1Features.putAll(sourceWord1Features);
            word2Features.putAll(sourceWord2Features);
          }

          ImmutableMap<Integer, Double> targetWord1Features = null;
          ImmutableMap<Integer, Double> targetWord2Features = null;
          if(maxTargetSim > 0) {
            if (targetFeaturesCache.containsKey(maxTargetWord1)) {
              targetWord1Features = targetFeaturesCache.get(maxTargetWord1);
            } else {
              targetWord1Features = toWeightedFeatures(maxTargetWord1, pvIndicesTarget);
              targetFeaturesCache.put(maxTargetWord1, targetWord1Features);
            }
            if (targetFeaturesCache.containsKey(maxTargetWord2)) {
              targetWord2Features = targetFeaturesCache.get(maxTargetWord2);
            } else {
              targetWord2Features = toWeightedFeatures(maxTargetWord2, pvIndicesTarget);
              targetFeaturesCache.put(maxTargetWord2, targetWord2Features);
            }
            word1Features.putAll(targetWord1Features);
            word2Features.putAll(targetWord2Features);
          }

          features.put(item, WeightedIndicesPair.from(word1Features.build(), word2Features.build()));
          */
        }
      }

      return this;
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final Symbol word,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      final double[] values = pvManager.getVector(word).get().getValues();
      for (int i = 0; i < indices.size(); i++) {
        //if(values[i] < 0) {
        //  ret.put(indices.get(i), 0.0);
        //} else {
        ret.put(indices.get(i), values[i]);
        //}
      }

      return ret.build();
    }

    private ImmutableMap<Symbol, RealVector> toRealVectors(final ImmutableSet<Symbol> predicates) {
      final ImmutableMap.Builder<Symbol, RealVector> predicateToRealVectorBuilder =
          ImmutableMap.builder();

      for (final Symbol predicate : predicates) {
        final Optional<PredictVectorManager.PredictVector> predictVector =
            pvManager.getVector(predicate);
        if (predictVector.isPresent()) {
          final RealVector rv = RealVector.toRealVector(predictVector.get().getValues());
          predicateToRealVectorBuilder.put(predicate, rv);
        }
      }

      return predicateToRealVectorBuilder.build();
    }

    private ImmutableSet<Symbol> getPredicates(final ImmutableCollection<EventFeatures> examples) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      for (final EventFeatures eg : examples) {
        ret.addAll(eg.predicates());
      }

      return ret.build();
    }

    private ImmutableList<Integer> getPvIndices(final String prefix) {
      final ImmutableList<Symbol> pvFeatures = pvManager.getFeatureType();

      final ImmutableList.Builder<Integer> ret = ImmutableList.builder();

      if(existingFeatureIndices.isPresent()) {
        for(final Symbol type : pvFeatures) {
          // the following get(type.asString()) should not fail, as the embeddings dimensions are fixed.
          // if it fails, it means we did not train with this (i.e. existingFeatureIndices does not contain embeddings), but we tried to use it during decoding
          if(!existingFeatureIndices.get().containsKey(prefix+type.asString())) {
            log.info("ERROR: existingFeatureIndices does not contain {}", prefix+type.asString());
          }
          final int index = existingFeatureIndices.get().get(prefix+type.asString());
          featureIndices.put(prefix+type.asString(), index);
          ret.add(index);
        }
      } else {
        for (final Symbol type : pvFeatures) {
          featureIndices.put(prefix+type.asString(), runningIndex);
          ret.add(runningIndex++);
        }
      }

      return ret.build();
    }

    private static ImmutableSet<Symbol> toSectorHeads(final ImmutableList<Symbol> sectors) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      for(final Symbol sector : sectors) {
        final String sectorString = sector.asString();

        if(sectorString.indexOf("/")!=-1) {
          final String[] sectorTokens = sectorString.split("/");
          for(final String sectorToken : sectorTokens) {
            final String[] tokens = StringUtils.split(
                StringUtils.removeEnd(StringUtils.removeStart(sectorToken, " "), " "), " ");
            ret.add(Symbol.from(tokens[tokens.length-1].toLowerCase()));
          }
        } else {
          final String[] tokens = StringUtils.split(sectorString, " ");
          ret.add(Symbol.from(tokens[tokens.length-1].toLowerCase()));
        }
      }

      return ret.build();
    }

    public SectorEmbeddings build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new SectorEmbeddings(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new SectorEmbeddings(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }

  private static String SS = "SS-";
  private static String TS = "TS-";
  private static String SOURCE = "SOURCE";
  private static String TARGET = "TARGET";
}
