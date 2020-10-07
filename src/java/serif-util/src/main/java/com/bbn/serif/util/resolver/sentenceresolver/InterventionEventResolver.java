package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;
import com.bbn.serif.util.events.consolidator.converter.InterventionEventConverter;

import com.google.common.collect.ImmutableList;

import org.json.simple.parser.ParseException;

import java.io.IOException;

public final class InterventionEventResolver implements SentenceResolver, Resolver {
  private InterventionEventConverter interventionEventConverter;

  public InterventionEventResolver(
      OntologyHierarchy ontologyHierarchy, String interventionJsonFile)
      throws IOException, ParseException
  {
    interventionEventConverter = InterventionEventConverter
        .from(interventionJsonFile, ontologyHierarchy);

  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    EventMentions.Builder emsBuilder = new EventMentions.Builder();
    emsBuilder.addAllEventMentions(sentenceTheory.eventMentions());
    final ImmutableList<EventMention> keywordEventMentions =
        interventionEventConverter.addEventMentionsUsingKeywords(sentenceTheory);
    emsBuilder.addAllEventMentions(keywordEventMentions);

    final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
    return stBuilder.eventMentions(emsBuilder.build()).build();


  }

}
