package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.types.DirectionOfChange;
import com.bbn.serif.util.events.consolidator.EventMentionPropertyFinder;
import com.bbn.serif.util.resolver.Resolver;

import org.json.simple.parser.ParseException;

import java.io.IOException;
import java.io.File;
import java.util.HashMap;
import java.util.HashSet;

public final class EventMentionDirectionOfChangeResolver implements DocumentResolver, Resolver {

  EventMentionPropertyFinder eventMentionPropertyFinder;

  public EventMentionDirectionOfChangeResolver(String propertiesFile)
      throws IOException, ParseException {
    eventMentionPropertyFinder = new EventMentionPropertyFinder(new File(propertiesFile));
  }

  public final DocTheory resolve(final DocTheory docTheory) {
    String directionOfChangeProperty = "Trend";
    HashSet<String> propertiesToFind = new HashSet<>();
    propertiesToFind.add(directionOfChangeProperty);

    final DocTheory.Builder newDT = docTheory.modifiedCopyBuilder();

    for (int i = 0; i < docTheory.numSentences(); ++i) {
      final SentenceTheory sentenceTheory = docTheory.sentenceTheory(i);
      EventMentions.Builder emsBuilder = new EventMentions.Builder();

      for (final EventMention em : sentenceTheory.eventMentions()) {
        DirectionOfChange directionOfChange = DirectionOfChange.UNSPECIFIED;
        HashMap<String, String> properties =
            eventMentionPropertyFinder.getProperties(em, sentenceTheory, propertiesToFind);
        if (properties.containsKey(directionOfChangeProperty)) {
          String direction = properties.get(directionOfChangeProperty);
          if (direction.equals("Increase")) {
            directionOfChange = DirectionOfChange.INCREASE;
          } else if (direction.equals("Decrease")) {
            directionOfChange = DirectionOfChange.DECREASE;
          }
        }

        // Special case -- look at propositions
        if (directionOfChange == DirectionOfChange.UNSPECIFIED) {

          for (Proposition proposition : sentenceTheory.propositions()) {
            DirectionOfChange propDirectionOfChange = DirectionOfChange.UNSPECIFIED;
            SynNode eventAnchorHead = em.anchorNode().head();

            String predPos =
                proposition.predType().name().asUnicodeFriendlyString().utf16CodeUnits()
                    .toLowerCase();

            if (proposition.predHead().isPresent()) {
              String propHead =
                  proposition.predHead().get().head().tokenSpan().tokenizedText(docTheory)
                      .utf16CodeUnits().toLowerCase();
              if (propHead.contains("increase")) {
                propDirectionOfChange = DirectionOfChange.INCREASE;
              } else if (propHead.contains("decrease")) {
                propDirectionOfChange = DirectionOfChange.DECREASE;
              } else {
                continue;
              }
            }

            boolean eventAnchorAsArgHead = false;

            for (Proposition.Argument argument : proposition.args()) {
              if (argument.span().overlaps(eventAnchorHead.span())) {
                eventAnchorAsArgHead = true;
                break;
              }
            }

            if (eventAnchorAsArgHead &&
                !propDirectionOfChange.equals(DirectionOfChange.UNSPECIFIED))
            {
              directionOfChange = propDirectionOfChange;
              break;
            }
          }
        }

        final EventMention newEM =
            em.modifiedCopyBuilder().setDirectionOfChange(directionOfChange).build();

        emsBuilder.addEventMentions(newEM);
      }

      final SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
      newST.eventMentions(emsBuilder.build());
      newDT.replacePrimarySentenceTheory(sentenceTheory, newST.build());
    }
    return newDT.build();
  }

}
