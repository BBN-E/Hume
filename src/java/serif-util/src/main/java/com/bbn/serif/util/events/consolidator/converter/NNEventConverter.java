package com.bbn.serif.util.events.consolidator.converter;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;

import com.google.common.base.Optional;
import com.google.common.collect.Lists;

// +2
public class NNEventConverter {
    public static boolean isNNEvent(EventMention eventMention) {
        String eventType = eventMention.type().asString();

        if(!KBPEventConverter.isKBPEvent(eventMention) &&
                !GenericEventConverter.isGenericEvent(eventMention))
            return true;
        else
            return false;
    }

    public static EventMention toNormalizedEventMention(EventMention eventMention, final OntologyHierarchy oh) {
        // this guards against processes (e.g. LearnIt) that might not have taken care to tag on <EventMentionType> or <EventMentionFactorType>

        if(oh.getOntologyName().equals(OntologyHierarchy.INTERNAL_ONTOLOGY) && oh.isValidEventType(eventMention.type().asString()) && eventMention.eventTypes().size()==0) {
            return eventMention.modifiedCopyBuilder()
                .setEventTypes(Lists.newArrayList(EventMention.EventType.from(eventMention.type(), eventMention.score(), Optional.absent(), Optional.absent()))).build();
        } else if(oh.getOntologyName().equals(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY) && oh.isValidEventType(eventMention.type().asString()) && eventMention.factorTypes().size()==0) {
            return eventMention.modifiedCopyBuilder()
                .setFactorTypes(Lists.newArrayList(EventMention.EventType.from(eventMention.type(), eventMention.score(), Optional.absent(), Optional.absent()))).build();
        } else {
            return eventMention;
        }
    }
}
