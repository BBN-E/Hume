package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.resolver.Resolver;
import com.bbn.serif.types.Trend;
import java.util.*;


// Simply makes sure the EventMention's type is represented as a child EventMention.EventType object

public class EventMentionTypeResolver implements Resolver, EventMentionResolver {
    @Override
    public java.util.Optional<EventMention> resolve(EventMention em) {
        Symbol eventType = em.type();
        boolean found = false;
        for (EventMention.EventType et : em.eventTypes()) {
            if (et.eventType() == eventType) {
                found = true;
                break;
            }
        }
        if (!found) {
            com.google.common.base.Optional<Double> e = com.google.common.base.Optional.absent();
            com.google.common.base.Optional<Trend> t = com.google.common.base.Optional.absent();
            em.eventTypes().add(EventMention.EventType.from(eventType, 0.0, e, t));
        }
        return Optional.of(em);
    }
}
