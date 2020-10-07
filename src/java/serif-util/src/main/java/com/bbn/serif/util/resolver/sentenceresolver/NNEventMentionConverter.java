package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.events.consolidator.common.EventRoleConstants;
import com.bbn.serif.util.events.consolidator.common.EventTypeConstants;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.converter.NNEventConverter;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

// +2
public class NNEventMentionConverter implements SentenceResolver, Resolver {
  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public NNEventMentionConverter(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;

  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    final EventMentions.Builder emsBuilder = new EventMentions.Builder();

    for (final EventMention eventMention : sentenceTheory.eventMentions()) {
      if (eventMention.model().isPresent() &&
          eventMention.model().get().equalTo(Symbol.from("NN")))
      {
        EventMention normedEm = eventMention.modifiedCopyBuilder().build();
        for(final OntologyHierarchy oh : this.ontologyHierarchies.values()) {
          normedEm = NNEventConverter.toNormalizedEventMention(normedEm, oh);
        }

        final EventMention newEm = EventConsolidator.normalizeEventArguments(normedEm);   // this normalizes role-string, and also make sure we accept 1 argument per (role, start-char, end-char)
        final EventMention renamedEm = renameEventRole(newEm);
        final Optional<EventMention> remappedEm = EventMentionUtils
            .remapEventMentionBasedOnEntityMentions(renamedEm, sentenceTheory);    // remap Intervention type 'provide_humanitarian_resources_001' to specific Intervention types

        if(remappedEm.isPresent()) {
          EventMention prunedEm = remappedEm.get();

          for(final OntologyHierarchy oh : this.ontologyHierarchies.values()) {
            prunedEm = EventConsolidator.pruneArgumentByEventTypeRoleEntityType(EventConsolidator.pruneEventArgumentUsingEntityTypeConstraint(prunedEm), oh);
          }

          final Optional<EventMention> emBasedOnEntityMentions = EventMentionUtils.acceptEventMentionBasedOnEntityMentions(prunedEm, sentenceTheory);
          if(emBasedOnEntityMentions.isPresent()) {
            emsBuilder.addEventMentions(emBasedOnEntityMentions.get());
          }
        }
      } else {
        emsBuilder.addEventMentions(eventMention);
      }
    }

    final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
    return stBuilder.eventMentions(emsBuilder.build()).build();
  }

  private EventMention renameEventRole(final EventMention em) {
    if(em.type().asString().compareTo(EventTypeConstants.HUMAN_DISPLACEMENT)==0 || em.type().asString().compareTo(EventTypeConstants.MOVEMENT)==0) {
      final ImmutableList.Builder<EventMention.Argument> newArgs = ImmutableList.builder();

      for (final EventMention.Argument arg : em.arguments()) {
        if(arg instanceof EventMention.MentionArgument) {
          final String entityType = ((EventMention.MentionArgument) arg).mention().entityType().name().asString();
          if((entityType.compareTo("PER")==0 || entityType.compareTo("ORG")==0) && arg.role().asString().compareTo(
              EventRoleConstants.HAS_ARTIFACT)==0) {
            newArgs.add(arg.copyWithDifferentRole(Symbol.from(EventRoleConstants.HAS_ACTOR)));
          } else {
            newArgs.add(arg);
          }
        } else {
          newArgs.add(arg);
        }
      }

      return em.modifiedCopyBuilder().setArguments(newArgs.build()).build();
    } else {
      return em;
    }
  }

}
