package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.converter.GenericEventConverter;
import com.bbn.serif.util.events.consolidator.converter.KBPEventConverter;
import com.bbn.serif.util.events.consolidator.converter.NNEventConverter;
import com.bbn.serif.util.resolver.Resolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.converter.GenericEventConverter;
import com.bbn.serif.util.events.consolidator.converter.KBPEventConverter;
import com.bbn.serif.util.events.consolidator.converter.NNEventConverter;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableList;

import java.io.IOException;
import java.util.Optional;

public final class EventConfidenceCalibrationResolver implements SentenceResolver, Resolver {

    public EventConfidenceCalibrationResolver () throws IOException {
    }

    public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
        final ImmutableList<EventMention> eventMentionsWithNewScore = EventConsolidator.calibrateEventMentionConfidence(sentenceTheory);

        EventMentions.Builder emsBuilder = new EventMentions.Builder();
        emsBuilder.addAllEventMentions(eventMentionsWithNewScore);

        SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
        return newST.eventMentions(emsBuilder.build()).build();
    }

}
