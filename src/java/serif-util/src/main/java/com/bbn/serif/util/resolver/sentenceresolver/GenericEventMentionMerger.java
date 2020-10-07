package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.*;
import com.bbn.serif.types.ValueType;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.Sets;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

// +2
public final class GenericEventMentionMerger implements SentenceResolver, Resolver {

  OntologyHierarchy ontologyHierarchy;

  public GenericEventMentionMerger(OntologyHierarchy oh) {
    ontologyHierarchy = oh;
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    // Builder for final set of EventMentions that will appear in the returned sentence theory
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    // Get list of event mentions to possibly merge
    ImmutableList.Builder<EventMention> emListBuilder = new ImmutableList.Builder<>();
    for (EventMention em : sentenceTheory.eventMentions()) {
      if (em.model().isPresent() && em.model().get().equalTo(Symbol.from("Generic")))
        emListBuilder.add(em);
      else
        emsBuilder.addEventMentions(em);
    }

    ImmutableList<EventMention> genericEventMentions;

    genericEventMentions =
        EventConsolidator.mergeByCoveringArguments(
            ImmutableList.copyOf(emListBuilder.build()), sentenceTheory);

    emsBuilder.addAllEventMentions(genericEventMentions);

    final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
    return stBuilder.eventMentions(emsBuilder.build()).build();
  }
}
