package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.resolver.Resolver;
import java.util.Optional;

public final class DoNothingEventMentionResolver implements EventMentionResolver, Resolver {

  public DoNothingEventMentionResolver(String someParam) {

  }

  public final Optional<EventMention> resolve(final EventMention em) {
    final EventMention.Builder newEM = em.modifiedCopyBuilder();
    return Optional.of(newEM.build());
  }
}
