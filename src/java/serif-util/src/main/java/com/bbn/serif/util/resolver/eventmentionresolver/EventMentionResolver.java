package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.serif.theories.EventMention;
import java.util.Optional;

public interface EventMentionResolver {

  Optional<EventMention> resolve(final EventMention em);

}
