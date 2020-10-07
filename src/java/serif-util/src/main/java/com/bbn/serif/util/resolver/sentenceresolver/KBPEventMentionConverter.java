package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.converter.KBPEventConverter;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMap;

import java.io.IOException;

// +2
public final class KBPEventMentionConverter implements SentenceResolver, Resolver {

  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public KBPEventMentionConverter(final ImmutableMap<String, OntologyHierarchy> oh, String kbpEventMappingFile)
      throws IOException {
    this.ontologyHierarchies = oh;
    KBPEventConverter.loadKBPEventAndRoleMapping(kbpEventMappingFile, ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY));
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    for (final EventMention eventMention : sentenceTheory.eventMentions()) {
      if (eventMention.model().isPresent() &&
          eventMention.model().get().equalTo(Symbol.from("KBP")))
      {
        for (EventMention em : KBPEventConverter
            .toNormalizedEventMention(eventMention, sentenceTheory)) {
          final EventMention normedEm = EventConsolidator.normalizeEventArguments(em);
          final EventMention prunedEm = EventConsolidator
              .pruneArgumentByEventTypeRoleEntityType(
                  EventConsolidator.pruneEventArgumentUsingEntityTypeConstraint(normedEm),
                  ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY));
          emsBuilder.addEventMentions(
              prunedEm.modifiedCopyBuilder().setScore(EventConsolidator.KBP_EVENT_SCORE).build());
        }
      } else {
        emsBuilder.addEventMentions(eventMention);
      }
    }

    final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
    return stBuilder.eventMentions(emsBuilder.build()).build();
  }
}


