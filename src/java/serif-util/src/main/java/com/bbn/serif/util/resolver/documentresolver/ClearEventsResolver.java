package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Events;
import com.bbn.serif.util.resolver.Resolver;

// Removes the event set from a DocTheory
public final class ClearEventsResolver implements DocumentResolver, Resolver {

  public final DocTheory resolve(final DocTheory docTheory) {
    final DocTheory.Builder docBuilder = docTheory.modifiedCopyBuilder();
    docBuilder.events(Events.absent());
    return docBuilder.build();
  }
}
