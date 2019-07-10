package com.bbn.necd.common.theory;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.PropositionUtils;
import com.bbn.necd.common.theory.PropositionConnection.PropositionInfo;
import com.bbn.nlp.languages.LanguageSpecific;
import com.bbn.serif.events.utilities.Stemmer;
import com.bbn.serif.theories.Parse;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Queue;
import java.util.Set;

public final class PropositionGraph {
  private static final Logger log = LoggerFactory.getLogger(PropositionGraph.class);

  final ImmutableMap<SynNode, PathNode> connections;
  final SentenceTheory sentenceTheory;

  private PropositionGraph(final ImmutableMap<SynNode, PathNode> connections, final SentenceTheory sentenceTheory) {
    this.sentenceTheory = sentenceTheory;
    this.connections = connections;
  }

  public SentenceTheory getSentenceTheory() {
    return sentenceTheory;
  }

  public static PropositionGraph from(final SentenceTheory st) {
    final ImmutableMap.Builder<SynNode, PathNode> ret = ImmutableMap.builder();

    final PropositionConnection connections = PropositionConnection.from(st);
    if (connections.size() == 0) {
      return new PropositionGraph(ret.build(), st);
    }

    final Parse parse = st.parse().get();

    List<PathNode> nodes = Lists.newArrayList();
    for (int i = 0; i < parse.root().numTerminals(); i++) {
      final SynNode synNode = parse.root().nthTerminal(i);
      nodes.add(PathNode.from(synNode));
    }

    for (int i = 0; (i + 1) < nodes.size(); i++) {
      final SynNode node1 = nodes.get(i).getNode();
      for (int j = (i + 1); j < nodes.size(); j++) {
        final SynNode node2 = nodes.get(j).getNode();
        final ImmutableSet<PropositionInfo> propInfos = connections.getPropInfo(node1, node2);
        for(final PropositionInfo propInfo : propInfos) {
          nodes.get(i).addNeighbor(propInfo, nodes.get(j));
          nodes.get(j).addNeighbor(propInfo, nodes.get(i));
        }
      }
    }

    for(final PathNode node : nodes) {
      ret.put(node.getNode(), node);
    }

    return new PropositionGraph(ret.build(), st);
  }

  // you might want to do various transformations on the proposition path, e.g. pathAsRoleString, pathAsRoleWordString, argRoleOnPath, pathRoles, pathWords
  public Optional<PropositionPath> getPropPath(final SynNode source, final SynNode target) {
    if(connections.containsKey(source) && connections.containsKey(target)) {
      final PathNode sourcePathNode = connections.get(source);
      final PathNode targetPathNode = connections.get(target);
      return findPropPath(sourcePathNode, targetPathNode, sentenceTheory);
    } else {
      return Optional.absent();
    }
  }

  // breadth first search for a path from source to target
  private static Optional<PropositionPath> findPropPath(final PathNode source, final PathNode target,
      final SentenceTheory sentenceTheory) {
    Queue<PathNode> Q = new LinkedList<PathNode>();
    Set<PathNode> seenNodes = new HashSet<PathNode>();
    Queue<PathSynNode> q = new LinkedList<PathSynNode>();       // to record our path traversal
    Map<PathSynNode, PathSynNode> parents = Maps.newHashMap();  // to record our path traversal
    Map<PathSynNode, Integer> nodeDepth = Maps.newHashMap();    // keeps track of the depth we are in, so we can stop exploring if we are too deep

    seenNodes.add(source);

    Q.add(source);
    q.add(PathSynNode.from(PropositionUtils.ROLE_NULL, source.getNode()));
    nodeDepth.put(q.peek(), 0);

    Optional<PathSynNode> destination = Optional.absent();      // this will be present if we can get from source to target

    while (!Q.isEmpty()) {
      final PathNode node = Q.remove();
      final PathSynNode parent = q.remove();
      final int currentDepth = nodeDepth.get(parent);

      if (node == target) {
        destination = Optional.of(parent);
        break;
      }

      if (currentDepth < maxPropPathLength) {
        for (int i = 0; i < node.numberOfNeighbor(); i++) {
          final PathNode n = node.getNeighborNode(i);
          final Symbol r = node.getNeighborRole(i);
          if (!seenNodes.contains(n)) {
            seenNodes.add(n);
            Q.add(n);

            final PathSynNode child = PathSynNode.from(r, n.getNode());
            q.add(child);
            parents.put(child, parent);
            nodeDepth.put(child, currentDepth + 1);
          }
        }
      }
    }

    if (destination.isPresent()) {
      final ImmutableList.Builder<PathSynNode> path = ImmutableList.builder();
      PathSynNode curr = destination.get();
      path.add(curr);
      while (parents.containsKey(curr)) {
        final PathSynNode p = parents.get(curr);
        curr = p;
        path.add(curr);
      }

      return Optional.of(PropositionPath.from(path.build(), sentenceTheory));
    } else {
      return Optional.absent();
    }
  }

  public Set<String> pathToVerbString(final SynNode source, final SentenceTheory st, final Stemmer stemmer) {
    final ImmutableSet.Builder<String> ret = new ImmutableSet.Builder<String>();

    final ImmutableList<PropositionPath> paths = pathToAllVerbsInSentence(source, st);
    for (final PropositionPath path : paths) {
      final int pathLength = path.length();
      if (pathLength <= 2) {
        final Optional<String> pathRoleString = path.pathAsRoleString();
        if(pathRoleString.isPresent()) {
          StringBuffer s = new StringBuffer("");
          s.append(pathRoleString);
          s.append("_");
          final SynNode node = path.getNodeByIndex(0).getNode();  // since we are going from arg to verbs, the first element is the verb
          s.append(stemmer.stem(node.headWord(), node.headPOS()).toString());
          ret.add(s.toString());
        }
      }
    }

    return ret.build();
  }

  // prop path to all verbs in sentence
  @LanguageSpecific("English")
  public ImmutableList<PropositionPath> pathToAllVerbsInSentence(final SynNode source, final SentenceTheory st) {
    final ImmutableList.Builder<PropositionPath> ret = ImmutableList.builder();

    if (st.parse().isPresent()) {
      final SynNode root = st.parse().get().root();
      for (int i = 0; i < root.numTerminals(); i++) {
        final SynNode node = root.nthTerminal(i);
        if ((node != source) && node.headPOS().toString().startsWith("VB")) {
          final Optional<PropositionPath> path = getPropPath(source, node);
          if(path.isPresent()) {
            ret.add(path.get());
          }
        }
      }
    }

    return ret.build();
  }


  public final static class PathNode {
    final SynNode node;
    List<PropositionInfo> neighborPropInfos;
    List<PathNode> neighborNodes;

    private PathNode(final SynNode node) {
      this.node = node;
      this.neighborPropInfos = Lists.newArrayList();
      this.neighborNodes = Lists.newArrayList();
    }

    public static PathNode from(final SynNode node) {
      return new PathNode(node);
    }

    public SynNode getNode() {
      return node;
    }

    public int numberOfNeighbor() {
      return neighborNodes.size();
    }

    public Symbol getNeighborRole(final int index) {
      return neighborPropInfos.get(index).getRole();
    }

    public Proposition getNeighborProp(final int index) {
      return neighborPropInfos.get(index).getProp();
    }

    public PathNode getNeighborNode(final int index) {
      return neighborNodes.get(index);
    }

    public void addNeighbor(final PropositionInfo propInfo, final PathNode neighbor) {
      neighborPropInfos.add(propInfo);
      neighborNodes.add(neighbor);
    }

    public String toString() {
      StringBuffer s = new StringBuffer("");
      s.append(node.headWord().toString());
      s.append(" |||");
      for (int i = 0; i < neighborNodes.size(); i++) {
        s.append(" ");
        s.append(neighborPropInfos.get(i).getRole().toString());
        s.append("_");
        s.append(neighborNodes.get(i).getNode().headWord().toString());
      }
      return s.toString();
    }
  }

  public final static class PathSynNode {
    private final Symbol role;
    private final SynNode node;

    private PathSynNode(final Symbol role, final SynNode node) {
      this.role = role;
      this.node = node;
    }

    public static PathSynNode from(final Symbol role, final SynNode node) {
      return new PathSynNode(transformRole(role), node);
    }

    public Symbol getRole() {
      return role;
    }

    public SynNode getNode() {
      return node;
    }

    private static Symbol transformRole(final Symbol role) {
      final String r = role.toString();
      if (r.startsWith("<") && r.endsWith(">")) {
        return role;
      } else {
        StringBuffer s = new StringBuffer("<");
        s.append(r);
        s.append(">");
        return Symbol.from(s.toString());
      }
    }
  }


  private static final int maxPropPathLength = 99;
}
