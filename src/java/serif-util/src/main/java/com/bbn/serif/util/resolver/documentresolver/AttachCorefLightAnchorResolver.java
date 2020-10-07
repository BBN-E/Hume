package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.SentenceNPs;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;

// +2
public final class AttachCorefLightAnchorResolver implements DocumentResolver, Resolver {

  ImmutableSet<String> lightWords;

  public AttachCorefLightAnchorResolver(String lightWordsFile) throws IOException {
    lightWords =
        ImmutableSet
            .copyOf(Files.asCharSource(new File(lightWordsFile), Charsets.UTF_8).readLines());
  }

  public final DocTheory resolve(final DocTheory docTheory) {

    final DocTheory.Builder newDT = docTheory.modifiedCopyBuilder();
    String docid = docTheory.docid().asString();

    final SentenceNPs sentenceNPs = SentenceNPs.from(docTheory);
    for (int i = 0; i < docTheory.numSentences(); ++i) {
      final SentenceTheory sentenceTheory = docTheory.sentenceTheory(i);
      EventMentions.Builder emsBuilder = new EventMentions.Builder();
      ImmutableList.Builder<EventMention> listBuilder = new ImmutableList.Builder<>();
      listBuilder.addAll(sentenceTheory.eventMentions());

      ImmutableList<EventMention> modifiedEventMentions =
          EventConsolidator.attachCorefLightAnchor(lightWords, listBuilder.build(), sentenceTheory, docid, sentenceNPs);
      emsBuilder.addAllEventMentions(modifiedEventMentions);

      final SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();

      newST.eventMentions(emsBuilder.build());
      newDT.replacePrimarySentenceTheory(sentenceTheory, newST.build());
    }

    return newDT.build();

  }
}

