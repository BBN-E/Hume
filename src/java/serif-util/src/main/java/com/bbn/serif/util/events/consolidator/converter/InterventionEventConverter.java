package com.bbn.serif.util.events.consolidator.converter;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.FileReader;
import java.io.IOException;
import java.util.Iterator;

public final class InterventionEventConverter {
  private final ImmutableList<EventPattern> eventPatterns;

  private InterventionEventConverter(final ImmutableList<EventPattern> eventPatterns) {
    this.eventPatterns = eventPatterns;
  }

  public static InterventionEventConverter from(final String filepath, final OntologyHierarchy ontologyHierarchy) throws IOException, ParseException {
    return new InterventionEventConverter(loadFromFile(filepath, ontologyHierarchy));
  }

  private static ImmutableList<String> toStrings(final JSONArray array) {
    final ImmutableList.Builder<String> ret = ImmutableList.builder();
    Iterator it = array.iterator();
    while(it.hasNext()) {
      ret.add((String) it.next());
    }
    return ret.build();
  }

  public static class EventPattern {
    private final String eventType;
    private final ImmutableList<KeyPhrase> argumentTriggers;
    private final ImmutableList<String> argumentValues;
    private final ImmutableList<KeyPhrase> keywords;

    private EventPattern(final String eventType, final ImmutableList<KeyPhrase> argumentTriggers, final ImmutableList<String> argumentValues, final ImmutableList<KeyPhrase> keywords) {
      this.eventType = eventType;
      this.argumentTriggers = argumentTriggers;
      this.argumentValues = argumentValues;
      this.keywords = keywords;
    }

    private static EventPattern from(final String eventType, final ImmutableList<String> argumentTriggers, final ImmutableList<String> argumentValues, final ImmutableList<String> keywords) {
      final ImmutableList.Builder<KeyPhrase> argumentTriggersBuilder = ImmutableList.builder();
      final ImmutableList.Builder<KeyPhrase> keywordsBuilder = ImmutableList.builder();
      for(final String s : argumentTriggers) {
        argumentTriggersBuilder.add(KeyPhrase.from(s));
      }
      for(final String s : keywords) {
        keywordsBuilder.add(KeyPhrase.from(s));
      }

      return new EventPattern(eventType, argumentTriggersBuilder.build(), argumentValues, keywordsBuilder.build());
    }

    public String eventType() {
      return this.eventType;
    }

    public ImmutableList<KeyPhrase> argumentTriggers() {
      return this.argumentTriggers;
    }

    public ImmutableList<String> argumentValues() {
      return this.argumentValues;
    }

    public ImmutableList<KeyPhrase> keywords() {
      return this.keywords;
    }
  }

  public static class KeyPhrase {
    private final String phrase;
    private final String anchor;

    private KeyPhrase(final String phrase, final String anchor) {
      this.phrase = phrase;
      this.anchor = anchor;
    }

    public static KeyPhrase from(final String phrase) {
      final String[] tokens = phrase.split(" ");

      String p = phrase.replaceAll("<", "").replaceAll(">", "");
      String anchor = "";

      if(tokens.length > 1) {
        for (final String token : tokens) {
          if (token.startsWith("<") && token.endsWith(">")) {
            anchor = token.substring(1, token.length() - 1);
          }
        }
      } else {
        anchor = tokens[0];
      }

      return new KeyPhrase(p, anchor);
    }

    public String phrase() {
      return this.phrase;
    }

    public String anchor() {
      return this.anchor;
    }
  }

  public static ImmutableList<EventPattern> loadFromFile(final String filepath, final OntologyHierarchy ontologyHierarchy) throws IOException, ParseException {
    final ImmutableList.Builder<EventPattern> ret = ImmutableList.builder();

    JSONArray events = (JSONArray)(new JSONParser().parse(new FileReader(filepath)));

    Iterator eventIt = events.iterator();
    while(eventIt.hasNext()) {
      JSONObject obj = (JSONObject) eventIt.next();
      final String eventType = (String) obj.get("event_type");
      ontologyHierarchy.assertEventTypeIsInOntology(eventType, "InterventionEventConverter.loadFromFile");

      final ImmutableList<String> argumentTriggers = toStrings((JSONArray) obj.get("argument_triggers"));
      final ImmutableList<String> argumentValues = toStrings((JSONArray) obj.get("argument_values"));
      final ImmutableList<String> keywords = toStrings((JSONArray) obj.get("keywords"));

      //System.out.println(eventType);
      //System.out.println("argumentTriggers: " + StringUtils.join(argumentTriggers, " | "));
      //System.out.println("argumentValues: " + StringUtils.join(argumentValues, " | "));
      //System.out.println("keywords: " + StringUtils.join(keywords, " | "));

      ret.add(EventPattern.from(eventType, argumentTriggers, argumentValues, keywords));
    }

    return ret.build();
  }

  public ImmutableList<EventMention> addEventMentionsUsingKeywords(final SentenceTheory st) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    final ImmutableList<SynNode> synnodes = EventMentionUtils.getSynNodeOfEachToken(st);
    final ImmutableList<String> words = EventMentionUtils.getWordOfEachToken(st);

    for(final EventPattern eventPattern : eventPatterns) {
      for(final KeyPhrase keyPhrase : eventPattern.keywords) {
        final ImmutableList<IntegerPair> indices = findIndicesInTokens(words, keyPhrase.phrase, Optional.absent(), Optional.absent());
        for(final IntegerPair startEnd : indices) {
          final int semanticPhraseStart = startEnd.first;
          final int semanticPhraseEnd = startEnd.second;
          //System.out.println("Trying to find: " + keyPhrase.anchor + " " + semanticPhraseStart + " " + semanticPhraseEnd);
          //System.out.println(StringUtils.join(words, " "));
          final ImmutableList<IntegerPair> anchorStartEnd = findIndicesInTokens(words, keyPhrase.anchor, Optional.of(semanticPhraseStart), Optional.of(semanticPhraseEnd));
          final int anchorTokenIndex = anchorStartEnd.get(0).first;

          final EventMention em = EventMention.builder(Symbol.from(eventPattern.eventType))
              .setAnchorNode(synnodes.get(anchorTokenIndex)).setAnchorPropFromNode(st).setScore(1.0)
              .setSemanticPhraseStart(semanticPhraseStart).setSemanticPhraseEnd(semanticPhraseEnd)
              .setModel(Symbol.from("Keyword")).build();
          ret.add(em);

          final String semanticPhraseString = st.tokenSequence().span(semanticPhraseStart, semanticPhraseEnd).tokenizedText().utf16CodeUnits().toString();
          System.out.println("INTERVENTION: " + em.type().asString() + " [" + semanticPhraseString + "] " + em.anchorNode().span().tokenizedText().utf16CodeUnits().toString());
        }
      }
    }

    return ret.build();
  }


  public ImmutableList<IntegerPair> findIndicesInTokens(final ImmutableList<String> tokens, final String phrase, final Optional<Integer> startIndex, final Optional<Integer> endIndex) {
    final ImmutableList.Builder<IntegerPair> ret = ImmutableList.builder();

    final String[] targetTokens = phrase.toLowerCase().split(" ");
    final int start = startIndex.isPresent()? startIndex.get() : 0;
    final int end = endIndex.isPresent()? endIndex.get() : tokens.size()-1;

    for(int i=start; (i+targetTokens.length-1)<=end; i++) {
      if(tokens.get(i).toLowerCase().equals(targetTokens[0])) {
        boolean match = true;
        for(int j=1; j<targetTokens.length; j++) {
          if(!tokens.get(i+j).toLowerCase().equals(targetTokens[j])) {
            match = false;
            break;
          }
        }
        if(match) {
          ret.add(new IntegerPair(i, i+targetTokens.length-1));
        }
      }
    }

    return ret.build();
  }

  public class IntegerPair {
    private final int first;
    private final int second;

    public IntegerPair(final int first, final int second) {
      this.first = first;
      this.second = second;
    }

    public int first() {
      return this.first;
    }

    public int second() {
      return this.second;
    }
  }

  public static void main (String [] args) throws IOException, ParseException {
    String jsonFile = args[0];

    //loadFromFile(jsonFile);
  }

}
