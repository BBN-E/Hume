package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Ordering;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.Set;

/**
 * Created by ychan on 6/24/16.
 */
public final class ParagraphVectorFeature extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(ParagraphVectorFeature.class);

  private ParagraphVectorFeature(final String featureName,
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
    private final PredictVectorManager pvManager;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;

    private Builder(final String featureName, final int runningIndex,
        final BackgroundInformation backgroundInformation) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.pvManager = backgroundInformation.getPredictVectorManager();
      this.existingFeatureIndices = Optional.absent();
    }

    public Builder withExistingFeatureIndices(
        final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      // assign (running) feature indices to the embeddings
      final ImmutableList<Integer> pvIndices = getPvIndices();

      ImmutableMap<Symbol, ImmutableMap<Integer, Double>> idToEmbeddings = calculateIdToEmbeddings(examples.values(), pvIndices);

      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        if(idToEmbeddings.containsKey(id1) && idToEmbeddings.containsKey(id2)) {
          features.put(item, WeightedIndicesPair.from(idToEmbeddings.get(id1), idToEmbeddings.get(id2)));
        }
      }

      return this;
    }

    public ParagraphVectorFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new ParagraphVectorFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new ParagraphVectorFeature(featureName, features.build(), featureIndices, -1, -1);
      }
    }

    private ImmutableMap<Symbol, ImmutableMap<Integer, Double>> calculateIdToEmbeddings(
        final ImmutableCollection<EventFeatures> examples, final ImmutableList<Integer> pvIndices) {
      final ImmutableMap.Builder<Symbol, ImmutableMap<Integer, Double>> ret = ImmutableMap.builder();

      for(final EventFeatures example : examples) {
        double[] featureValues = new double[pvManager.getDim()];
        Arrays.fill(featureValues, 0.0);

        final Optional<PredictVectorManager.PredictVector> pv = pvManager.getVector(example.docId());
        if(pv.isPresent()) {
          final double[] values = pv.get().getValues();
          for(int i=0; i<values.length; i++) {
            featureValues[i] += values[i];
          }
        } else {
          log.info("ERROR: cannot find paragraph vector for {}", example.docId().asString());
        }

        ret.put(example.id(), toWeightedFeatures(featureValues, pvIndices));
      }

      return ret.build();
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final double[] values,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for (int i = 0; i < indices.size(); i++) {
        ret.put(indices.get(i), values[i]);
      }

      return ret.build();
    }

    private ImmutableList<Integer> getPvIndices() {
      final ImmutableList<Symbol> pvFeatures = pvManager.getFeatureType();

      final ImmutableList.Builder<Integer> ret = ImmutableList.builder();

      if(existingFeatureIndices.isPresent()) {
        for(final Symbol type : pvFeatures) {
          // the following get(type.asString()) should not fail, as the embeddings dimensions are fixed.
          // if it fails, it means we did not train with this (i.e. existingFeatureIndices does not contain embeddings), but we tried to use it during decoding
          final int index = existingFeatureIndices.get().get(PARA+type.asString());
          featureIndices.put(PARA+type.asString(), index);
          ret.add(index);
        }
      } else {
        for (final Symbol type : pvFeatures) {
          featureIndices.put(PARA+type.asString(), runningIndex);
          ret.add(runningIndex++);
        }
      }

      return ret.build();
    }


  }

  private final static String PARA = "PARA";
}
