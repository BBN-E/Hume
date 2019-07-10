package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.PropositionTreeFeatures;
import com.bbn.nlp.WordAndPOS;
import com.bbn.nlp.languages.English;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Ordering;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.Set;

/**
 * Created by ychan on 4/12/16.
 */
public final class SurroundingWordsFeature extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(SurroundingWordsFeature.class);

  private SurroundingWordsFeature(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final BackgroundInformation backgroundInformation,
      final Parameters params) {
    return new Builder(featureName, runningIndex, backgroundInformation, params);
  }

  public static class Builder {

    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private final PredictVectorManager pvManager;
    private final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final boolean useVerbs;
    private final boolean useNouns;
    //private final ImmutableSet<Symbol> eventWords;
    private final BackgroundInformation backgroundInformation;

    private Builder(final String featureName, final int runningIndex,
        final BackgroundInformation backgroundInformation,
        final Parameters params) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.pvManager = backgroundInformation.getPredictVectorManager();
      this.docSentences = backgroundInformation.getDocSentences();
      this.existingFeatureIndices = Optional.absent();
      this.useVerbs = params.getBoolean("feature.sw.useVerbs");
      this.useNouns = params.getBoolean("feature.sw.useNouns");
      //this.eventWords = backgroundInformation.getEventWords();
      this.backgroundInformation = backgroundInformation;
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

      // example id to (average) embeddings of surrounding words from surrounding sentences (-1, 0, +1 sentences)
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

    public SurroundingWordsFeature build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new SurroundingWordsFeature(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new SurroundingWordsFeature(featureName, features.build(), featureIndices, -1, -1);
      }
    }

    private ImmutableMap<Symbol, ImmutableMap<Integer, Double>> calculateIdToEmbeddings(
        final ImmutableCollection<EventFeatures> examples, final ImmutableList<Integer> pvIndices) {
      final ImmutableMap.Builder<Symbol, ImmutableMap<Integer, Double>> ret = ImmutableMap.builder();

      //final English lang = English.getInstance();

      for(final EventFeatures example : examples) {
        double[] featureValues = new double[pvManager.getDim()];
        Arrays.fill(featureValues, 0.0);
        int featureCount = 0;

        final ImmutableMultiset<Symbol> sw = getSurroundingWords(example, docSentences, backgroundInformation.getLanguage(), useVerbs, useNouns);

        for(final Symbol w : sw.elementSet()) {
          final Optional<PredictVectorManager.PredictVector> pv = pvManager.getVector(w);

          if(pv.isPresent()) {
            final double[] values = pv.get().getValues();
            for(int i=0; i<values.length; i++) {
              featureValues[i] += values[i];
            }
            featureCount += 1;
          }
        }

        if(featureCount > 0) {
          for (int i = 0; i < featureValues.length; i++) {
            featureValues[i] = featureValues[i] / (double)featureCount;
          }
        }

        if(featureCount == 0) {
          //Arrays.fill(featureValues, 0.0);
          StringBuilder sb = new StringBuilder("");
          for(final Symbol w : sw.elementSet()) {
            sb.append(" " + w.asString());
          }
          log.info("example {} SW is zeros:{}", example.id().asString(), sb.toString());
        } //else {
          // L2 normalize
          //final double dotProduct = DoubleUtils.dotProduct(featureValues, featureValues);
          //final double norm = Math.sqrt(dotProduct);
          //for(int i=0; i<featureValues.length; i++) {
          //  featureValues[i] = featureValues[i]/norm;
          //}
        //}

        ret.put(example.id(), toWeightedFeatures(featureValues, pvIndices));
      }

      return ret.build();
    }

    private ImmutableMap<Integer, Double> toWeightedFeatures(final double[] values,
        final ImmutableList<Integer> indices) {
      final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

      for (int i = 0; i < indices.size(); i++) {
        //if(values[i] < 0) {
        //  ret.put(indices.get(i), 0.0);
        //} else {
          ret.put(indices.get(i), values[i]);
        //}
      }

      return ret.build();
    }

    private ImmutableMultiset<Symbol> getSurroundingWords(final EventFeatures example,
        final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences, final English lang,
        final boolean useVerbs, final boolean useNouns) {
      final ImmutableMultiset.Builder<Symbol> ret = ImmutableMultiset.builder();

      final Symbol docId = example.docId();
      final int sentenceIndex = example.sentenceIndex();

      for(int index=(sentenceIndex-sentenceWindowSize); index<=(sentenceIndex+sentenceWindowSize); index++) {
        if(docSentences.contains(docId, index)) {
          final SentenceInformation sentInfo = docSentences.get(docId, index);
          //if(eventWords.size() > 0) {
          //  for(final WordAndPOS wordPos : sentInfo.wordAndPOS()) {
          //    if(eventWords.contains(wordPos.word())) {
          //      ret.add(wordPos.word());
          //    }
          //  }
          //}

            if (useVerbs) {
              ret.addAll(getEventiveVerbs(sentInfo, lang));
            }
            if (useNouns) {
              ret.addAll(getEventiveNouns(sentInfo, lang));
            }

        }
      }

      return ret.build();
    }

    // there are many ways to define what is an eventive verb. For the moment, we exclude modals, and exclude corpulas
    private ImmutableList<Symbol> getEventiveVerbs(final SentenceInformation sentence, final English lang) {
      final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

      final ImmutableList<WordAndPOS> verbs = PropositionTreeFeatures.getVerbs(sentence.wordAndPOS(), lang);
      final ImmutableList<WordAndPOS> nonAuxVerbs = PropositionTreeFeatures.getNonAuxiliaryVerbs(verbs, backgroundInformation);

      for(final WordAndPOS wordPos : nonAuxVerbs) {
        ret.add(wordPos.word());
      }

      return ret.build();
    }

    // ideally, we want to pre-generate a list of deverbal nouns
    private static ImmutableList<Symbol> getEventiveNouns(final SentenceInformation sentence, final English lang) {
      final ImmutableList.Builder<Symbol> ret = ImmutableList.builder();

      for(final WordAndPOS wordPos : sentence.wordAndPOS()) {
        final Symbol word = wordPos.word();
        final Symbol POS = wordPos.POS();

        if(POS.equalTo(NN) || POS.equalTo(NNS)) {
          ret.add(word);
        }
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
          final int index = existingFeatureIndices.get().get(SW+type.asString());
          featureIndices.put(SW+type.asString(), index);
          ret.add(index);
        }
      } else {
        for (final Symbol type : pvFeatures) {
          featureIndices.put(SW+type.asString(), runningIndex);
          ret.add(runningIndex++);
        }
      }

      return ret.build();
    }


  }

  private final static String SW = "SW";
  private final static Symbol NN = Symbol.from("NN");
  private final static Symbol NNS = Symbol.from("NNS");

  private final static int sentenceWindowSize = 1;
}
