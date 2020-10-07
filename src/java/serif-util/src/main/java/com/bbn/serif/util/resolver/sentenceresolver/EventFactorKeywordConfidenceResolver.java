package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.base.Optional;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;

public final class EventFactorKeywordConfidenceResolver implements SentenceResolver, Resolver {

  private HashMap<Symbol, HashMap<String, Double>> factorToSubstringToWeight;

  public EventFactorKeywordConfidenceResolver(String weightFile) throws Exception {
    // read file containing weights of (keyword, factor) pairs
    factorToSubstringToWeight = new HashMap<>();
    BufferedReader reader = new BufferedReader(new FileReader(weightFile));
    String line;
    while ((line = reader.readLine()) != null) {
      line = line.trim();
      if (line.length() == 0 || line.startsWith("#")) {
        continue;
      }

      String[] pieces = line.split("\t");
      if (pieces.length != 3) {
        throw new Exception("Malformed weightFile file with line:\n" + line);
      }

      Symbol factorType = Symbol.from(pieces[0].trim());
      String substring = pieces[1].trim().toLowerCase();
      Double weight = Double.valueOf(pieces[2].trim());
      factorToSubstringToWeight.put(factorType, new HashMap<>());
      factorToSubstringToWeight.get(factorType).put(substring, weight);
    }
    reader.close();
  }

  private String getLowerCaseEventPhrase(EventMention em, SentenceTheory st) {
    // This function is from EventFactorMagnitudeResolver, where it is private.
    String eventPhrase = em.anchorNode().span().text().toString();
    // Use semantic phrase instead if available
    Optional<Integer> startOpt = em.semanticPhraseStart();
    Optional<Integer> endOpt = em.semanticPhraseEnd();
    if (startOpt.isPresent() && endOpt.isPresent()) {
      int start = startOpt.get().intValue();
      int end = endOpt.get().intValue();
      eventPhrase = st.tokenSequence().span(start, end).text().toString();
    }
    return eventPhrase.toLowerCase();
  }

  private Double getWeight(EventMention.EventType factor, String phrase) {
    Double w = 1.0;
    if (this.factorToSubstringToWeight.containsKey(factor.eventType())) {
      for (String keyword : this.factorToSubstringToWeight.get(factor.eventType()).keySet()) {
        if (!phrase.contains(keyword)) {
          continue;
        }
        for (String phraseToken : phrase.split(" ")) {
          if (phraseToken.compareTo(keyword) == 0) {
            w *= this.factorToSubstringToWeight.get(factor.eventType()).get(keyword);
          }
        }
      }
    }
    return w;
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {
    EventMentions.Builder emsBuilder = new EventMentions.Builder();
    for (EventMention em : sentenceTheory.eventMentions()) {

      EventMention.Builder emBuilder = em.modifiedCopyBuilder();
      List<EventMention.EventType> newFactors = new ArrayList<>();

      // get weight and set new score
      String eventPhrase = this.getLowerCaseEventPhrase(em, sentenceTheory);
      for (EventMention.EventType eventFactor : em.factorTypes()) {
        // get weight
        Double weight = this.getWeight(eventFactor, eventPhrase);
        double newScore = eventFactor.score() * weight;

        // set score
        EventMention.EventType.Builder factorBuilder = eventFactor.modifiedCopyBuilder();
        factorBuilder.setScore(newScore);
        newFactors.add(factorBuilder.build());
      }

      emBuilder.setFactorTypes(newFactors);
      emsBuilder.addEventMentions(emBuilder.build());
    }
    final SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
    newST.eventMentions(emsBuilder.build());
    return newST.build();
  }

}
