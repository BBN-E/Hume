package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMap;

import java.util.Optional;

// +2
public final class GenericEventMentionConverter implements EventMentionResolver, Resolver {
  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public GenericEventMentionConverter(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;
  }

  public final Optional<EventMention> resolve(final EventMention eventMention) {
    if (eventMention.model().isPresent() &&
        eventMention.model().get().equalTo(Symbol.from("Generic")))
    {
      final EventMention em = com.bbn.serif.util.events.consolidator.converter.GenericEventConverter
          .toNormalizedEventMention(eventMention);
      final EventMention newEm = EventConsolidator.normalizeEventArguments(em);
      final EventMention prunedEm = EventConsolidator
          .pruneArgumentByEventTypeRoleEntityType(
              EventConsolidator.pruneEventArgumentUsingEntityTypeConstraint(newEm),
              ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY));
      return Optional.of(prunedEm);
    } else {
      return Optional.of(eventMention);
    }
  }
}
