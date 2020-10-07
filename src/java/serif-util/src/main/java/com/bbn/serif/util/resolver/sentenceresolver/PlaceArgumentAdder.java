package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;

import java.util.List;


// +2
public final class PlaceArgumentAdder implements SentenceResolver, Resolver {

  /* 
  public static void printEventMentions(final EventMentions ems) {
    for(final EventMention em : ems.eventMentions()) {
      if(em.factorTypes().size() > 0) {
        final String eventType = em.type().asString();
        final String anchorText = em.anchorNode().span().text().toString().toLowerCase().replaceAll("\t'", "_").replaceAll(" ", "_");
        System.out.println("**" + eventType + " " + anchorText);

        for(final EventMention.Argument arg : em.arguments()) {
          final String role = arg.role().asString();
          final String argText = arg.span().text().utf16CodeUnits().toString().replaceAll(" ", "_");
          System.out.println("  - " + role + "\t" + argText + "\t" + arg.score());
        }
      }
    }
  }
  */

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    final ImmutableList.Builder<Mention> placeMentionsBuilder = ImmutableList.builder();
    for(final Mention m : sentenceTheory.mentions()) {
      if(m.entityType().toString().equals("LOC") || m.entityType().toString().equals("GPE")) {
        placeMentionsBuilder.add(m);
      }
    }
    final ImmutableList<Mention> placeMentions = placeMentionsBuilder.build();

    ImmutableList<EventMention> ems =
        ImmutableList.copyOf(sentenceTheory.eventMentions().asList());
    // Final EventMentions that will go into our new sentence
    EventMentions.Builder emBuilder = new EventMentions.Builder();

    if (placeMentions.size() > 0) {
      ImmutableList<EventMention> modifiedEventMentions =
          EventMentionUtils
              .heuristicallyAddPlaceArgument(placeMentions, ems, sentenceTheory);
      emBuilder.addAllEventMentions(modifiedEventMentions);
    } else {
      emBuilder.addAllEventMentions(sentenceTheory.eventMentions());
    }

    /*
    if(!sentenceTheory.isEmpty()) {
      final String sentenceText = sentenceTheory.span().text().utf16CodeUnits().toString();
      System.out.println(sentenceText);
      PlaceArgumentAdder.printEventMentions(emBuilder.build());
      System.out.println("====================");
    }
    */

    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emBuilder.build()).build();
  }

}
