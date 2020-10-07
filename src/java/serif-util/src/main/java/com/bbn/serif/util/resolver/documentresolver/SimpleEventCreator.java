package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Event;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Events;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.common.EventCandidate;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;

// +2
public final class SimpleEventCreator implements DocumentResolver, Resolver {

  public final DocTheory resolve(final DocTheory docTheory) {
    final ImmutableList.Builder<Event> newEvents = ImmutableList.builder();
    final DocTheory.Builder docBuilder = docTheory.modifiedCopyBuilder();

    for (int i = 0; i < docTheory.numSentences(); ++i) {
      final SentenceTheory st = docTheory.sentenceTheory(i);
      for (final EventMention em : st.eventMentions()) {
        final EventCandidate eCandidate =
            new EventCandidate(docTheory, em.type(), ImmutableList.of(em));
        newEvents.add(eCandidate.toEvent());
      }
    }

    docBuilder.events(new Events(newEvents.build()));
    return docBuilder.build();
  }

}
