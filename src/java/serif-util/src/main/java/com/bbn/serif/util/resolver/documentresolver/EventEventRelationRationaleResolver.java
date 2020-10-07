package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.*;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.types.Polarity;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.collect.ImmutableList;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.HashSet;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;
import com.google.common.base.Optional;

import java.util.HashMap;

import java.io.IOException;

public class EventEventRelationRationaleResolver implements DocumentResolver, Resolver {

    HashMap<String, List<String>> relationToWords = new HashMap<String, List<String>>();

    public EventEventRelationMention.Argument makeArgument(Object objectArg, String role) {
        if (objectArg instanceof ICEWSEventMention) {
            EventEventRelationMention.Argument arg =
                    new EventEventRelationMention.ICEWSEventMentionArgument(
                            (ICEWSEventMention) objectArg, Symbol.from(role));
            return arg;
        }

        if (objectArg instanceof EventMention) {
            EventEventRelationMention.Argument arg =
                    new EventEventRelationMention.EventMentionArgument(
                            (EventMention) objectArg, Symbol.from(role));
            return arg;
        }

        return null;
    }

    public EventEventRelationRationaleResolver(String relationDirectory) throws IOException {
        // Load in negative phrases
        // Lower case for normalization
        File dir = new File(relationDirectory);
        File[] directoryListing = dir.listFiles();
        if (directoryListing != null) {
            for (File child : directoryListing) {
                List<String> relationLst = Files.asCharSource(child, Charsets.UTF_8).readLines();
                // System.out.println(child.getName());
                String childName = child.getName();
                // System.out.println(substring(0, str.lastIndexOf('.')));
                relationToWords.put(childName.substring(0, childName.lastIndexOf('.')), relationLst);
            }
        }
    }

    // Simply check the words in between the two spans and assign a negative polarity
    // if a negative phrase is contained within the words between the two spans
    public Optional<String> assignTriggerText(String inBetween, String relationType) {
//         System.out.println("relationType: " + relationType);
        List<String> relationLst = relationToWords.getOrDefault(relationType,new ArrayList<>());
        // System.out.println(inBetween);
        for (String phrase : relationLst) {
            if (inBetween.contains(phrase)) {
                // System.out.println("negative");
                return Optional.of(phrase);
            }
        }
        // System.out.println("positive");
        return Optional.absent();
    }

    // Construct the span containing the left and right event mentions (event mentions are inclusive)
    // Lower case for normalization
    public String constructInBetween(SentenceTheory sentenceTheory, EventMention leftEventMention, EventMention rightEventMention) {
        int smallerLeft = Math.min(leftEventMention.semanticPhraseStart().get(), leftEventMention.semanticPhraseEnd().get());
        int smallerRight = Math.min(rightEventMention.semanticPhraseStart().get(), rightEventMention.semanticPhraseEnd().get());
        int biggerLeft = Math.max(leftEventMention.semanticPhraseStart().get(), leftEventMention.semanticPhraseEnd().get());
        int biggerRight = Math.max(rightEventMention.semanticPhraseStart().get(), rightEventMention.semanticPhraseEnd().get());

        int smallest = Math.min(smallerLeft, smallerRight);
        int biggest = Math.max(biggerLeft, biggerRight);
        String inBetween = sentenceTheory.tokenSequence().span(smallest, biggest).tokenizedText().utf16CodeUnits();
        return inBetween.toLowerCase();
    }

    @Override
    public DocTheory resolve(DocTheory docTheory) {
        final DocTheory.Builder newDT = docTheory.modifiedCopyBuilder();
        ImmutableList.Builder<EventEventRelationMention> resolvedEERMs = ImmutableList.builder();
        for (EventEventRelationMention eventEventRelationMentionOld : docTheory.eventEventRelationMentions()) {
            EventMention leftEventMention = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMentionOld.leftEventMention()).eventMention();
            EventMention rightEventMention = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMentionOld.rightEventMention()).eventMention();
            SentenceTheory sentenceTheory = leftEventMention.sentenceTheory(docTheory);
            String inBetween = constructInBetween(sentenceTheory, leftEventMention, rightEventMention);


            Optional<String> triggerText = assignTriggerText(inBetween, eventEventRelationMentionOld.relationType().toString());
            // System.out.println(triggerText);

            EventEventRelationMention.Builder newEventEventRelationMention = new EventEventRelationMention.Builder();
            newEventEventRelationMention.relationType(eventEventRelationMentionOld.relationType())
                    .leftEventMention(makeArgument(leftEventMention, "arg1"))
                    .rightEventMention(makeArgument(rightEventMention, "arg2"))
                    .confidence(eventEventRelationMentionOld.confidence())
                    .pattern(eventEventRelationMentionOld.pattern())
                    .model(eventEventRelationMentionOld.model())
                    .polarity(eventEventRelationMentionOld.polarity())
                    .triggerText(triggerText);
            resolvedEERMs.add(newEventEventRelationMention.build());
        }
        newDT.eventEventRelationMentions(EventEventRelationMentions.create(resolvedEERMs.build()));
        return newDT.build();
    }

    public static void main(String[] args) throws Exception{
        String exampleDir = "/d4m/ears/expts/47837.072220.v1/expts/hume_test.072220.cx.v1/pyserif/pyserif_confidence_calibration/0/output";
        EventEventRelationRationaleResolver eventEventRelationRationaleResolver = new EventEventRelationRationaleResolver("/nfs/raid88/u10/users/jcai/eer-serifxml/Hume_2/Hume/resource/causal_relation_word_lists/relations");
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builder().build();
        for(File file :new File(exampleDir).listFiles()){
            DocTheory docTheory = serifXMLLoader.loadFrom(file);
            DocTheory resolvedDocTheory = eventEventRelationRationaleResolver.resolve(docTheory);
            // Write back logic is not needed here for debugging purpose
        }
    }
}
