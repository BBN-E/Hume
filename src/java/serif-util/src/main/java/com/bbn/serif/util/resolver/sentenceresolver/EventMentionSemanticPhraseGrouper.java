package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.proputil.PropositionUtils;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;

// +2
public final class EventMentionSemanticPhraseGrouper implements SentenceResolver, Resolver {

  ImmutableSet<String> lightVerbs;

  public EventMentionSemanticPhraseGrouper(String lightVerbsFile) throws IOException {
    lightVerbs =
        ImmutableSet
            .copyOf(Files.asCharSource(new File(lightVerbsFile), Charsets.UTF_8).readLines());
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    final List<PropositionUtils.PathNode> graph =
        PropositionUtils.constructPropositionGraph(sentenceTheory);
    final Map<SynNode, PropositionUtils.PathNode> synToPathNodes =
        PropositionUtils.mapSynNodeToPathNode(graph);

    ImmutableList.Builder<EventMention> listBuilder = ImmutableList.builder();
    listBuilder.addAll(sentenceTheory.eventMentions());

    final ImmutableList<EventMention> eventMentionsConsolidatedViaSemanticPhrase = EventConsolidator
        .groupEventMentionsBySemanticPhrase(listBuilder.build(), synToPathNodes, sentenceTheory, lightVerbs);

    EventMentions.Builder emsBuilder = new EventMentions.Builder();
    emsBuilder.addAllEventMentions(eventMentionsConsolidatedViaSemanticPhrase);
    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emsBuilder.build()).build();
  }

}
