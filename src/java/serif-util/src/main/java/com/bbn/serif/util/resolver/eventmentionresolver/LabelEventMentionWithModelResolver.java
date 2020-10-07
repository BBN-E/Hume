package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.converter.GenericEventConverter;
import com.bbn.serif.util.events.consolidator.converter.KBPEventConverter;
import com.bbn.serif.util.events.consolidator.converter.NNEventConverter;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMap;

import java.io.IOException;
import java.util.Optional;

// +2
public final class LabelEventMentionWithModelResolver implements EventMentionResolver, Resolver {

  public LabelEventMentionWithModelResolver (
      final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies, String kbpEventMappingFile)
      throws IOException
  {
    KBPEventConverter.loadKBPEventAndRoleMapping(kbpEventMappingFile, ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY));
  }

  public final Optional<EventMention> resolve(final EventMention eventMention) {
    EventMention.Builder emBuilder = eventMention.modifiedCopyBuilder();
    if (NNEventConverter.isNNEvent(eventMention)) {
      emBuilder.setModel(Symbol.from("NN"));
    } else if (KBPEventConverter.isKBPEvent(eventMention)) {
      emBuilder.setModel(Symbol.from("KBP"));
    } else if (GenericEventConverter.isGenericEvent(eventMention)) {
      emBuilder.setModel(Symbol.from("Generic"));
    }

    return Optional.of(emBuilder.build());
  }

}
