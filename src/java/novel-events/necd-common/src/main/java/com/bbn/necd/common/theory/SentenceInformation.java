package com.bbn.necd.common.theory;


import com.bbn.nlp.WordAndPOS;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;

@JsonAutoDetect(fieldVisibility = JsonAutoDetect.Visibility.ANY, getterVisibility = JsonAutoDetect.Visibility.NONE, setterVisibility = JsonAutoDetect.Visibility.NONE)
public final class SentenceInformation {
  private final int sentenceNum;
  private final ImmutableList<WordAndPOS> wordAndPOS;

  @JsonCreator
  private SentenceInformation(
      @JsonProperty("sentenceNum") int sentenceNum,
      @JsonProperty("wordAndPOS") ImmutableList<WordAndPOS> wordAndPOS) {
    this.sentenceNum = sentenceNum;
    this.wordAndPOS = wordAndPOS;
  }

  @JsonProperty("sentenceNum")
  public int sentenceNum() {
    return sentenceNum;
  }

  @JsonProperty("wordAndPOS")
  public ImmutableList<WordAndPOS> wordAndPOS() {
    return wordAndPOS;
  }

  public static Builder builder(final int sentenceNum) {
    return new Builder(sentenceNum);
  }

  public static class Builder {
    private final int sentenceNum;
    private final ImmutableList.Builder<WordAndPOS> wordAndPOS;

    private Builder(final int sentenceNum) {
      this.sentenceNum = sentenceNum;
      wordAndPOS = ImmutableList.builder();
    }

    public Builder withWordAndPOS(final WordAndPOS wordAndPOS) {
      this.wordAndPOS.add(wordAndPOS);
      return this;
    }

    public Builder withWordAndPOSes(final ImmutableList<WordAndPOS> wordAndPOS) {
      this.wordAndPOS.addAll(wordAndPOS);
      return this;
    }

    public SentenceInformation build() {
      return new SentenceInformation(sentenceNum, wordAndPOS.build());
    }
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(sentenceNum, wordAndPOS);
  }

  @Override
  public boolean equals(Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null || getClass() != obj.getClass()) {
      return false;
    }
    final SentenceInformation other = (SentenceInformation) obj;
    return Objects.equal(this.sentenceNum, other.sentenceNum) && Objects.equal(this.wordAndPOS, other.wordAndPOS);
  }
}

