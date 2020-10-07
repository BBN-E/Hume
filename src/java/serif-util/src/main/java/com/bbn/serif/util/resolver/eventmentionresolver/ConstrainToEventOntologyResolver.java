package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;

import java.util.List;
import java.util.Optional;

// +2
public final class ConstrainToEventOntologyResolver implements EventMentionResolver, Resolver {

  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public ConstrainToEventOntologyResolver(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;
  }

  public final Optional<EventMention> resolve(final EventMention eventMention) {
    boolean foundEtInOntology = false;
    final String etString = eventMention.type().asString();

    for(final OntologyHierarchy oh : this.ontologyHierarchies.values()) {
      if(oh.isValidEventType(etString)) {
        foundEtInOntology = true;
        break;
      }
    }
    if(!foundEtInOntology) {
      System.out.println("ERROR: discarding event whose event_type attribute is not in ontology: " + etString);
      System.exit(1);
    }

    for(final EventMention.EventType et : eventMention.eventTypes()) {
      if(!this.ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY).isValidEventType(et.eventType().asString())) {
        System.out.println("ERROR: discarding event whose eventType is not in ontology: " + et.eventType().asString());
        System.exit(1);
      }
    }

    for(final EventMention.EventType et : eventMention.factorTypes()) {
      if(!this.ontologyHierarchies.get(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY).isValidEventType(et.eventType().asString())) {
        System.out.println("ERROR: discarding event whose factorType is not in ontology: " + et.eventType().asString());
        System.exit(1);
      }
    }

    List<EventMention.Argument> newArgs = Lists.newArrayList();
    for(final EventMention.Argument arg : eventMention.arguments()) {
      if(!ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY).isValidRole(arg.role().asString())) {
        System.out.println("ERROR: discarding event argument whose role is not in ontology: " + arg.role().asString());
        System.exit(1);
      }
      newArgs.add(arg);
    }

    EventMention.Builder newEM = eventMention.modifiedCopyBuilder();
    return Optional.of(newEM.setArguments(newArgs).build());
  }

}
