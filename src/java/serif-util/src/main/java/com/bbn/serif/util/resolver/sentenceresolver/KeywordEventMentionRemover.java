package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;

// +2
public final class KeywordEventMentionRemover implements SentenceResolver, Resolver {

  private final ImmutableSet<String> adverbs;
  private final ImmutableSet<String> prepositions;
  private final ImmutableSet<String> verbs;
  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public KeywordEventMentionRemover (
      final ImmutableMap<String, OntologyHierarchy> oh,
      String adverbsFile,
      String prepositionsFile,
      String verbsFile)
      throws IOException {
    this.ontologyHierarchies = oh;
    adverbs =
        ImmutableSet
            .copyOf(Files.asCharSource(new File(adverbsFile), Charsets.UTF_8).readLines());
    prepositions =
        ImmutableSet
            .copyOf(Files.asCharSource(new File(prepositionsFile), Charsets.UTF_8).readLines());
    verbs =
        ImmutableSet.copyOf(Files.asCharSource(new File(verbsFile), Charsets.UTF_8).readLines());
  }


  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    SentenceTheory st = sentenceTheory.modifiedCopyBuilder().build();

    for(final OntologyHierarchy oh : this.ontologyHierarchies.values()) {
      st = EventConsolidator.removeEventMentionBasedOnKeyword(oh, st, adverbs, prepositions, verbs);
    }

    return st;
  }


}
