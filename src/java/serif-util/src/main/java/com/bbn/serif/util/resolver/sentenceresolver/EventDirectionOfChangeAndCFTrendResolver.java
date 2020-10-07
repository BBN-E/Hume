package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.serif.theories.*;
import com.bbn.serif.types.DirectionOfChange;
import com.bbn.serif.types.Trend;
import com.bbn.serif.util.events.consolidator.EventMentionPropertyFinder;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.base.Optional;
import org.json.simple.parser.ParseException;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;

import com.bbn.serif.io.SerifXMLLoader;  // for testing with main


public class EventDirectionOfChangeAndCFTrendResolver implements SentenceResolver, Resolver {
    EventMentionPropertyFinder eventMentionPropertyFinder;
    static String directionOfChangeProperty = "Trend";
    static String lexicalDecreaseProperty = "Trend_Lexical_Decrease";
    HashSet<String> propertiesToFind;
    HashSet<String> lexicalPropertiesToFind;

    public EventDirectionOfChangeAndCFTrendResolver(String propertiesFile) throws IOException, ParseException {
        eventMentionPropertyFinder = new EventMentionPropertyFinder(new File(propertiesFile));
        this. propertiesToFind = new HashSet<>();
        propertiesToFind.add(directionOfChangeProperty);
        this. lexicalPropertiesToFind = new HashSet<>();
        lexicalPropertiesToFind.add(lexicalDecreaseProperty);
    }

    @Override
    public SentenceTheory resolve(SentenceTheory sentenceTheory) {
        EventMentions.Builder emsBuilder = new EventMentions.Builder();

        for (final EventMention em : sentenceTheory.eventMentions()) {
            DirectionOfChange directionOfChange = DirectionOfChange.UNSPECIFIED;
            Trend trend = Trend.UNSPECIFIED;
            HashMap<String, String> properties =
                    eventMentionPropertyFinder.getProperties(em, sentenceTheory, propertiesToFind);
            if (properties.containsKey(directionOfChangeProperty)) {
                String direction = properties.get(directionOfChangeProperty);
                if (direction.equals("Increase")) {
                    directionOfChange = DirectionOfChange.INCREASE;
                    trend = Trend.INCREASE;
                } else if (direction.equals("Decrease")) {
                    directionOfChange = DirectionOfChange.DECREASE;
                    trend = Trend.DECREASE;
                }
            }

            // Special case -- look at propositions
            if (directionOfChange == DirectionOfChange.UNSPECIFIED) {

                for (Proposition proposition : sentenceTheory.propositions()) {
                    DirectionOfChange propDirectionOfChange = DirectionOfChange.UNSPECIFIED;
                    Trend propTrend = Trend.UNSPECIFIED;
                    SynNode eventAnchorHead = em.anchorNode().head();

                    String predPos =
                            proposition.predType().name().asUnicodeFriendlyString().utf16CodeUnits()
                                    .toLowerCase();

                    if (proposition.predHead().isPresent()) {
                        String propHead =
                                proposition.predHead().get().head().span().tokenizedText()
                                        .utf16CodeUnits().toLowerCase();
                        if (propHead.contains("increase")) {
                            propDirectionOfChange = DirectionOfChange.INCREASE;
                            propTrend = Trend.INCREASE;
                        } else if (propHead.contains("decrease")) {
                            propDirectionOfChange = DirectionOfChange.DECREASE;
                            propTrend = Trend.DECREASE;
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
                        trend = propTrend;
                        break;
                    }
                }
            }

            // Modify direction based on lexical details of the phrase
            HashMap<String, HashSet<String>> lexicalProperties =
                eventMentionPropertyFinder.getMultipleProperties(em, sentenceTheory, lexicalPropertiesToFind);
            HashSet<String> factorTypesToDecrease = new HashSet<>();
            if (lexicalProperties.containsKey(lexicalDecreaseProperty)) {
                factorTypesToDecrease = lexicalProperties.get(lexicalDecreaseProperty);
            }

            final EventMention.Builder newEM =
                    em.modifiedCopyBuilder().setDirectionOfChange(directionOfChange);
            List<EventMention.EventType> newFactors = new ArrayList<>();
            for(EventMention.EventType factor : em.factorTypes()){
                EventMention.EventType.Builder factorBuilder = factor.modifiedCopyBuilder();
                // Factor-specific lexical trend reversal
                if (factorTypesToDecrease.contains(factor.eventType().asString())) {
                    if (trend.toString().equals(Trend.INCREASE.toString()) || trend.toString().equals(Trend.UNSPECIFIED.toString())) {
                        trend = Trend.DECREASE;
                    } else if (trend.toString().equals(Trend.DECREASE.toString())) {
                        trend = Trend.INCREASE;
                    }
                    // don't change stable trends
                }

                factorBuilder.setTrend(Optional.of(trend));
                newFactors.add(factorBuilder.build());
            }
            newEM.setFactorTypes(newFactors);
            emsBuilder.addEventMentions(newEM.build());
        }

        final SentenceTheory.Builder newST = sentenceTheory.modifiedCopyBuilder();
        newST.eventMentions(emsBuilder.build());
        return newST.build();
    }

    public static void main(String[] args) throws Exception{
        // For testing/debugging purposes
        String exampleDir = "/d4m/ears/expts/47838_v1/expts/hume_test.041420.cx.v2/pyserif/pyserif_main/tmp_output";
        String propertiesFile = "/home/criley/repos/Hume/resource/event_consolidation/common/event_mention_properties.json";
        EventDirectionOfChangeAndCFTrendResolver eventDirectionOfChangeAndCFTrendResolver =
            new EventDirectionOfChangeAndCFTrendResolver(propertiesFile);
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builder().build();
        for(File file : new File(exampleDir).listFiles()){
            DocTheory docTheory = serifXMLLoader.loadFrom(file);
            for (SentenceTheory st : docTheory.sentenceTheories()) {
                SentenceTheory resolvedDocTheory = eventDirectionOfChangeAndCFTrendResolver.resolve(st);
                // Write back logic is not needed here for debugging purpose
            }
        }
    }
}
