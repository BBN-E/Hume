package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

// +2
public final class KBPEventMentionMerger implements SentenceResolver, Resolver {

  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public KBPEventMentionMerger(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    // Builder for final set of EventMentions that will appear in the returned sentence theory
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    // Get list of event mentions to possibly merge
    ImmutableList.Builder<EventMention> emListBuilder = new ImmutableList.Builder<>();
    for (EventMention em : sentenceTheory.eventMentions()) {
      if (em.model().isPresent() && em.model().get().equalTo(Symbol.from("KBP")))
        emListBuilder.add(em);
      else
        emsBuilder.addEventMentions(em);
    }

    ImmutableList<EventMention> kbpEventMentions;

    kbpEventMentions =
        EventConsolidator.mergeByCoveringArguments(
            ImmutableList.copyOf(emListBuilder.build()), sentenceTheory);

    emsBuilder.addAllEventMentions(kbpEventMentions);

    final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
    return stBuilder.eventMentions(emsBuilder.build()).build();
  }
}
