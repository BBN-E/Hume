package com.bbn.necd.wordnet;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.GraphUtils;
import com.bbn.nlp.banks.wordnet.IWordNet;
import com.bbn.nlp.banks.wordnet.WordNetPOS;
import com.bbn.nlp.banks.wordnet.WordNetSynset;
import com.google.common.annotations.Beta;
import com.google.common.base.MoreObjects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Queues;
import edu.uci.ics.jung.algorithms.shortestpath.DijkstraShortestPath;
import edu.uci.ics.jung.graph.DirectedGraph;
import edu.uci.ics.jung.graph.DirectedSparseGraph;

import java.util.Deque;
import java.util.List;

import static com.bbn.necd.common.GraphUtils.addEdgeIfNeeded;
import static com.bbn.necd.common.GraphUtils.addVertexIfNeeded;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Operations on WordNet as as graph.
 */
@Beta
final class WordNetGraph {

  private static final String ROOT_LABEL = "ROOT_VERTEX";
  private final IWordNet wn;
  private final WordNetPOS pos;
  private final GenericNode<String> rootVertex;
  private final DirectedGraph<GenericNode, GenericNode.Edge> graph;
  private final DijkstraShortestPath<GenericNode, GenericNode.Edge> pathFinder;
  private final int height;

  private WordNetGraph(final IWordNet wordNet, final WordNetPOS pos) {
    this.wn = wordNet;
    this.pos = pos;
    rootVertex = GenericNode.from(ROOT_LABEL);
    graph = new DirectedSparseGraph<>();
    addHypernymVertices();
    pathFinder = new DijkstraShortestPath<>(graph);
    height = computeHeight();
  }

  static WordNetGraph fromWordNet(final IWordNet wordNet, final WordNetPOS pos) {
    return new WordNetGraph(checkNotNull(wordNet), checkNotNull(pos));
  }

  public int height() {
    return height;
  }

  public <V1, V2> Optional<Integer> shortestDistance(V1 item1, V2 item2) {
    GenericNode<V1> vertex1 = GenericNode.from(item1);
    GenericNode<V2> vertex2 = GenericNode.from(item2);
    checkArgument(graph.containsVertex(vertex1), "item1 not found in graph");
    checkArgument(graph.containsVertex(vertex2), "item2 not found in graph");
    List<GenericNode.Edge> path = pathFinder.getPath(vertex1, vertex2);
    if (path.isEmpty()) {
      return Optional.absent();
    } else {
      return Optional.of(path.size());
    }
  }

  public <V1> Optional<Integer> shortestDistanceToRoot(V1 item) {
    return shortestDistance(item, ROOT_LABEL);
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this).add("pos", pos).add("height", height).toString();
  }

  private void addHypernymVertices() {
    // Create graph and add root node to it
    addVertexIfNeeded(graph, rootVertex);

    // Add all stems and their hypernyms to it
    for (final Symbol stem : wn.getAllStemsForPos(pos)) {
      // Add stem
      final GenericNode<Symbol> stemNode = GenericNode.from(stem);
      addVertexIfNeeded(graph, stemNode);
      for (WordNetSynset synset : wn.getAllSynsetsOfStem(stem, pos)) {
        // Add synset and edge between stem and synset
        final GenericNode<WordNetSynset> synsetNode = GenericNode.from(synset);
        addVertexIfNeeded(graph, synsetNode);
        final GenericNode.Edge stemSynsetEdge = GenericNode.Edge.from(stemNode, synsetNode);
        addEdgeIfNeeded(graph, stemSynsetEdge, stemNode, synsetNode);

        // Add hypernyms for this synset
        addHypernymVertices(synsetNode);
      }
    }
  }

  private void addHypernymVertices(final GenericNode<WordNetSynset> baseVertex) {
    final Deque<GenericNode<WordNetSynset>> synsetVertices = Queues.newArrayDeque();
    synsetVertices.add(baseVertex);
    while (!synsetVertices.isEmpty()) {
      final GenericNode<WordNetSynset> synsetVertex = synsetVertices.pop();
      ImmutableList<WordNetSynset> hypernyms = wn.getHypernymsOfSynset(synsetVertex.content());
      // Base case, add edge to root
      if (hypernyms.isEmpty()) {
        final GenericNode.Edge rootEdge = GenericNode.Edge.from(synsetVertex, rootVertex);
        addEdgeIfNeeded(graph, rootEdge, synsetVertex, rootVertex);
      } else {
        for (final WordNetSynset synset : hypernyms) {
          final GenericNode<WordNetSynset> newVertex = GenericNode.from(synset);
          addVertexIfNeeded(graph, newVertex);
          // Add the upward edge
          final GenericNode.Edge newEdge = GenericNode.Edge.from(synsetVertex, newVertex);
          addEdgeIfNeeded(graph, newEdge, synsetVertex, newVertex);
          // Add the new vertex to the deque
          synsetVertices.add(newVertex);
        }
      }
    }
  }

  private int computeHeight() {
    int height = 0;

    for (WordNetSynset synset : wn.getAllSynsetsForPos(pos)) {
      Optional<Integer> optPathLength = shortestDistanceToRoot(synset);
      if (optPathLength.isPresent()) {
        if (optPathLength.get() > height) {
          height = optPathLength.get();
        }
      } else {
        throw new GraphUtils.GraphException(String.format("No path from synset '%s' to root", synset));
      }
    }
    return height;
  }
}
