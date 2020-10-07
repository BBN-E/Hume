package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;

import java.util.HashSet;
import java.util.List;

// +2
public final class ArtifactArgumentAdder implements SentenceResolver, Resolver {

  HashSet<String> artifactSubtypes = new HashSet<>();

  public ArtifactArgumentAdder(List<String> subtypes) {
    for (String subtype : subtypes)
      artifactSubtypes.add(subtype);
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    final ImmutableList.Builder<Mention> mentionsBuilder = ImmutableList.builder();
    for (final Mention m : sentenceTheory.mentions()) {
      String subtype = m.entitySubtype().toString();
      if (artifactSubtypes.contains(subtype))
        mentionsBuilder.add(m);
    }

    ImmutableList<EventMention> ems =
        ImmutableList.copyOf(sentenceTheory.eventMentions().asList());

    // Final EventMentions that will go into our new sentence
    EventMentions.Builder emBuilder = new EventMentions.Builder();

    ImmutableList<EventMention> modifiedEventMentions =
        EventMentionUtils.heuristicallyAddArtifactArgument(
            mentionsBuilder.build(), ems, sentenceTheory);
    emBuilder.addAllEventMentions(modifiedEventMentions);

    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emBuilder.build()).build();
  }

}
