package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.util.resolver.Resolver;

public final class DoNothingDocumentResolver implements DocumentResolver, Resolver {

  public DoNothingDocumentResolver(String someParam) {

  }

  public final DocTheory resolve(final DocTheory dt) {
    final DocTheory.Builder newDT = dt.modifiedCopyBuilder();
    return newDT.build();
  }
}
