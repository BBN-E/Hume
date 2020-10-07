package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.converter.AccentKbpEventConverter;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMultimap;

// +2
public final class MapAccentEventMentionResolver implements DocumentResolver, Resolver {

  private OntologyHierarchy ontologyHierarchy;

  public MapAccentEventMentionResolver(
      OntologyHierarchy ontologyHierarchy,
      String accentEventMapFile, String cameoCodeToEventTypeFile)
  {
    this.ontologyHierarchy = ontologyHierarchy;
    assert this.ontologyHierarchy.getOntologyName().equals(OntologyHierarchy.INTERNAL_ONTOLOGY);
    AccentKbpEventConverter.readEventMappingJson(accentEventMapFile, ontologyHierarchy);
    AccentKbpEventConverter.LoadCameoCodeToEventType(cameoCodeToEventTypeFile);
  }

  public final DocTheory resolve(final DocTheory docTheory) {
    final DocTheory.Builder newDT = docTheory.modifiedCopyBuilder();
    final ImmutableMultimap<SentenceTheory, EventMention> accentEventsInDoc =
        AccentKbpEventConverter.mapAccentEventForDoc(docTheory);
    for (int i = 0; i < docTheory.numSentences(); ++i) {
      final SentenceTheory sentenceTheory = docTheory.sentenceTheory(i);
      //System.out.println("Existing number of eventmentions:" + sentenceTheory.eventMentions().size());
      EventMentions.Builder emsBuilder = new EventMentions.Builder();

      // Add in new EventMentions created from ACCENT events
      if (accentEventsInDoc.containsKey(sentenceTheory)) {
        for (final EventMention em : accentEventsInDoc.get(sentenceTheory)) {
          emsBuilder.addEventMentions(EventConsolidator.normalizeEventArguments(em));
        }
      }

      // Add in all existing EventMentions
      for (EventMention em : sentenceTheory.eventMentions()) {
        emsBuilder.addEventMentions(em);
      }

      final SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
      //System.out.println("new number of eventmentions:" +  newST.build().eventMentions().size());

      newST.eventMentions(emsBuilder.build());
      newDT.replacePrimarySentenceTheory(sentenceTheory, newST.build());
    }

    newDT.icewsEventMentions(ICEWSEventMentions.createEmpty());
    return newDT.build();
  }

}
