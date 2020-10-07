package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;


public final class ThemeArgumentAdder implements SentenceResolver, Resolver {

  private final ImmutableSet<String> invalidThemeTypes;
  private final ImmutableSet<String> validFactorTypes;
  private final HashMap<String, HashSet<String>> selectionConstraints;

  public ThemeArgumentAdder(String invalidThemesFile, String validFactorsFile, String constraintsFile)
      throws IOException {
    invalidThemeTypes = ImmutableSet.copyOf(Files.asCharSource(new File(invalidThemesFile), Charsets.UTF_8).readLines());
    validFactorTypes = ImmutableSet.copyOf(Files.asCharSource(new File(validFactorsFile), Charsets.UTF_8).readLines());
    selectionConstraints = new HashMap<>();
    for (String line : Files.asCharSource(new File(constraintsFile), Charsets.UTF_8).readLines()) {
      if (line.startsWith("#") || line.trim().equals("")) {
        continue;
      }
      String[] elements = line.split(" ");
      String factor = elements[0];
      String theme = elements[1];
      if (!selectionConstraints.containsKey(factor)) {
        selectionConstraints.put(factor, new HashSet<>());
      }
      selectionConstraints.get(factor).add(theme);
    }

    System.out.println("* valid factors: " + String.join(" ", this.validFactorTypes));
    System.out.println("* invalid themes: " + String.join(" ", this.invalidThemeTypes));
    System.out.println("* selection constraints: " + this.selectionConstraints.toString());

  }

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

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    /* For each EventMention...
    Case 0: no Mentions available as candidates for theme.  Use existing EM and its Arguments.
    Case 1: factor may not take theme.  Use existing EM and its Arguments.
    Case 2: factor may take a theme, modulo selection constraints.

    Case 2 algorithm:
    - search for licit theme within semantic phrase
    - search for licit theme within neighborhood of semantic phrase/trigger
    - ...
     */

    int neighborDistance = 3;  // TODO this is a magic number and should be studied/revised

    final ImmutableList.Builder<Mention> themeMentionsBuilder = ImmutableList.builder();
    for(final Mention m : sentenceTheory.mentions()) {
      if(!this.invalidThemeTypes.contains(m.entityType().toString())) {
        themeMentionsBuilder.add(m);
      }
    }
    final ImmutableList<Mention> themeMentions = themeMentionsBuilder.build();

    // Final EventMentions that will go into our new sentence
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    // 0: no theme candidates
    if (themeMentions.size() == 0) {
      emsBuilder.addAllEventMentions(sentenceTheory.eventMentions());

    } else {  // theme candidates are available
      //System.out.println("theme candidates: " + themeMentions.size());

      // Original EventMentions
      ImmutableList<EventMention> ems = ImmutableList.copyOf(sentenceTheory.eventMentions().asList());
      final ImmutableList.Builder<EventMention> newEventMentions = ImmutableList.builder();
      for (EventMention em : ems) {

        // Which of this EM's factors may have a theme?
        List<String> factors = new ArrayList<>();
        String eventType = em.type().asString();
        //System.out.println("; CURRENT FACTOR: " + eventType);
        if (validFactorTypes.contains(eventType)) {
          factors.add(eventType);
        }
        for (EventMention.EventType factorType : em.factorTypes()) {
          String factor = factorType.eventType().asString();
          //System.out.println("; CURRENT FACTOR: " + factor);
          if (validFactorTypes.contains(factor)) {
              factors.add(factor);
          }
        }
        //System.out.println("valid factors: " + factors.toString());

        // 1: factor types all invalid
        if (factors.size() == 0) {
          newEventMentions.add(em);

        } else {  // 2: factor type is allowed to take a theme
          EventMention modifiedEventMention = EventMentionUtils.heuristicallyAddThemeArgument(
              themeMentions, factors, em, sentenceTheory, this.selectionConstraints, neighborDistance);
          newEventMentions.add(modifiedEventMention);
        }
      }
      emsBuilder.addAllEventMentions(newEventMentions.build());
    }

    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emsBuilder.build()).build();
  }

}
