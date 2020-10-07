package com.bbn.serif.util.resolver.sentenceresolver;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.resolver.Resolver;

public final class DoNothingSentenceResolver implements SentenceResolver, Resolver {
  public DoNothingSentenceResolver(String someParam) {

  }

  public final SentenceTheory resolve(final SentenceTheory st)
  {
    final SentenceTheory.Builder newST = st.modifiedCopyBuilder();
    return newST.build();
  }
}
