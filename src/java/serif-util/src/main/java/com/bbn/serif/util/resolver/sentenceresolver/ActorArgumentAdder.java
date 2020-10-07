package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;

import java.io.IOException;

// +2
public final class ActorArgumentAdder implements SentenceResolver, Resolver {

  final ImmutableMap<String, String> docidToSourceType;

  public ActorArgumentAdder(String metadataFile)
      throws IOException
  {
    final ImmutableMap<String, String> dtst =
    EventConsolidator.readDocumentSourceType(metadataFile);
    docidToSourceType = dtst;
  }

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
    String docid = sentenceTheory.sentence().document().name().asString();
    boolean aggressive = true;
    //if (docidToSourceType.get(docid).equals("news"))
    //  aggressive = true;


    final ImmutableList.Builder<Mention> actorMentionsBuilder = ImmutableList.builder();
    for(final Mention m : sentenceTheory.mentions()) {
      if(m.entityType().toString().equals("PER") ||
          m.entityType().toString().equals("ORG") ||
          m.entityType().toString().equals("GPE"))
      {
        actorMentionsBuilder.add(m);
      }
    }

    ImmutableList<EventMention> ems =
        ImmutableList.copyOf(sentenceTheory.eventMentions().asList());

    // Final EventMentions that will go into our new sentence
    EventMentions.Builder emBuilder = new EventMentions.Builder();

    if (aggressive) {
      ImmutableList<EventMention> modifiedEventMentions =
          EventMentionUtils.heuristicallyAddActorArgument(
              actorMentionsBuilder.build(), ems, sentenceTheory);
      emBuilder.addAllEventMentions(modifiedEventMentions);
    } else {
      emBuilder.addAllEventMentions(ems);
    }

    /*
    if(!sentenceTheory.isEmpty()) {
      final String sentenceText = sentenceTheory.span().text().utf16CodeUnits().toString();
      System.out.println(sentenceText);
      ActorArgumentAdder.printEventMentions(emBuilder.build());
      System.out.println("====================");
    }
    */

    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emBuilder.build()).build();
  }

}
