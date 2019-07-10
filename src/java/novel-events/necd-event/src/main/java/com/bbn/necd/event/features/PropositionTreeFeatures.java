package com.bbn.necd.event.features;

import com.bbn.bue.common.StringUtils;
import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.event.propositions.PropositionEdge;
import com.bbn.necd.event.propositions.PropositionNode;
import com.bbn.necd.event.propositions.PropositionRole;
import com.bbn.necd.event.propositions.PropositionTree;
import com.bbn.necd.event.propositions.PropositionTreeEventInstanceExtractor.PropositionTreePathFilter;
import com.bbn.necd.event.wrappers.MentionInfo;
import com.bbn.necd.event.wrappers.SynNodeInfo;
import com.bbn.nlp.WordAndPOS;
import com.bbn.nlp.languages.English;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

/**
 * Generate all kinds of proposition tree features
 */
public final class PropositionTreeFeatures {
  private static final Logger log = LoggerFactory.getLogger(PropositionTreeFeatures.class);

  public static void addFeatures(final PropositionTreeEvent eg, final EventFeatures.Builder eventFeaturesBuilder) {
    final PropositionTree tree = eg.getPropositionTree();

    final OffsetRange<CharOffset> source = OffsetRange
        .fromInclusiveEndpoints(CharOffset.asCharOffset(eg.getSourceStartOffset()),
            CharOffset.asCharOffset(eg.getSourceEndOffset()));
    final OffsetRange<CharOffset> target = OffsetRange
        .fromInclusiveEndpoints(CharOffset.asCharOffset(eg.getTargetStartOffset()),
            CharOffset.asCharOffset(eg.getTargetEndOffset()));

    eventFeaturesBuilder.withPropTreeRoot(tree.root());

    final Optional<PropositionTreePathFilter> rootToSource = tree.root().pathToMention(source, ImmutableSet.<MentionInfo>of());
    final Optional<PropositionTreePathFilter> rootToTarget = tree.root().pathToMention(target, ImmutableSet.<MentionInfo>of());

    final ImmutableList<PropositionEdge> propPathRootToSource =
        rootToSource.isPresent() ? rootToSource.get().path() : ImmutableList.<PropositionEdge>of();
    final ImmutableList<PropositionEdge> propPathRootToTarget =
        rootToTarget.isPresent() ? rootToTarget.get().path() : ImmutableList.<PropositionEdge>of();

    // these paths do not include the root node
    eventFeaturesBuilder.withPropPathRootToSource(propPathRootToSource);
    eventFeaturesBuilder.withPropPathRootToTarget(propPathRootToTarget);

    // these neighbors will include the edge leading to root. There might also be duplicates PropositionEdge
    final ImmutableList<PropositionEdge> sourceNeighbors = tree.root().getAllNeighborNodes(source);
    final ImmutableList<PropositionEdge> targetNeighbors = tree.root().getAllNeighborNodes(target);
    eventFeaturesBuilder.withSourceNeighbors(sourceNeighbors);
    eventFeaturesBuilder.withTargetNeighbors(targetNeighbors);

    final ImmutableList<ImmutableList<PropositionEdge>> pathsOfMaxLength = tree.root()
        .getAllPathsOfLength(ImmutableList.<PropositionEdge>of(),
            Math.max(propPathRootToSource.size(), propPathRootToTarget.size()));

    final ImmutableList<ImmutableList<PropositionEdge>> sourceSharedPathsFromRoot =
        findSharedPathsFromRoot(propPathRootToSource, pathsOfMaxLength);
    final ImmutableList<ImmutableList<PropositionEdge>> targetSharedPathsFromRoot =
        findSharedPathsFromRoot(propPathRootToTarget, pathsOfMaxLength);
    eventFeaturesBuilder.withSourceSharedPathsFromRoot(sourceSharedPathsFromRoot);
    eventFeaturesBuilder.withTargetSharedPathsFromRoot(targetSharedPathsFromRoot);

  }


  private static ImmutableList<ImmutableList<PropositionEdge>> findSharedPathsFromRoot(
      final ImmutableList<PropositionEdge> fromRootPath,
      ImmutableList<ImmutableList<PropositionEdge>> paths) {
    final ImmutableList.Builder<ImmutableList<PropositionEdge>> ret = ImmutableList.builder();

    for(final ImmutableList<PropositionEdge> path : paths) {
      if(pathsOverlapButDiverge(fromRootPath, path)) {
        ret.add(path);
      }
    }

    return ret.build();
  }

  // check that 2 paths start from the same point, but does indeed diverge
  private static boolean pathsOverlapButDiverge(final ImmutableList<PropositionEdge> path1, final ImmutableList<PropositionEdge> path2) {
    if(path1.size()>0 && path2.size()>0) {
      final boolean startSame = propositionEdgesAreEqual(path1.get(0), path2.get(0));
      final boolean endSame = propositionEdgesAreEqual(path1.get(path1.size()-1), path2.get(path2.size()-1));

      if(startSame) {
        if(path1.size()==path2.size()) {
          if(!endSame) {
            return true;
          } else {
            return false;
          }
        } else {
          ImmutableList<PropositionEdge> shorterPath;
          ImmutableList<PropositionEdge> longerPath;
          if(path1.size() < path2.size()) {
            shorterPath = path1;
            longerPath = path2;
          } else {
            shorterPath = path2;
            longerPath = path1;
          }
          final PropositionEdge lastEdge = shorterPath.get(shorterPath.size()-1);
          // check that this edge is not found in the longer path
          for(int i=0; i<longerPath.size(); i++) {
            if(propositionEdgesAreEqual(lastEdge, longerPath.get(i))) {
              return false;
            }
          }
          return true;
        }
      } else {
        return false;
      }
    } else {
      return false;
    }
  }

  private static boolean propositionEdgesAreEqual(final PropositionEdge edge1, final PropositionEdge edge2) {
    if(edge1.rawLabel().equalTo(edge2.rawLabel())) {
      return propositionNodesAreEqual(edge1.node(), edge2.node());
    } else {
      return false;
    }
  }

  // ideally we should have a hash function on PropositionNode, but SynNodeInfo could sometimes
  // be missing, and checking a nodes children would result in recursion.
  // also, here we are only doing 1 level deep checking of children.
  private static boolean propositionNodesAreEqual(final PropositionNode node1, final PropositionNode node2) {
    if(node1.head().isPresent() && node2.head().isPresent()) {
      return node1.head().get().equals(node2.head().get());
    } else if(node1.head().isPresent() && !node2.head().isPresent()) {
      return false;
    } else if(!node1.head().isPresent() && node2.head().isPresent()) {
      return false;
    } else {
      final ImmutableList<PropositionEdge> children1 = node1.children();
      final ImmutableList<PropositionEdge> children2 = node2.children();
      if(children1.size()==children2.size()) {
        for(int i=0; i<children1.size(); i++) {
          final PropositionEdge child1 = children1.get(i);
          final PropositionEdge child2 = children2.get(i);
          if(child1.rawLabel().equalTo(child2.rawLabel())) {
            final Optional<SynNodeInfo> head1 = child1.node().head();
            final Optional<SynNodeInfo> head2 = child2.node().head();
            if(head1.isPresent() && !head2.isPresent()) {
              return false;
            } else if(!head1.isPresent() && head2.isPresent()) {
              return false;
            } else if(head1.isPresent() && head2.isPresent()) {
              if(!head1.get().equals(head2.get())) {
                return false;
              }
            }
          } else {
            return false;
          }
        }
        return true;
      } else {
        return false;
      }
    }
  }


  public static void constructPropositionFeatures(final EventFeatures eg, final BackgroundInformation backgroundInformation) {
    // feature
    final Optional<String> sourceRole = getSourceRole(eg);  // source prop label

    // feature
    final Optional<String> targetRole = getTargetRole(eg);  // target prop label

    // feature
    // set of prop labels on path from source to target. Note this includes the prop roles directly connected to source and target.
    final ImmutableSet<String> rolesOnPath = getRolesOnPathBetweenSourceTarget(eg);

    // feature
    // sequence of intervening prop labels. Note this excludes the prop roles directly connected to source and target.
    final ImmutableList<String> interveningRoleSequenceOnPath = getInterveningRoleSequenceOnPathBetweenSourceTarget(eg);

    // sequence of (word,POS) on path from source to target. Excludes source and target themselves.
    final ImmutableList<WordAndPOS> wordPosOnPath = getWordPosOnPathSourceToTarget(eg, backgroundInformation);


    final ImmutableList<WordAndPOS> verbsOnPath = getVerbs(wordPosOnPath, backgroundInformation.getLanguage());

    // feature
    final ImmutableSet<Symbol> nonAuxiliaryVerbsOnPath = toWords(getNonAuxiliaryVerbs(verbsOnPath, backgroundInformation));

    // these are paths which start from the same root node, but diverge so it doesn't end up in the same source/target nodes
    // these paths will not include subpaths of (root-source, root,target)
    final ImmutableList<ImmutableList<PropositionEdge>> sourceSharedPathsFromRoot = eg.sourceSharedPathsFromRoot();
    final ImmutableList<ImmutableList<PropositionEdge>> targetSharedPathsFromRoot = eg.targetSharedPathsFromRoot();

    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounSourceSharedPaths = getPathsNotEndingInPronoun(sourceSharedPathsFromRoot, backgroundInformation);
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounTargetSharedPaths = getPathsNotEndingInPronoun(targetSharedPathsFromRoot, backgroundInformation);

    // feature
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounSourceSharedSUBPaths = getPathsEndingInSUB(nonPronounSourceSharedPaths);
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounSourceSharedOBJPaths = getPathsEndingInOBJ(nonPronounSourceSharedPaths);
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounSourceSharedIOBJPaths = getPathsEndingInIOBJ(nonPronounSourceSharedPaths);

    // feature
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounTargetSharedSUBPaths = getPathsEndingInSUB(nonPronounTargetSharedPaths);
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounTargetSharedOBJPaths = getPathsEndingInOBJ(nonPronounTargetSharedPaths);
    final ImmutableList<ImmutableList<PropositionEdge>> nonPronounTargetSharedIOBJPaths = getPathsEndingInIOBJ(nonPronounTargetSharedPaths);


    final ImmutableList<PropositionEdge> sourceNeighbors = eg.sourceNeighbors();
    final ImmutableList<PropositionEdge> targetNeighbors = eg.targetNeighbors();

    // feature
    final ImmutableSet<SymbolPair> sourceNeighborPropLabelAndHw = toPropLabelAndHeadword(sourceNeighbors);
    final ImmutableSet<SymbolPair> sourceNeighborPropLabelAndEntityType = toPropLabelAndEntityType(sourceNeighbors);
    final ImmutableSet<SymbolPair> sourceNeighborPropLabelAndEntitySubtype = toPropLabelAndEntitySubtype(sourceNeighbors);

    // feature
    final ImmutableSet<SymbolPair> targetNeighborPropLabelAndHw = toPropLabelAndHeadword(targetNeighbors);
    final ImmutableSet<SymbolPair> targetNeighborPropLabelAndEntityType = toPropLabelAndEntityType(targetNeighbors);
    final ImmutableSet<SymbolPair> targetNeighborPropLabelAndEntitySubtype = toPropLabelAndEntitySubtype(targetNeighbors);
  }

  public static ImmutableSet<Symbol> toWords(final ImmutableList<WordAndPOS> wordPos) {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for(final WordAndPOS wp : wordPos) {
      ret.add(wp.word());
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> toPropLabelAndHeadword(final ImmutableList<PropositionEdge> edges) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    for(final PropositionEdge edge : edges) {
      final Symbol propLabel = edge.rawLabel();
      final Symbol hw = edge.node().head().isPresent()? edge.node().head().get().getHeadWord() : ASTERISK;
      ret.add(SymbolPair.fromUnordered(propLabel, hw));
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> toPropLabelAndEntityType(final ImmutableList<PropositionEdge> edges) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    for(final PropositionEdge edge : edges) {
      final Symbol propLabel = edge.rawLabel();
      final Symbol entityType = edge.node().mention().isPresent()? edge.node().mention().get().getEntityType().name() : ASTERISK;
      ret.add(SymbolPair.fromUnordered(propLabel, entityType));
    }

    return ret.build();
  }

  public static ImmutableSet<SymbolPair> toPropLabelAndEntitySubtype(final ImmutableList<PropositionEdge> edges) {
    final ImmutableSet.Builder<SymbolPair> ret = ImmutableSet.builder();

    for(final PropositionEdge edge : edges) {
      final Symbol propLabel = edge.rawLabel();
      final Symbol entitySubtype = edge.node().mention().isPresent()? edge.node().mention().get().getEntitySubtype() : ASTERISK;
      ret.add(SymbolPair.fromUnordered(propLabel, entitySubtype));
    }

    return ret.build();
  }


  // this is more or debugging and not for features, as this is very sparse
  public static Optional<String> getWordRolePath(final PropositionNode rootNode,
      final Optional<ImmutableList<PropositionEdge>> propPathSourceToRoot,
      final Optional<ImmutableList<PropositionEdge>> propPathRootToTarget) {

    if(propPathSourceToRoot.isPresent() && propPathRootToTarget.isPresent()) {
      List<String> wordRolePath = Lists.newArrayList();

      for(final PropositionEdge edge : propPathSourceToRoot.get()) {
        final String hw = edge.node().head().isPresent()? edge.node().head().get().getHeadWord().asString() : NULL;
        final String propRole = edge.rawLabel().asString();
        wordRolePath.add(hw);
        wordRolePath.add(propRole);
      }

      final String rootHw = rootNode.head().isPresent()? rootNode.head().get().getHeadWord().asString() : NULL;
      wordRolePath.add("*"+rootHw+"*");

      for(final PropositionEdge edge : propPathRootToTarget.get()) {
        final String hw = edge.node().head().isPresent()? edge.node().head().get().getHeadWord().asString() : NULL;
        final String propRole = edge.rawLabel().asString();
        wordRolePath.add(propRole);
        wordRolePath.add(hw);
      }

      return Optional.of(StringUtils.join(wordRolePath, "_"));
    } else {
      return Optional.<String>absent();
    }
  }

  // feature. This includes the prop label directly connected to the source and target
  public static ImmutableSet<String> getRolesOnPathBetweenSourceTarget(final EventFeatures eg) {
    final ImmutableSet.Builder<String> ret = ImmutableSet.builder();

    final ImmutableList<PropositionEdge> propPathRootToSource = eg.propPathRootToSource();
    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();

    for (final PropositionEdge edge : propPathRootToSource) {
      ret.add(edge.rawLabel().asString());
    }
    for (final PropositionEdge edge : propPathRootToTarget) {
      ret.add(edge.rawLabel().asString());
    }

    return ret.build();
  }

  // the sequence of prop roles on path from source to target, excluding the roles directly connected to source and target
  public static ImmutableList<String> getInterveningRoleSequenceOnPathBetweenSourceTarget(final EventFeatures eg) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();

    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();

    for(int i=1; i<propPathSourceToRoot.size(); i++) {
      ret.add(propPathSourceToRoot.get(i).rawLabel().asString());
    }

    for(int i=0; i<(propPathRootToTarget.size()-1); i++) {
      ret.add(propPathRootToTarget.get(i).rawLabel().asString());
    }

    return ret.build();
  }

  // feature
  public static Optional<String> getSourceRole(final EventFeatures eg) {
    final ImmutableList<PropositionEdge> propPathSourceToRoot = eg.propPathRootToSource().reverse();
    if(propPathSourceToRoot.size()>0) {
      return Optional.of(propPathSourceToRoot.get(0).rawLabel().asString());
    } else {
      return Optional.absent();
    }
  }

  // feature
  public static Optional<String> getTargetRole(final EventFeatures eg) {
    final ImmutableList<PropositionEdge> propPathRootToTarget = eg.propPathRootToTarget();
    if(propPathRootToTarget.size()>0) {
      final int lastIndex = propPathRootToTarget.size()-1;
      return Optional.of(propPathRootToTarget.get(lastIndex).rawLabel().asString());
    } else {
      return Optional.absent();
    }
  }

  public static ImmutableSet<Symbol> getWordsOnPathSourceToTarget(final EventFeatures eg,
      final BackgroundInformation backgroundInformation) {
    final ImmutableSet.Builder<Symbol> ret = ImmutableSet.builder();

    for(final WordAndPOS wp : getWordPosOnPathSourceToTarget(eg, backgroundInformation)) {
      ret.add(wp.word());
    }

    return ret.build();
  }

  // this excludes the source and target themselves, i.e. just the intervening nodes in between
  public static ImmutableList<WordAndPOS> getWordPosOnPathSourceToTarget(final EventFeatures eg,
      final BackgroundInformation backgroundInformation) {
    final ImmutableList.Builder<WordAndPOS> ret = ImmutableList.builder();

    final PropositionNode rootNode = eg.propTreeRoot();
    final ImmutableList<PropositionEdge> sourcePath = eg.propPathRootToSource().reverse();
    final ImmutableList<PropositionEdge> targetPath = eg.propPathRootToTarget();

    // the first word is the source, so we skip it
    for (int i = 1; i < sourcePath.size(); i++) {
      final Optional<SynNodeInfo> synNodeInfo = sourcePath.get(i).node().head();
      if (synNodeInfo.isPresent()) {
        final Symbol hw = synNodeInfo.get().getHeadWord();
        final Symbol pos = synNodeInfo.get().getHeadPos();
        final Symbol lemma = backgroundInformation.toLemma(hw, pos);
        ret.add(WordAndPOS.fromWordThenPOS(lemma, pos));
      }
    }

    if (rootNode.head().isPresent()) {
      final Symbol hw = rootNode.head().get().getHeadWord();
      final Symbol pos = rootNode.head().get().getHeadPos();
      final Symbol lemma = backgroundInformation.toLemma(hw, pos);
      ret.add(WordAndPOS.fromWordThenPOS(lemma, pos));
    }

    // the last word is the target, so we skip it
    for (int i = 0; i < (targetPath.size() - 1); i++) {
      final Optional<SynNodeInfo> synNodeInfo = targetPath.get(i).node().head();
      if (synNodeInfo.isPresent()) {
        final Symbol hw = synNodeInfo.get().getHeadWord();
        final Symbol pos = synNodeInfo.get().getHeadPos();
        final Symbol lemma = backgroundInformation.toLemma(hw, pos);
        ret.add(WordAndPOS.fromWordThenPOS(lemma, pos));
      }
    }

    return ret.build();
  }

  // feature
  public static ImmutableList<WordAndPOS> getVerbs(
      final ImmutableList<WordAndPOS> list, final English language) {
    final ImmutableList.Builder<WordAndPOS> ret = ImmutableList.builder();

    for(final WordAndPOS wp : list) {
      final Symbol word = wp.word();
      final Symbol pos = wp.POS();
      if(language.isVerbalPOSExcludingModals(pos) && !language.wordIsCopula(word)) {
        ret.add(wp);
      }
    }

    return ret.build();
  }

  // feature
  public static ImmutableList<WordAndPOS> getNonAuxiliaryVerbs(
      final ImmutableList<WordAndPOS> list, final BackgroundInformation backgroundInformation) {
    final ImmutableList.Builder<WordAndPOS> ret = ImmutableList.builder();

    for(final WordAndPOS wp : list) {
      if(!backgroundInformation.isAuxiliaryVerb(wp.word())) {
        ret.add(wp);
      }
    }

    return ret.build();
  }


  // feature
  public static ImmutableList<ImmutableList<PropositionEdge>> getPathsEndingInSUB(
      final ImmutableList<ImmutableList<PropositionEdge>> paths) {
    final ImmutableList.Builder<ImmutableList<PropositionEdge>> ret = ImmutableList.builder();

    for (final ImmutableList<PropositionEdge> path : paths) {
      final PropositionEdge edge = path.get(path.size() - 1);
      if(edge.label().equals(PropositionRole.SUB_ROLE)) {
        ret.add(path);
      }
    }

    return ret.build();
  }

  // feature
  public static ImmutableList<ImmutableList<PropositionEdge>> getPathsEndingInOBJ(
      final ImmutableList<ImmutableList<PropositionEdge>> paths) {
    final ImmutableList.Builder<ImmutableList<PropositionEdge>> ret = ImmutableList.builder();

    for (final ImmutableList<PropositionEdge> path : paths) {
      final PropositionEdge edge = path.get(path.size() - 1);
      if(edge.label().equals(PropositionRole.OBJ_ROLE)) {
        ret.add(path);
      }
    }

    return ret.build();
  }

  // feature
  public static ImmutableList<ImmutableList<PropositionEdge>> getPathsEndingInIOBJ(
      final ImmutableList<ImmutableList<PropositionEdge>> paths) {
    final ImmutableList.Builder<ImmutableList<PropositionEdge>> ret = ImmutableList.builder();

    for (final ImmutableList<PropositionEdge> path : paths) {
      final PropositionEdge edge = path.get(path.size() - 1);
      if(edge.label().equals(PropositionRole.IOBJ_ROLE)) {
        ret.add(path);
      }
    }

    return ret.build();
  }

  // feature
  public static ImmutableList<ImmutableList<PropositionEdge>> getPathsNotEndingInPronoun(
      final ImmutableList<ImmutableList<PropositionEdge>> paths,
      final BackgroundInformation backgroundInformation) {
    final ImmutableList.Builder<ImmutableList<PropositionEdge>> ret = ImmutableList.builder();

    for (final ImmutableList<PropositionEdge> path : paths) {
      final Optional<SynNodeInfo> head = path.get(path.size() - 1).node().head();
      if (head.isPresent() && !backgroundInformation.isPronounPOS(head.get().getHeadPos())) {
        ret.add(path);
      }
    }

    return ret.build();
  }

  private final static String NULL = "NULL";
  public final static Symbol ASTERISK = Symbol.from("*");

  public final static String SOURCE = "SOURCE";
  public final static String TARGET = "TARGET";
  public final static String ARGUMENT = "ARGUMENT";
  public final static String ROOT = "ROOT";
}
