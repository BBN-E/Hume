package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.types.Polarity;
import com.bbn.serif.util.events.consolidator.EventMentionPropertyFinder;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.base.Optional;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;

public final class EventFactorMagnitudeResolver implements SentenceResolver, Resolver {

  EventMentionPropertyFinder eventMentionPropertyFinder;

  private final String polarityProperty = "Polarity";
  private final String magnitudeProperty = "Magnitude";
  private HashSet<String> relevantProperties;
  private HashMap<String, HashSet<Symbol>> substringToFactorClasses;

  private final HashMap<String, Double> magnitudeValues = new HashMap<String, Double>() {{
    put("High", 1.0);
    put("Medium", 0.5);
    put("Low", 0.25);
  }};

  public EventFactorMagnitudeResolver(String propertiesFile, String reverseFactorTypesFile)
      throws Exception {
    eventMentionPropertyFinder = new EventMentionPropertyFinder(new File(propertiesFile));
    relevantProperties = new HashSet<>();
    relevantProperties.add(polarityProperty);
    relevantProperties.add(magnitudeProperty);

    // Read reverse file which says which factor types to flip (multiply by -1) the
    // magnitude when a certain substring is found
    substringToFactorClasses = new HashMap<>();
    BufferedReader reader = new BufferedReader(new FileReader(reverseFactorTypesFile));
    String line;
    while ((line = reader.readLine()) != null) {
      line = line.trim();
      if (line.length() == 0 || line.startsWith("#")) {
        continue;
      }

      String[] pieces = line.split("\t", 2);
      if (pieces.length != 2) {
        throw new Exception("Malformed reverseFactorTypesFile file: " + pieces.length);
      }

      String substring = pieces[0].trim().toLowerCase();
      if (!substringToFactorClasses.containsKey(substring)) {
        substringToFactorClasses.put(substring, new HashSet<>());
      }

      String[] factorTypeStrs = pieces[1].split(" ");
      for (String factorTypeStr : factorTypeStrs) {
        Symbol factorType = Symbol.from(factorTypeStr.trim());
        substringToFactorClasses.get(substring).add(factorType);
      }
    }
    reader.close();
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    // Builder for final set of EventMentions that will appear in the returned sentence theory
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    for (EventMention em : sentenceTheory.eventMentions()) {
      boolean foundNegative = false;

      HashMap<String, String> emProperties =
          eventMentionPropertyFinder.getProperties(em, sentenceTheory, relevantProperties);

      // Get magnitude value if we can
      double magnitude = magnitudeValues.get("Medium");
      if (emProperties.containsKey(magnitudeProperty)) {
        String returnMagnitudeStr = emProperties.get(magnitudeProperty);
        magnitude = magnitudeValues.get(returnMagnitudeStr);
      }

      // Get polarity value if we can
      if (emProperties.containsKey(polarityProperty)) {
        String returnPolarityStr = emProperties.get(polarityProperty);
        if (returnPolarityStr.equals("Negative")) {
          foundNegative = true;
          magnitude = -magnitude;
        }
      }

      // Special case -- look for negative propositions whose head overlaps with
      // event mention anchor
      if (magnitude > 0) {
        for (Proposition proposition : sentenceTheory.propositions()) {
          if (!proposition.predHead().isPresent()) {
            continue;
          }

          SynNode eventAnchorHead = em.anchorNode().head();

          if (!proposition.hasStatus(Proposition.Status.NEGATIVE)) {
            continue;
          }

          if (proposition.predHead().get().span().overlaps(eventAnchorHead.span())) {
            foundNegative = true;
            magnitude = -magnitude;
            break;
          }
        }
      }

      /*
      // DEBUGGING
      String eventPhrase = em.anchorNode().span().text().toString();
      // Use semantic phrase instead if available
      Optional<Integer> startOpt = em.semanticPhraseStart();
      Optional<Integer> endOpt = em.semanticPhraseEnd();
      if (startOpt.isPresent() && endOpt.isPresent()) {
        int start = startOpt.get().intValue();
        int end = endOpt.get().intValue();
        eventPhrase = sentenceTheory.tokenSequence().span(start, end).text().toString();
      }
      System.out.println("-------------------");
      if (magnitude != 0.5)
        System.out.print("!!");
      if (magnitude < 0.0)
        System.out.print("!!");
      System.out.println(sentenceTheory.tokenSequence().span().text().toString());
      System.out.println(eventPhrase + " " + magnitude);
*/

      // Create new event mention, but replace factors with new factors that have
      // the magnitude set
      EventMention.Builder newEM = em.modifiedCopyBuilder();

      String eventPhrase = getLowerCaseEventPhrase(em, sentenceTheory);

      List<EventMention.EventType> newFactors = new ArrayList<>();
      for (EventMention.EventType factor : em.factorTypes()) {
        double factorMagnitude = magnitude;
        if (needsToFlipFactorMagnitude(eventPhrase, factor)) {
          factorMagnitude = -factorMagnitude;
        }
        EventMention.EventType.Builder factorBuilder = factor.modifiedCopyBuilder();
        factorBuilder.setMagnitude(Optional.of(factorMagnitude));
        newFactors.add(factorBuilder.build());
      }
      newEM.setFactorTypes(newFactors);

      // Check eventType for flip indicator (used in WM)
      boolean flip = false;
      for (EventMention.EventType eventType : em.eventTypes()) {
        if (needsToFlipPolarityEventType(eventPhrase, eventType)) {
          flip = true;
        }
      }
      if (flip) {
        foundNegative = !foundNegative;
      }

      // Set main polarity on EventMention based on previous results (used in WM)
      if (foundNegative) {
        newEM.setPolarity(Polarity.NEGATIVE);
      } else {
        newEM.setPolarity(Polarity.POSITIVE);
      }

      emsBuilder.addEventMentions(newEM.build());
    }

    final SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    newST.eventMentions(emsBuilder.build());
    return newST.build();
  }


  private String getLowerCaseEventPhrase(EventMention eventMention, SentenceTheory sentenceTheory) {
    String eventPhrase = eventMention.anchorNode().span().text().toString();
    // Use semantic phrase instead if available
    Optional<Integer> startOpt = eventMention.semanticPhraseStart();
    Optional<Integer> endOpt = eventMention.semanticPhraseEnd();
    if (startOpt.isPresent() && endOpt.isPresent()) {
      int start = startOpt.get().intValue();
      int end = endOpt.get().intValue();
      eventPhrase = sentenceTheory.tokenSequence().span(start, end).text().toString();
    }
    return eventPhrase.toLowerCase();
  }

  private boolean needsToFlipFactorMagnitude(String eventPhrase, EventMention.EventType factor) {
    for (String substring : substringToFactorClasses.keySet()) {
      if (eventPhrase.contains(substring)) {
        for (Symbol factorClassToFlip : substringToFactorClasses.get(substring)) {
          if (factor.eventType() == factorClassToFlip ||
              factor.eventType().asString().endsWith("#" + factorClassToFlip.asString())) {
            return true;
          }
        }
      }
    }
    return false;
  }

  private boolean needsToFlipPolarityEventType(
      String eventPhrase, EventMention.EventType eventType) {
    for (String substring : substringToFactorClasses.keySet()) {
      if (eventPhrase.contains(substring)) {
        for (Symbol eventTypeToFlip : substringToFactorClasses.get(substring)) {
          if (eventType.eventType() == eventTypeToFlip ||
              eventType.eventType().asString().endsWith("/" + eventTypeToFlip.asString())) {
            return true;
          }
        }
      }
    }
    return false;
  }

}
