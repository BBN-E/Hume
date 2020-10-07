package com.bbn.serif.util.events.consolidator.converter;

import com.bbn.serif.theories.EventMention;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Lists;

// +2
public class GenericEventConverter {
    static ImmutableSet<String> genericTypes = ImmutableSet.of("Generic","Event");

    public static boolean isGenericEvent(EventMention eventMention) {
        if(genericTypes.contains(eventMention.type().asString()))
            return true;
        else
            return false;
    }

    public static EventMention toNormalizedEventMention(EventMention eventMention) {
        if(eventMention.eventTypes().size() == 0) {
            return eventMention.modifiedCopyBuilder()
                .setEventTypes(Lists.newArrayList(EventMention.EventType.from(eventMention.type(), eventMention.score(), Optional.absent(), Optional.absent()))).build();
        } else {
            return eventMention;
        }
    }
}
