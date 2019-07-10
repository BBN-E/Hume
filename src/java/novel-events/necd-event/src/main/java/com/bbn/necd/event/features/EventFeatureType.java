package com.bbn.necd.event.features;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.common.theory.PairFeature;
import com.bbn.necd.common.theory.SingleFeature;
import com.bbn.necd.event.features.pair.MaxSimBiPredicate;
import com.bbn.necd.event.features.pair.MaxSimBiPredicateAll;
import com.bbn.necd.event.features.pair.MaxSimOnPathFeature;
import com.bbn.necd.event.features.pair.MaxSimPredicateAll;
import com.bbn.necd.event.features.pair.MaxSimPredicateFeature;
import com.bbn.necd.event.features.pair.ParagraphVectorFeature;
import com.bbn.necd.event.features.pair.SectorCrossEmbeddings;
import com.bbn.necd.event.features.pair.SectorEmbeddings;
import com.bbn.necd.event.features.pair.SectorOverlap;
import com.bbn.necd.event.features.pair.SourceSectorPairFeature;
import com.bbn.necd.event.features.pair.SurroundingWordsFeature;
import com.bbn.necd.event.features.pair.TargetSectorPairFeature;
import com.bbn.necd.event.features.pair.WordnetFeatures;
import com.bbn.necd.event.features.single.ArgumentPropNeighborEntityType;
import com.bbn.necd.event.features.single.ArgumentPropNeighborHw;
import com.bbn.necd.event.features.single.ArgumentSectors;
import com.bbn.necd.event.features.single.DirectPropRole;
import com.bbn.necd.event.features.single.PredicatesFeature;
import com.bbn.necd.event.features.single.PropRoleSequenceOnPath;
import com.bbn.necd.event.features.single.PropRoleSequencePattern;
import com.bbn.necd.event.features.single.PropRolesOnPath;
import com.bbn.necd.event.features.single.WordsOnPath;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;


public final class EventFeatureType {

  // the user can specify what particular feature types to extract
  public enum ExtractPairFeatureType {
    SECTOR_OVERLAP {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final SectorOverlap.Builder featureBuilder = SectorOverlap
            .builder(SECTOR_OVERLAP.name(), runningIndex,
                sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, eventPairFeatures).build();
      }
    }, SECTOR_EMBEDDINGS {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final SectorEmbeddings.Builder featureBuilder = SectorEmbeddings
            .builder(SECTOR_EMBEDDINGS.name(), runningIndex,
                backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, SECTOR_CROSS_EMBEDDINGS {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final SectorCrossEmbeddings.Builder featureBuilder = SectorCrossEmbeddings
            .builder(SECTOR_CROSS_EMBEDDINGS.name(), runningIndex,
                backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, WORDNET_FEATURES {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final WordnetFeatures.Builder featureBuilder = WordnetFeatures
            .builder(WORDNET_FEATURES.name(), runningIndex,
                sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, eventPairFeatures).build();
      }
    }, SURROUNDING_WORDS {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final SurroundingWordsFeature.Builder featureBuilder = SurroundingWordsFeature
            .builder(SURROUNDING_WORDS.name(), runningIndex,
                backgroundInformation, params);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, PARAGRAPH_VECTOR_FEATURE {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final ParagraphVectorFeature.Builder featureBuilder = ParagraphVectorFeature
            .builder(PARAGRAPH_VECTOR_FEATURE.name(), runningIndex,
                backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, MAXSIM_ONPATH {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final MaxSimOnPathFeature.Builder featureBuilder = MaxSimOnPathFeature
            .builder(MAXSIM_ONPATH.name(), runningIndex,
                backgroundInformation.getPredictVectorManager(), backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, MAXSIM_PREDICATE_PAIR {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final MaxSimPredicateFeature.Builder featureBuilder = MaxSimPredicateFeature
            .builder(MAXSIM_PREDICATE_PAIR.name(), runningIndex,
                backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, MAXSIM_BI_PREDICATE {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final MaxSimBiPredicate.Builder featureBuilder = MaxSimBiPredicate
            .builder(MAXSIM_BI_PREDICATE.name(), runningIndex,
                backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, MAXSIM_PREDICATE_ALL {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final MaxSimPredicateAll.Builder featureBuilder = MaxSimPredicateAll
            .builder(MAXSIM_PREDICATE_ALL.name(), runningIndex,
                backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, MAXSIM_BI_PREDICATE_ALL {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final MaxSimBiPredicateAll.Builder featureBuilder = MaxSimBiPredicateAll
            .builder(MAXSIM_BI_PREDICATE_ALL.name(), runningIndex,
                backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, SOURCE_SECTOR_PAIR {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final SourceSectorPairFeature.Builder featureBuilder = SourceSectorPairFeature
            .builder(SOURCE_SECTOR_PAIR.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, TARGET_SECTOR_PAIR {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final TargetSectorPairFeature.Builder featureBuilder = TargetSectorPairFeature
            .builder(TARGET_SECTOR_PAIR.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, ARGUMENT_SECTORS {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.ArgumentSectors.Builder featureBuilder = com.bbn.necd.event.features.pair.ArgumentSectors
            .builder(ARGUMENT_SECTORS.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, ARGUMENT_PROPNEIGHBOR_ENTITY_TYPE {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.ArgumentPropNeighborEntityType.Builder featureBuilder = com.bbn.necd.event.features.pair.ArgumentPropNeighborEntityType
            .builder(ARGUMENT_PROPNEIGHBOR_ENTITY_TYPE.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, ARGUMENT_PROPNEIGHBOR_HW {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.ArgumentPropNeighborHw.Builder featureBuilder = com.bbn.necd.event.features.pair.ArgumentPropNeighborHw
            .builder(ARGUMENT_PROPNEIGHBOR_HW.name(), runningIndex, sparsityThreshold, backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, DIRECT_PROPROLE {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.DirectPropRole.Builder featureBuilder = com.bbn.necd.event.features.pair.DirectPropRole
            .builder(DIRECT_PROPROLE.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, PROPROLE_SEQUENCE_ONPATH {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.PropRoleSequenceOnPath.Builder featureBuilder = com.bbn.necd.event.features.pair.PropRoleSequenceOnPath
            .builder(PROPROLE_SEQUENCE_ONPATH.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, PROPROLE_SEQUENCE_PATTERN {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.PropRoleSequencePattern.Builder featureBuilder = com.bbn.necd.event.features.pair.PropRoleSequencePattern
            .builder(PROPROLE_SEQUENCE_PATTERN.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, PROPROLES_ON_PATH {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.PropRolesOnPath.Builder featureBuilder = com.bbn.necd.event.features.pair.PropRolesOnPath
            .builder(PROPROLES_ON_PATH.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, WORDS_ON_PATH {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.WordsOnPath.Builder featureBuilder = com.bbn.necd.event.features.pair.WordsOnPath
            .builder(WORDS_ON_PATH.name(), runningIndex, sparsityThreshold, backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, TEXTGRAPH_EDGE {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.TextGraphEdgeFeature.Builder featureBuilder = com.bbn.necd.event.features.pair.TextGraphEdgeFeature
            .builder(TEXTGRAPH_EDGE.name(), runningIndex);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, TEXTGRAPH_EDGEWORD {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.TextGraphEdgeWordFeature.Builder featureBuilder = com.bbn.necd.event.features.pair.TextGraphEdgeWordFeature
            .builder(TEXTGRAPH_EDGEWORD.name(), runningIndex, backgroundInformation.getPredictVectorManager());

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, NEXTBEST_WORDPAIR_IN_CONTEXT {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.NextBestWordPairInContext.Builder featureBuilder = com.bbn.necd.event.features.pair.NextBestWordPairInContext
            .builder(NEXTBEST_WORDPAIR_IN_CONTEXT.name(), runningIndex, backgroundInformation.getPredictVectorManager(), backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    }, POS_NGRAMS {
      @Override
      public PairFeature from(final ImmutableList<SymbolPair> idPairs,
          final ImmutableMap<Symbol, EventFeatures> examples,
          final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
          final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final com.bbn.necd.event.features.pair.POSNgrams.Builder featureBuilder = com.bbn.necd.event.features.pair.POSNgrams
            .builder(POS_NGRAMS.name(), runningIndex, backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(idPairs, examples).build();
      }
    };


    public abstract PairFeature from(final ImmutableList<SymbolPair> idPairs,
        final ImmutableMap<Symbol, EventFeatures> examples,
        final ImmutableMap<SymbolPair, EventPairFeatures> eventPairFeatures,
        final int runningIndex,
        final BackgroundInformation backgroundInformation, final int sparsityThreshold,
        final Optional<ImmutableMap<String, Integer>> featureIndices,
        final Parameters params);
  }

  public enum ExtractSingleFeatureType {

    PREDICATES {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final PredicatesFeature.Builder featureBuilder = PredicatesFeature
            .builder(PREDICATES.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, ARGUMENT_SECTORS {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final ArgumentSectors.Builder featureBuilder = ArgumentSectors
            .builder(ARGUMENT_SECTORS.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, ARGUMENT_PROPNEIGHBOR_ENTITY_TYPE {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final ArgumentPropNeighborEntityType.Builder featureBuilder = ArgumentPropNeighborEntityType
            .builder(ARGUMENT_PROPNEIGHBOR_ENTITY_TYPE.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, ARGUMENT_PROPNEIGHBOR_HW {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final ArgumentPropNeighborHw.Builder featureBuilder = ArgumentPropNeighborHw
            .builder(ARGUMENT_PROPNEIGHBOR_HW.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, DIRECT_PROPROLE {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final DirectPropRole.Builder featureBuilder = DirectPropRole
            .builder(DIRECT_PROPROLE.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, PROPROLE_SEQUENCE_ONPATH {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final PropRoleSequenceOnPath.Builder featureBuilder = PropRoleSequenceOnPath
            .builder(PROPROLE_SEQUENCE_ONPATH.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, PROPROLE_SEQUENCE_PATTERN {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final PropRoleSequencePattern.Builder featureBuilder = PropRoleSequencePattern
            .builder(PROPROLE_SEQUENCE_PATTERN.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, PROPROLES_ON_PATH {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final PropRolesOnPath.Builder featureBuilder = PropRolesOnPath
            .builder(PROPROLES_ON_PATH.name(), runningIndex, sparsityThreshold);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    }, WORDS_ON_PATH {
      @Override
      public SingleFeature from(final ImmutableList<Symbol> ids,
          final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
          final BackgroundInformation backgroundInformation, final int sparsityThreshold,
          final Optional<ImmutableMap<String, Integer>> featureIndices,
          final Parameters params) {

        final WordsOnPath.Builder featureBuilder = WordsOnPath
            .builder(WORDS_ON_PATH.name(), runningIndex, sparsityThreshold, backgroundInformation);

        if (featureIndices.isPresent()) {
          featureBuilder.withExistingFeatureIndices(featureIndices.get());
        }

        return featureBuilder.extractFeatures(ids, examples).build();
      }
    };

    public abstract SingleFeature from(final ImmutableList<Symbol> idss,
        final ImmutableMap<Symbol, EventFeatures> examples, final int runningIndex,
        final BackgroundInformation backgroundInformation, final int sparsityThreshold,
        final Optional<ImmutableMap<String, Integer>> featureIndices,
        final Parameters params);
  }

  // the user can detect whether an instance has a particular feature type
  public enum HasFeatureType {

    PREDICATES {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.predicates().size() > 0;
      }
    }, STEMS {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.stems().size() > 0;
      }
    }, POS {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.pos().size() > 0;
      }
    }, SOURCE_SECTORS {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.sourceSectors().size() > 0;
      }
    }, TARGET_SECTORS {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.targetSectors().size() > 0;
      }
    }, SOURCE_TOKENS {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.sourceTokens().size() > 0;
      }
    }, TARGET_TOKENS {
      @Override
      public boolean hasValue(final EventFeatures eg) {
        return eg.targetTokens().size() > 0;
      }
    };

    public abstract boolean hasValue(final EventFeatures eg);
  }


}
