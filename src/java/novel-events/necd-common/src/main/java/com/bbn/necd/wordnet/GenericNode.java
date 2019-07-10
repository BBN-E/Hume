package com.bbn.necd.wordnet;

import com.google.common.annotations.Beta;
import com.google.common.base.Objects;

/**
 * Represents a generic container to be used for nodes in a graph.
 */
@Beta
final public class GenericNode<T> {

  private T content;

  private GenericNode(T content) {
    this.content = content;
  }

  public static <T> GenericNode<T> from(T content) {
    return new GenericNode<>(content);
  }

  public T content() {
    return content;
  }

  public Class contentClass() {
    return content.getClass();
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;

    GenericNode that = (GenericNode) o;

    return Objects.equal(this.content, that.content);
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(content);
  }

  @Override
  public String toString() {
    return "GenericNode{" + content + "}";
  }

  public static final class Edge<V1, V2> {

    private final V1 v1;
    private final V2 v2;

    private Edge(V1 vertex1, V2 vertex2) {
      this.v1 = vertex1;
      this.v2 = vertex2;
    }

    public static <V1, V2> Edge<V1, V2> from(V1 vertex1, V2 vertex2) {
      return new Edge<>(vertex1, vertex2);
    }

    public V1 vertex1() {
      return v1;
    }

    public V2 vertex2() {
      return v2;
    }

    @Override
    public boolean equals(Object o) {
      if (this == o) return true;
      if (o == null || getClass() != o.getClass()) return false;

      Edge that = (Edge) o;

      return Objects.equal(this.v1, that.v1) &&
          Objects.equal(this.v2, that.v2);
    }

    @Override
    public int hashCode() {
      return Objects.hashCode(v1, v2);
    }

    @Override
    public String toString() {
      return "Edge{" + v1 + " : " + v2 + "}";
    }
  }
}
