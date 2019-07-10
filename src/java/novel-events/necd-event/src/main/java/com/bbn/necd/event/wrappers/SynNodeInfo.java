package com.bbn.necd.event.wrappers;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.SynNode;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;

/**
 * Enable serialization of {@link SynNode}s.
 */
public final class SynNodeInfo {

  private final Symbol headWord;
  private final Symbol headPos;
  private final ImmutableList<Symbol> tokens;
  private final int startOffset;
  private final int endOffset;
  private final int headTokenIndex;

  private SynNodeInfo(
      @JsonProperty("headWord") final Symbol headWord,
      @JsonProperty("headPos") final Symbol headPos,
      @JsonProperty("tokens") final ImmutableList<Symbol> tokens,
      @JsonProperty("startOffset") final int startOffset,
      @JsonProperty("endOffset") final int endOffset,
      @JsonProperty("headTokenIndex") final int headTokenIndex) {
    this.headWord = headWord;
    this.headPos = headPos;
    this.tokens = tokens;
    this.startOffset = startOffset;
    this.endOffset = endOffset;
    this.headTokenIndex = headTokenIndex;
  }

  public static SynNodeInfo from(final SynNode synNode) {
    // they should be the same
    final int headStartTokenIndex = synNode.head().tokenSpan().startToken().index();
    //final int headEndTokenIndex = synNode.head().tokenSpan().endToken().index();

    return new SynNodeInfo(synNode.headWord(), synNode.headPOS(), ImmutableList.copyOf(synNode.terminalSymbols()),
        synNode.tokenSpan().startCharOffset().asInt(), synNode.tokenSpan().endCharOffset().asInt(),
        headStartTokenIndex);
  }

  public Symbol getHeadWord() {
    return headWord;
  }

  public Symbol getHeadPos() {
    return headPos;
  }

  public ImmutableList<Symbol> getTokens() {
    return tokens;
  }

  public int getStartOffset() {
    return startOffset;
  }

  public int getEndOffset() {
    return endOffset;
  }

  public int getHeadTokenIndex() {
    return headTokenIndex;
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(headWord, headPos, tokens, startOffset, endOffset, headTokenIndex);
  }

  @Override
  public boolean equals(final Object obj) {
    if(this == obj) {
      return true;
    }
    if(obj == null) {
      return false;
    }
    if(getClass() != obj.getClass()) {
      return false;
    }
    final SynNodeInfo other = (SynNodeInfo) obj;
    return Objects.equal(headWord, other.headWord) &&
        Objects.equal(headPos, other.headPos) &&
        Objects.equal(tokens, other.tokens) &&
        Objects.equal(startOffset, other.startOffset) &&
        Objects.equal(endOffset, other.endOffset) &&
        Objects.equal(headTokenIndex, other.headTokenIndex);
  }


  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("headWord", headWord)
        .add("headPos", headPos)
        .add("tokens", tokens)
        .toString();
  }
}
