package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PredictVectorManager;
import com.bbn.necd.common.theory.RealVector;
import com.bbn.necd.event.features.PropositionTreeEvent.WordPos;
import com.bbn.necd.event.formatter.StringPair;
import com.bbn.necd.event.propositions.PropositionEdge;
import com.bbn.necd.event.wrappers.SynNodeInfo;
import com.bbn.nlp.banks.wordnet.WordNetPOS;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import java.util.Map;

import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.collect.Iterables.toArray;

/**
 * Shared utilities for the feature classes.
 */
public final class FeatureUtils {

  private FeatureUtils () {
    throw new UnsupportedOperationException();
  }

  static Symbol[] symbolArray(Iterable<Symbol> symbols) {
    return toArray(checkNotNull(symbols), Symbol.class);
  }

  static Integer[] intArray(Iterable<Integer> integers) {
    return toArray(checkNotNull(integers), Integer.class);
  }

  static WordNetPOS[] wordNetPOSArray(Iterable<WordNetPOS> pos) {
    return toArray(checkNotNull(pos), WordNetPOS.class);
  }

  static WordPos[] wordPosArray(Iterable<WordPos> wordPos) {
    return toArray(checkNotNull(wordPos), WordPos.class);
  }

  public static ImmutableSet<String> getSourcePropRoles(final EventFeatures eg) {
    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();

    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();
    for(int i=1; i<propPathSourceToRoot.size(); i++) {
      ret.add(propPathSourceToRoot.get(i).rawLabel().asString());
    }

    return ret.build();
  }

  public static ImmutableSet<String> getTargetPropRoles(final EventFeatures eg) {
    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();

    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();
    for(int i=0; i<(propPathRootToTarget.size()-1); i++) {
      ret.add(propPathRootToTarget.get(i).rawLabel().asString());
    }

    return ret.build();
  }

  public static ImmutableList<String> getPropRoleSequenceSourceToRoot(final EventFeatures eg) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
    for(int i=1; i<propPathSourceToRoot.size(); i++) {
      ret.add(propPathSourceToRoot.get(i).rawLabel().asString());
    }

    return ret.build();
  }

  public static ImmutableList<String> getPropRoleSequenceRootToTarget(final EventFeatures eg) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();
    for(int i=0; i<(propPathRootToTarget.size()-1); i++) {
      ret.add(propPathRootToTarget.get(i).rawLabel().asString());
    }

    return ret.build();
  }

  public static ImmutableSet<StringPair> getSourcePropRolesWords(final EventFeatures eg) {
    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();

    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();
    for(int i=1; i<propPathSourceToRoot.size(); i++) {
      final Optional<SynNodeInfo> synNodeInfo = propPathSourceToRoot.get(i).node().head();
      if (synNodeInfo.isPresent()) {
        final Symbol hw = synNodeInfo.get().getHeadWord();
        ret.add(StringPair.fromUnordered(propPathSourceToRoot.get(i).rawLabel().asString(), hw.asString()));
      }
    }

    return ret.build();
  }

  public static ImmutableSet<StringPair> getTargetPropRolesWords(final EventFeatures eg) {
    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();

    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();
    for(int i=0; i<(propPathRootToTarget.size()-1); i++) {
      final Optional<SynNodeInfo> synNodeInfo = propPathRootToTarget.get(i).node().head();
      if (synNodeInfo.isPresent()) {
        final Symbol hw = synNodeInfo.get().getHeadWord();
        ret.add(StringPair.fromUnordered(propPathRootToTarget.get(i).rawLabel().asString(), hw.asString()));
      }
    }

    return ret.build();
  }

  public static ImmutableSet<String> getSourceWordsOnPath(final EventFeatures eg) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
    for(int i=1; i<propPathSourceToRoot.size(); i++) {
      final Optional<SynNodeInfo> synNodeInfo = propPathSourceToRoot.get(i).node().head();
      if (synNodeInfo.isPresent()) {
        ret.add(synNodeInfo.get().getHeadWord().asString());
      }
    }

    return ret.build();
  }

  public static ImmutableSet<String> getTargetWordsOnPath(final EventFeatures eg) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();
    for(int i=0; i<(propPathRootToTarget.size()-1); i++) {
      final Optional<SynNodeInfo> synNodeInfo = propPathRootToTarget.get(i).node().head();
      if (synNodeInfo.isPresent()) {
        ret.add(synNodeInfo.get().getHeadWord().asString());
      }
    }

    return ret.build();
  }

  public static ImmutableSet<String> getAllWordsOnPath(final ImmutableCollection<EventFeatures> examples) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    for(final EventFeatures eg : examples) {
      ret.addAll(getSourceWordsOnPath(eg));
      ret.addAll(getTargetWordsOnPath(eg));
    }

    return ret.build();
  }

  public static ImmutableMap<String, RealVector> toRealVectors(final ImmutableSet<String> predicates, final PredictVectorManager pvManager) {
    final ImmutableMap.Builder<String, RealVector> predicateToRealVectorBuilder =
        ImmutableMap.builder();

    for (final String predicate : predicates) {
      final Optional<PredictVectorManager.PredictVector> predictVector =
          pvManager.getVector(Symbol.from(predicate));
      if (predictVector.isPresent()) {
        final RealVector rv = RealVector.toRealVector(predictVector.get().getValues());
        predicateToRealVectorBuilder.put(predicate, rv);
      }
    }

    return predicateToRealVectorBuilder.build();
  }

  public static ImmutableMap<Integer, Double> toDummyIndices(final ImmutableMap<Integer, Double> indices) {
    final ImmutableMap.Builder<Integer, Double> ret = ImmutableMap.builder();

    for(final Map.Entry<Integer, Double> entry : indices.entrySet()) {
      ret.put(entry.getKey(), 1.0);
    }

    return ret.build();
  }

}
