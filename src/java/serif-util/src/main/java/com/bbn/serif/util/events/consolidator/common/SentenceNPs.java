package com.bbn.serif.util.events.consolidator.common;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.SentenceTheory;

import com.google.common.collect.ImmutableMap;

public final class SentenceNPs {
  private final ImmutableMap<Integer, NPChunks> sentenceNPs;

  private SentenceNPs(final ImmutableMap<Integer, NPChunks> sentenceNPs) {
    this.sentenceNPs = sentenceNPs;
  }

  public static SentenceNPs from(DocTheory doc) {
    final ImmutableMap.Builder<Integer, NPChunks> sentenceNPsBuilder = ImmutableMap.builder();
    for (final SentenceTheory st : doc.nonEmptySentenceTheories()) {
      final int sentenceNumber = st.sentenceNumber();
      final NPChunks np = NPChunks.create(st);
      sentenceNPsBuilder.put(sentenceNumber, np);
    }

    return new SentenceNPs(sentenceNPsBuilder.build());
  }

  public ImmutableMap<Integer, NPChunks> toMap() {
    return sentenceNPs;
  }
}
