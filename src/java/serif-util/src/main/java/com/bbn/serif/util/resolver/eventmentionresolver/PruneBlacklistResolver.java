package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;

import java.util.Optional;
import java.util.List;
import java.util.ArrayList;

// +2
public final class PruneBlacklistResolver implements EventMentionResolver, Resolver {
  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public PruneBlacklistResolver(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;
  }

  // if an EventMention has multiple <EventMentionType> , e.g. "Attack" and "Injure",
  // and assuming that a blacklist pair is (eventType="Attack", anchorText="shout"),
  // we could choose to just drop "Attack", leaving a single <EventMentionType>="Injure".
  // Or we could drop the entire EventMention. I'll drop the entire EventMention in this code.
  public final Optional<EventMention> resolve(final EventMention eventMention) {
    final String emText = eventMention.anchorNode().span().text().toString();
    final String emHeadText = eventMention.anchorNode().head().span().text().toString();

    List<EventMention.EventType> eventTypes = Lists.newArrayList();
    List<EventMention.EventType> factorTypes = Lists.newArrayList();

    if(this.ontologyHierarchies.containsKey(OntologyHierarchy.INTERNAL_ONTOLOGY)) {
      final OntologyHierarchy oh = this.ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY);
      for(final EventMention.EventType et : eventMention.eventTypes()) {
        if (!oh.isInBlackList(et.eventType().asString(), emText) && !oh.isInBlackList(et.eventType().asString(), emHeadText)) {
          eventTypes.add(et);
        }
      }
    } else {
      for(final EventMention.EventType et : eventMention.eventTypes()) {
        eventTypes.add(et);
      }
    }

    if(this.ontologyHierarchies.containsKey(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY)) {
      final OntologyHierarchy oh = this.ontologyHierarchies.get(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY);
      for(final EventMention.EventType et : eventMention.factorTypes()) {
        if (!oh.isInBlackList(et.eventType().asString(), emText) && !oh.isInBlackList(et.eventType().asString(), emHeadText)) {
          factorTypes.add(et);
        }
      }
    } else {
      for(final EventMention.EventType et : eventMention.factorTypes()) {
        factorTypes.add(et);
      }
    }

    if(eventTypes.size() >= 1) {
      return Optional.of(eventMention.modifiedCopyBuilder().setType(eventTypes.get(0).eventType()).setEventTypes(eventTypes).setFactorTypes(factorTypes).build());
    } else if(factorTypes.size() >= 1) {
      return Optional.of(eventMention.modifiedCopyBuilder().setType(factorTypes.get(0).eventType()).setEventTypes(eventTypes).setFactorTypes(factorTypes).build());
    } else {
      return Optional.empty();
    }

  }
}
