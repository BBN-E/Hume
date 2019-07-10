package com.bbn.necd.common.theory;


import com.bbn.bue.common.symbols.Symbol;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

import static com.google.common.base.Preconditions.checkNotNull;

@JsonAutoDetect(fieldVisibility = JsonAutoDetect.Visibility.ANY, getterVisibility = JsonAutoDetect.Visibility.NONE, setterVisibility = JsonAutoDetect.Visibility.NONE)
public final class DocumentInformation {
  private final Symbol docId;
  private final ImmutableList<SentenceInformation> sentencesInformation;

  @JsonCreator
  private DocumentInformation(
      @JsonProperty("docId") Symbol docId,
      @JsonProperty("sentencesInformation") ImmutableList<SentenceInformation> sentencesInformation) {
    this.docId = checkNotNull(docId);
    this.sentencesInformation = sentencesInformation;
  }

  @JsonProperty("docId")
  public Symbol docId() {
    return docId;
  }

  @JsonProperty("sentencesInformation")
  public ImmutableList<SentenceInformation> sentencesInformation() {
    return sentencesInformation;
  }

  public int numberOfSentences() {
    return sentencesInformation.size();
  }

  public static Builder builder(final Symbol docId) {
    return new Builder(docId);
  }

  public static class Builder {
    private final Symbol docId;
    private final ImmutableMap.Builder<Integer, SentenceInformation> sentenceInformationBuilder;

    private Builder(final Symbol docId) {
      this.docId = checkNotNull(docId);
      this.sentenceInformationBuilder = ImmutableMap.builder();
    }

    public Builder withSentenceInformation(final int sentenceNum, final SentenceInformation sentenceInformation) {
      sentenceInformationBuilder.put(sentenceNum, sentenceInformation);
      return this;
    }

    public DocumentInformation build() {
      return new DocumentInformation(docId, sentenceInformationBuilder.build().values().asList());
    }
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(docId, sentencesInformation);
  }

  @Override
  public boolean equals(Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null || getClass() != obj.getClass()) {
      return false;
    }
    final DocumentInformation other = (DocumentInformation) obj;
    return Objects.equal(this.docId, other.docId) && Objects.equal(this.sentencesInformation, other.sentencesInformation);
  }


}
