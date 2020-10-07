package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.ValueMention;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;

import java.util.List;

// +2
public final class TimeArgumentAdder implements SentenceResolver, Resolver {

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    List<ValueMention> timeMentions = Lists.newArrayList();
    for (final ValueMention m : sentenceTheory.valueMentions()) {
      if (m.type().toString().equals("TIMEX2")) {
        timeMentions.add(m);
      }
    }

    ImmutableList<EventMention> ems =
        ImmutableList.copyOf(sentenceTheory.eventMentions().asList());

    // Final EventMentions that will go into our new sentence
    EventMentions.Builder emBuilder = new EventMentions.Builder();

    if (timeMentions.size() == 1) {
      ImmutableList<EventMention> modifiedEventMentions =
          EventMentionUtils.heuristicallyAddTimeArgument(timeMentions.get(0), ems, sentenceTheory);
      emBuilder.addAllEventMentions(modifiedEventMentions);
    } else {
      emBuilder.addAllEventMentions(sentenceTheory.eventMentions());
    }

    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emBuilder.build()).build();
  }

}
