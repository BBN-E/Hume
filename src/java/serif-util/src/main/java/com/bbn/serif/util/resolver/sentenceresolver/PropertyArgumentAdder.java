package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.ValueMention;
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
import java.util.List;


public final class PropertyArgumentAdder implements SentenceResolver, Resolver {

  private final ImmutableSet<String> processTypes;
  private final ImmutableSet<String> propertyTypes;
//  private final HashMap<String, HashSet<String>> selectionConstraints;

  public PropertyArgumentAdder(String processTypesFile, String propertyTypesFile)
      throws IOException {
    processTypes = ImmutableSet.copyOf(Files.asCharSource(new File(processTypesFile), Charsets.UTF_8).readLines());
    propertyTypes = ImmutableSet.copyOf(Files.asCharSource(new File(propertyTypesFile), Charsets.UTF_8).readLines());
//    selectionConstraints = new HashMap<>();
//    for (String line : Files.asCharSource(new File(constraintsFile), Charsets.UTF_8).readLines()) {
//      if (line.startsWith("#") || line.trim().equals("")) {
//        continue;
//      }
//      String[] elements = line.split(" ");
//      String process = elements[0];
//      String property = elements[1];
//      if (!selectionConstraints.containsKey(process)) {
//        selectionConstraints.put(process, new HashSet<>());
//      }
//      selectionConstraints.get(process).add(property);
//    }
//
    System.out.println("* valid process types: " + String.join(" ", this.processTypes));
    System.out.println("* valid property types: " + String.join(" ", this.propertyTypes));
//    System.out.println("* selection constraints: " + this.selectionConstraints.toString());

  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    int neighborDistance = 3;  // TODO this is a magic number and should be studied/revised

    // Final EventMentions that will go into our new sentence
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    final ImmutableList.Builder<ValueMention> propertyMentionsBuilder = ImmutableList.builder();
    for (final ValueMention vm : sentenceTheory.valueMentions()) {
      if (this.propertyTypes.contains(vm.fullType().toString())) {
        propertyMentionsBuilder.add(vm);
      }
    }
    final ImmutableList<ValueMention> propertyMentions = propertyMentionsBuilder.build();

    // 0: no property candidates.  Keep all original EventMentions unchanged.
    if (propertyMentions.size() == 0) {
      emsBuilder.addAllEventMentions(sentenceTheory.eventMentions());

    } else {  // property candidates are available
      //System.out.println("property candidates: " + propertyMentions.size());

      // Original EventMentions
      ImmutableList<EventMention> ems = ImmutableList.copyOf(sentenceTheory.eventMentions().asList());
      final ImmutableList.Builder<EventMention> newEventMentions = ImmutableList.builder();
      for (EventMention em : ems) {

        // Which of this EM's factors (processes) may have a property?
        List<String> factors = new ArrayList<>();
        String eventType = em.type().asString();
        if (this.processTypes.contains(eventType)) {
          factors.add(eventType);
        }
        for (EventMention.EventType factorType : em.factorTypes()) {
          String factor = factorType.eventType().asString();
          if (this.processTypes.contains(factor)) {
              factors.add(factor);
          }
        }

        // 1: factor types all invalid: keep original EventMention unchanged
        if (factors.size() == 0) {
          newEventMentions.add(em);

        } else {  // 2: factor type is allowed to take a property
          EventMention modifiedEventMention = EventMentionUtils.heuristicallyAddPropertyArgument(
//              propertyMentions, factors, em, sentenceTheory, this.selectionConstraints, neighborDistance);
              propertyMentions, em, neighborDistance);
          newEventMentions.add(modifiedEventMention);
        }
      }
      emsBuilder.addAllEventMentions(newEventMentions.build());
    }

    SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    return newST.eventMentions(emsBuilder.build()).build();
  }

}
