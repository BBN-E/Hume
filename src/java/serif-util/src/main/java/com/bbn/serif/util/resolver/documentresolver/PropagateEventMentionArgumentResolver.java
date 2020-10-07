package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.resolver.Resolver;

public final class PropagateEventMentionArgumentResolver implements DocumentResolver, Resolver {

  int copyArgumentSentenceWindow;

  public PropagateEventMentionArgumentResolver(int casw) {
    copyArgumentSentenceWindow = casw;
  }

  public final DocTheory resolve(final DocTheory docTheory) {
    return EventConsolidator
        .propagateEventArgumentsAcrossSentence(docTheory, copyArgumentSentenceWindow);
  }
}
