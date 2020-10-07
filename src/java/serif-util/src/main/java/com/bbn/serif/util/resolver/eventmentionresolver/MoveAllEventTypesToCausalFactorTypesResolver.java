package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.collect.ImmutableList;

import java.util.Optional;

public class MoveAllEventTypesToCausalFactorTypesResolver implements Resolver,EventMentionResolver{
    @Override
    public Optional<EventMention> resolve(EventMention em) {
        EventMention.Builder newEm = em.modifiedCopyBuilder();
        newEm.setEventTypes(ImmutableList.of());
        newEm.setFactorTypes(em.eventTypes());
        return Optional.of(newEm.build());
    }
}
