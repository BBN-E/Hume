package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.resolver.Resolver;
import java.util.Optional;

// +2
public final class PruneOverlappingArgumentResolver implements EventMentionResolver, Resolver {
  public final Optional<EventMention> resolve(final EventMention eventMention) {

    EventMention prunedEm = EventConsolidator.pruneOverlappingArgument(eventMention);
    return Optional.of(prunedEm);
  }

}
