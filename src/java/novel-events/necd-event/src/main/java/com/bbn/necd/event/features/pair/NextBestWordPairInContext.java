package com.bbn.necd.event.features.pair;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.metric.CosineSimilarity;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.common.theory.SentenceInformation;
import com.bbn.necd.common.theory.WeightedIndicesPair;
import com.bbn.necd.event.features.BackgroundInformation;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.propositions.PropositionEdge;
import com.bbn.necd.event.wrappers.SynNodeInfo;
import com.bbn.nlp.WordAndPOS;
import com.bbn.nlp.languages.English;

import com.google.common.base.Optional;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;
import com.google.common.collect.Sets;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Set;

/**
 * Created by ychan on 6/30/16.
 */
public final class NextBestWordPairInContext extends PairFeature {
  private static final Logger log = LoggerFactory.getLogger(NextBestWordPairInContext.class);

  private NextBestWordPairInContext(final String featureName,
      final ImmutableMap<SymbolPair, WeightedIndicesPair> features,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    super(featureName, features, featureIndices, startIndex, endIndex);
  }

  public static Builder builder(final String featureName, final int runningIndex,
      final PredictVectorManager pvManager,
      final BackgroundInformation backgroundInformation) {
    return new Builder(featureName, runningIndex, pvManager, backgroundInformation);
  }

  public static class Builder {
    private final String featureName;
    private int runningIndex;
    private final ImmutableMap.Builder<SymbolPair, WeightedIndicesPair> features;
    private final BiMap<String, Integer> featureIndices;
    private final PredictVectorManager pvManager;
    private Optional<ImmutableMap<String, Integer>> existingFeatureIndices;
    private final BackgroundInformation backgroundInformation;
    private final ImmutableTable<Symbol, Integer, SentenceInformation> docSentences;
    private final English language;

    private Builder(final String featureName, final int runningIndex,
        final PredictVectorManager pvManager, final BackgroundInformation backgroundInformation) {
      this.featureName = featureName;
      this.runningIndex = runningIndex;
      this.features = ImmutableMap.builder();
      this.featureIndices = HashBiMap.create();
      this.pvManager = pvManager;
      this.existingFeatureIndices = Optional.absent();
      this.backgroundInformation = backgroundInformation;
      this.docSentences = backgroundInformation.getDocSentences();
      this.language = backgroundInformation.getLanguage();
    }

    public Builder withExistingFeatureIndices(final ImmutableMap<String, Integer> existingFeatureIndices) {
      this.existingFeatureIndices = Optional.of(existingFeatureIndices);
      return this;
    }

    public Builder extractFeatures(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples) {
      // assign (running) feature indices to the embeddings
      final ImmutableList<Integer> pvIndices = getPvIndices();

      // get all predicates from all examples
      final ImmutableSet<Symbol> predicates = ImmutableSet.<Symbol>builder().addAll(getPredicates(examples.values())).addAll(getAllVerbsNounsFromLocalContext(examples.values())).build();



      // convert the predicates to embeddings vectors. We do this so that we can calculate pairwise similarity
      final ImmutableMap<Symbol, RealVector> predicateToRealVector = toRealVectors(predicates);

      // similarity between words
      Map<SymbolPair, Double> simCache = Maps.newHashMap();
      Map<Symbol, ImmutableMap<Integer, Double>> featuresCache = Maps.newHashMap();
      for (final SymbolPair item : idPairs) {
        final Symbol id1 = item.getFirstMember();
        final Symbol id2 = item.getSecondMember();

        final ImmutableSet<Symbol> words1 =
            ImmutableSet.<Symbol>builder().addAll(examples.get(id1).predicates()).build();
        final ImmutableSet<Symbol> words2 =
            ImmutableSet.<Symbol>builder().addAll(examples.get(id2).predicates()).build();

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

        // notice that this will only be true if maxWord1 and maxWord2 are in predicateToRealVector
        if (maxSim > 0) {
          final ImmutableSet<Symbol> contextWords1 = Sets.difference(getAllVerbsNounsFromLocalContext(examples.get(id1)), ImmutableSet.of(maxWord1)).immutableCopy();
          final ImmutableSet<Symbol> contextWords2 = Sets.difference(getAllVerbsNounsFromLocalContext(examples.get(id2)), ImmutableSet.of(maxWord2)).immutableCopy();

          double nextSim = 0;
          Symbol nextWord1 = null;
          Symbol nextWord2 = null;
          for (final Symbol w1 : contextWords1) {
            for (final Symbol w2 : contextWords2) {
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
                if (sim > nextSim) {
                  nextSim = sim;
                  nextWord1 = w1;
                  nextWord2 = w2;
                }
              }
            }
          }

          if(nextSim > 0) {
            // the following is just a map from feature-index to feature-value (which is a real number)
            ImmutableMap<Integer, Double> word1Features = null;
            ImmutableMap<Integer, Double> word2Features = null;

            if (featuresCache.containsKey(nextWord1)) {
              word1Features = featuresCache.get(nextWord1);
            } else {
              word1Features = toWeightedFeatures(nextWord1, pvIndices);
              featuresCache.put(nextWord1, word1Features);
            }
            if (featuresCache.containsKey(nextWord2)) {
              word2Features = featuresCache.get(nextWord2);
            } else {
              word2Features = toWeightedFeatures(nextWord2, pvIndices);
              featuresCache.put(nextWord2, word2Features);
            }

            features.put(item, WeightedIndicesPair.from(word1Features, word2Features));
          }


        }
      }

      return this;
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

    private ImmutableList<Integer> getPvIndices() {
      final ImmutableList<Symbol> pvFeatures = pvManager.getFeatureType();

      final ImmutableList.Builder<Integer> ret = ImmutableList.builder();

      if(existingFeatureIndices.isPresent()) {
        for(final Symbol type : pvFeatures) {
          // the following get(type.asString()) should not fail, as the embeddings dimensions are fixed.
          // if it fails, it means we did not train with this (i.e. existingFeatureIndices does not contain embeddings), but we tried to use it during decoding
          final int index = existingFeatureIndices.get().get(LOCAL+type.asString());
          featureIndices.put(LOCAL+type.asString(), index);
          ret.add(index);
        }
      } else {
        for (final Symbol type : pvFeatures) {
          featureIndices.put(LOCAL+type.asString(), runningIndex);
          ret.add(runningIndex++);
        }
      }

      return ret.build();
    }

    public NextBestWordPairInContext build() {
      final Set<Integer> indices = featureIndices.inverse().keySet();

      if(indices.size() > 0) {
        final int minIndex = Ordering.natural().min(indices);
        final int maxIndex = Ordering.natural().max(indices);

        return new NextBestWordPairInContext(featureName, features.build(), featureIndices, minIndex,
            maxIndex);
      } else {
        return new NextBestWordPairInContext(featureName, features.build(), featureIndices, -1, -1);
      }
    }

    public ImmutableSet<Symbol> getAllVerbsNounsFromLocalContext(final ImmutableCollection<EventFeatures> examples) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      for(final EventFeatures eg : examples) {
        ret.addAll(getAllVerbsNounsFromLocalContext(eg));
      }

      return ret.build();
    }

    public ImmutableSet<Symbol> getAllVerbsNounsFromLocalContext(final EventFeatures eg) {
      final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

      final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
      final Optional<SynNodeInfo> sourceInfo = propPathSourceToRoot.get(0).node().head();

      final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();
      final Optional<SynNodeInfo> targetInfo = propPathRootToTarget.get(propPathRootToTarget.size() - 1).node().head();

      if (sourceInfo.isPresent() && targetInfo.isPresent()) {
        final int sourceIndex = sourceInfo.get().getHeadTokenIndex();
        final int targetIndex = targetInfo.get().getHeadTokenIndex();

        int startIndex = 0;
        int endIndex = 0;
        if (sourceIndex < targetIndex) {
          startIndex = sourceIndex + 1;
          endIndex = targetIndex - 1;
        } else {
          startIndex = targetIndex + 1;
          endIndex = sourceIndex - 1;
        }

        if (docSentences.contains(eg.docId(), eg.sentenceIndex())) {
          final ImmutableList<WordAndPOS> tokens = docSentences.get(eg.docId(), eg.sentenceIndex()).wordAndPOS();

          if (0 <= startIndex && startIndex < tokens.size() && 0 <= endIndex && endIndex < tokens.size()) {

            for (int i=startIndex; i<=endIndex; i++) {
              final WordAndPOS wp = tokens.get(i);
              if(isVerbAndNonAuxiliary(wp, language, backgroundInformation) || isNominalNoun(wp)) {
                ret.add(Symbol.from(wp.word().asString().toLowerCase()));
              }
            }
          }
        }
      }

      return ret.build();
    }

  }




  public static boolean isVerb(final WordAndPOS wp, final English language) {
    final Symbol word = wp.word();
    final Symbol pos = wp.POS();
    return (language.isVerbalPOSExcludingModals(pos) && !language.wordIsCopula(Symbol.from(word.asString().toLowerCase())));
  }

  public static boolean isVerbAndNonAuxiliary(final WordAndPOS wp, final English language, final BackgroundInformation backgroundInformation) {
    return (isVerb(wp, language) && !backgroundInformation.isAuxiliaryVerb(wp.word()));
  }

  public static boolean isNominalNoun(final WordAndPOS wp) {
    return (wp.POS().equalTo(NN) || wp.POS().equalTo(NNS));
  }

  private final static Symbol NN = Symbol.from("NN");
  private final static Symbol NNS = Symbol.from("NNS");

  private final static String LOCAL = "LOCAL";
}
