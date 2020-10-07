package com.bbn.serif.util.events.consolidator;

import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Sentence;
import com.bbn.serif.theories.SentenceTheory;

import com.google.common.base.Optional;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;

import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

public final class EventMentionPropertyFinder {

  private JSONObject propertyWords;

  public EventMentionPropertyFinder(File propertiesJsonFile)
      throws IOException, ParseException {
    JSONParser parser = new JSONParser();

    Object obj = parser.parse(new FileReader(propertiesJsonFile));

    propertyWords = (JSONObject) obj;
  }

  public final HashMap<String, String> getProperties(
      EventMention eventMention, SentenceTheory sentenceTheory,
      HashSet<String> propertiesToFind) {

    HashMap<String, String> results = new HashMap<>();

    String eventPhrase = getLowerCaseEventPhrase(eventMention, sentenceTheory);

    for (Object propertyObj : propertyWords.keySet()) {
      // property is something like "Trend"
      String property = (String) propertyObj;
      if (!propertiesToFind.contains(property))
        continue;

      // property value is something like "Increase",
      // propertyValues is a hash keyed on property value
      JSONObject propertyValues = (JSONObject) propertyWords.get(propertyObj);
      for (Object propertyValueObj : propertyValues.keySet()) {
        String propertyValue = (String) propertyValueObj;
        // property word is something like "increasing"
        HashSet<String> propertyWords =  new HashSet<>();
        ArrayList<Object> wordList = (ArrayList<Object>) propertyValues.get(propertyValueObj);
        for (Object propertyWordObj : wordList) {
          propertyWords.add((String) propertyWordObj);
        }

        if (eventMentionMatches(eventPhrase, propertyWords)) {
          results.put(property, propertyValue);
        }
      }
    }

    return results;
  }

  public final HashMap<String, HashSet<String>> getMultipleProperties(
      EventMention eventMention, SentenceTheory sentenceTheory,
      HashSet<String> propertiesToFind) {

    HashMap<String, HashSet<String>> results = new HashMap<>();

    String eventPhrase = getLowerCaseEventPhrase(eventMention, sentenceTheory);

    for (Object propertyObj : propertyWords.keySet()) {
      // property is something like "Trend"
      String property = (String) propertyObj;
      if (!propertiesToFind.contains(property))
        continue;

      // property value is something like "Increase",
      // propertyValues is a hash keyed on property value
      JSONObject propertyValues = (JSONObject) propertyWords.get(propertyObj);
      for (Object propertyValueObj : propertyValues.keySet()) {
        String propertyValue = (String) propertyValueObj;
        // property word is something like "increasing"
        HashSet<String> propertyWords =  new HashSet<>();
        ArrayList<Object> wordList = (ArrayList<Object>) propertyValues.get(propertyValueObj);
        for (Object propertyWordObj : wordList) {
          propertyWords.add((String) propertyWordObj);
        }

        if (eventMentionMatches(eventPhrase, propertyWords)) {
          HashSet<String> propertySet;
          if (results.containsKey(property)) {
            propertySet = results.get(property);
          } else {
            propertySet = new HashSet<>();
            results.put(property, propertySet);
          }
          propertySet.add(propertyValue);
        }
      }
    }

    return results;
  }

  private boolean eventMentionMatches(String eventPhrase, HashSet<String> propertyWords)
  {
    for (String word : eventPhrase.trim().split(" ")) {
      if (propertyWords.contains(word)) {
        return true;
      }
    }
    return false;
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
}
