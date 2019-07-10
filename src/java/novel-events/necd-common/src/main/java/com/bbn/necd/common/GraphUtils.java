package com.bbn.necd.common;

import com.google.common.annotations.Beta;
import edu.uci.ics.jung.graph.Graph;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Utility methods for working with {@link Graph}s.
 */
@Beta
public final class GraphUtils {
  public static <V> void addVertexIfNeeded(Graph<V, ?> graph, V vertex) {
    checkNotNull(graph);
    checkNotNull(vertex);
    if (!graph.containsVertex(vertex)) {
      if (!graph.addVertex(vertex)) {
        throw new GraphException("Adding vertex to the graph failed");
      }
    }
  }

  public static <V, E> void addEdgeIfNeeded(Graph<V, E> graph, E edge, V vertex1, V vertex2) {
    checkNotNull(graph);
    checkNotNull(edge);
    checkNotNull(vertex1);
    checkNotNull(vertex2);
    if (!graph.containsEdge(edge)) {
      if (!graph.addEdge(edge, vertex1, vertex2)) {
        throw new GraphException("Adding edge to the graph failed");
      }
    }
  }

  public static class GraphException extends RuntimeException {
    public GraphException(String msg) {
      super(msg);
    }
  }
}
