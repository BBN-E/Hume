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
 * Created by ychan on 7/21/16.
 */
public final class SectorCrossEmbeddings extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(SectorCrossEmbeddings.class);

  private SectorCrossEmbeddings(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  private static class WordPairSimilarity {
    final double sim;
    final Symbol word1;
    final Symbol word2;

    public WordPairSimilarity(final double sim, final Symbol word1, final Symbol word2) {
      this.sim = sim;
      this.word1 = word1;
      this.word2 = word2;
    }

    public double getSim() {
      return sim;
    }

    public Symbol getWord1() {
      return word1;
    }

    public Symbol getWord2() {
      return word2;
    }
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

    private WordPairSimilarity calculateMostSimilarWordPair(final ImmutableSet<Symbol> words1,
        final ImmutableSet<Symbol> words2,
        final ImmutableMap<Symbol, RealVector> predicateToRealVector,
        Map<SymbolPair, Double> simCache) {

      double maxSim = 0;
      Symbol maxWord1 = null;
      Symbol maxWord2 = null;
      for (final Symbol w1 : words1) {
        for (final Symbol w2 : words2) {
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
            if (sim > maxSim) {
              maxSim = sim;
              maxWord1 = w1;
              maxWord2 = w2;
            }
          }
        }
      }

      return new WordPairSimilarity(maxSim, maxWord1, maxWord2);
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      // assign (running) feature indices to the embeddings
      final ImmutableList<Integer> pvIndices = getPvIndices(SECTOR);

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

      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        // source-source and target-target combination
        final WordPairSimilarity ssWpSim = calculateMostSimilarWordPair(egSourceSectors.get(id1),
            egSourceSectors.get(id2), predicateToRealVector, simCache);
        final WordPairSimilarity ttWpSim = calculateMostSimilarWordPair(egTargetSectors.get(id1),
            egTargetSectors.get(id2), predicateToRealVector, simCache);

        // cross combination: source-target , target-source
        final WordPairSimilarity stWpSim = calculateMostSimilarWordPair(egSourceSectors.get(id1),
            egTargetSectors.get(id2), predicateToRealVector, simCache);
        final WordPairSimilarity tsWpSim = calculateMostSimilarWordPair(egTargetSectors.get(id1),
            egSourceSectors.get(id2), predicateToRealVector, simCache);

        WordPairSimilarity wpSim1 = null;
        WordPairSimilarity wpSim2 = null;
        if( (ssWpSim.getSim()+ttWpSim.getSim()) >= (stWpSim.getSim()+tsWpSim.getSim()) ) {
          wpSim1 = ssWpSim;
          wpSim2 = ttWpSim;
        } else {
          wpSim1 = stWpSim;
          wpSim2 = tsWpSim;
        }

        if(wpSim1.getSim()>0 || wpSim2.getSim()>0) {
          final ImmutableMap.Builder<Integer, Double> indicesBuilder = ImmutableMap.builder();
          final ImmutableMap.Builder<Integer, Double> indicesDummyBuilder = ImmutableMap.builder();

          final String v1 = featureName + DELIMITER + SECTORS1;
          final String v2 = featureName + DELIMITER + SECTORS2;
          final ImmutableList<String> featureStrings = ImmutableList.<String>builder().add(v1).add(v2).build();
          final ImmutableList<Double> featureWeights = ImmutableList.<Double>builder().add(wpSim1.getSim()).add(wpSim2.getSim()).build();

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
          double[] values1Overall = new double[pvIndices.size()];
          double[] values2Overall = new double[pvIndices.size()];

          if(wpSim1.getSim()>0) {
            final double[] values1 = pvManager.getVector(wpSim1.getWord1()).get().getValues();
            final double[] values2 = pvManager.getVector(wpSim1.getWord2()).get().getValues();
            for(int i=0; i<values1.length; i++) {
              values1Overall[i] += values1[i];
            }
            for(int i=0; i<values2.length; i++) {
              values2Overall[i] += values2[i];
            }
          }

          if(wpSim2.getSim()>0) {
            final double[] values1 = pvManager.getVector(wpSim2.getWord1()).get().getValues();
            final double[] values2 = pvManager.getVector(wpSim2.getWord2()).get().getValues();
            for(int i=0; i<values1.length; i++) {
              values1Overall[i] += values1[i];
            }
            for(int i=0; i<values2.length; i++) {
              values2Overall[i] += values2[i];
            }
          }

          final double scalar = (wpSim1.getSim()>0 && wpSim2.getSim()>0)? 0.5 : 0.5;

          for(int i=0; i<values1Overall.length; i++) {
            values1Overall[i] = values1Overall[i] * scalar;
          }
          for(int i=0; i<values2Overall.length; i++) {
            values2Overall[i] = values2Overall[i] * scalar;
          }

          features.put(item, WeightedIndicesPair.from(toWeightedFeatures(values1Overall, pvIndices), toWeightedFeatures(values2Overall, pvIndices)));
          */
        }

      }

      return this;
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final double[] values,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for (int i = 0; i < indices.size(); i++) {
        ret.put(indices.get(i), values[i]);
      }

      return ret.build();
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final Symbol word,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      final double[] values = pvManager.getVector(word).get().getValues();
      for (int i = 0; i < indices.size(); i++) {
        ret.put(indices.get(i), values[i]);
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

    public SectorCrossEmbeddings build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new SectorCrossEmbeddings(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new SectorCrossEmbeddings(featureName, features.build(), featureIndices, -1, -1);
      }
    }

  }

  private static String SECTOR = "SECTOR-";
  private static String SECTORS1 = "SECTORS1";
  private static String SECTORS2 = "SECTORS2";

}
