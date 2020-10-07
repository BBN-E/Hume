package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

// +2
public final class KeywordEventMentionAdder implements SentenceResolver, Resolver {

  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public KeywordEventMentionAdder(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    SentenceTheory st = sentenceTheory.modifiedCopyBuilder().build();

    for(final OntologyHierarchy oh : ontologyHierarchies.values()) {
      ImmutableList<EventMention> newEms =
          EventConsolidator.addEventMentionBasedOnKeyword(oh, st);

      EventMentions.Builder emsBuilder = new EventMentions.Builder();
      emsBuilder.addAllEventMentions(st.eventMentions());
      emsBuilder.addAllEventMentions(newEms);

      final SentenceTheory.Builder stBuilder = st.modifiedCopyBuilder();
      st = stBuilder.eventMentions(emsBuilder.build()).build();
    }

    return st;
  }

}
