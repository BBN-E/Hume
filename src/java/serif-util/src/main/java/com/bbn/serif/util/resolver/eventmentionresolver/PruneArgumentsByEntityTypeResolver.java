package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.resolver.Resolver;
import java.util.Optional;

// +2
public final class PruneArgumentsByEntityTypeResolver implements EventMentionResolver, Resolver {

  public final Optional<EventMention> resolve (final EventMention eventMention) {
    return Optional.of(
        EventConsolidator.pruneEventArgumentUsingEntityTypeConstraint(eventMention));
  }

}
