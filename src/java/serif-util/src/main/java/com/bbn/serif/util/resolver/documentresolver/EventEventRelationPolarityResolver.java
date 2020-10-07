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

import java.io.IOException;

public class EventEventRelationPolarityResolver implements DocumentResolver, Resolver {

    Set<String> negationPhrases = new HashSet<String>();;

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

    public EventEventRelationPolarityResolver(String negationFile) throws IOException {
        // Load in negative phrases
        // Lower case for normalization
        List<String> negationLst = Files.asCharSource(new File(negationFile), Charsets.UTF_8).readLines();
        for (String phrase : negationLst) {
            negationPhrases.add(phrase.toLowerCase());
        }
    }

    // Simply check the words in between the two spans and assign a negative polarity
    // if a negative phrase is contained within the words between the two spans
    public Polarity assignPolarity(String inBetween, Set<String> negationPhrases) {
        // System.out.println(inBetween);
        for (String phrase : negationPhrases) {
            if (inBetween.contains(phrase)) {
                // System.out.println("negative");
                return Polarity.NEGATIVE;
            }
        }
        // System.out.println("positive");
        return Polarity.POSITIVE;
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
            Polarity polarity = assignPolarity(inBetween, negationPhrases);

            EventEventRelationMention.Builder newEventEventRelationMention = new EventEventRelationMention.Builder();
            newEventEventRelationMention.relationType(eventEventRelationMentionOld.relationType())
                    .leftEventMention(makeArgument(leftEventMention, "arg1"))
                    .rightEventMention(makeArgument(rightEventMention, "arg2"))
                    .confidence(eventEventRelationMentionOld.confidence())
                    .pattern(eventEventRelationMentionOld.pattern())
                    .model(eventEventRelationMentionOld.model())
                    .polarity(polarity).triggerText(eventEventRelationMentionOld.triggerText());
            resolvedEERMs.add(newEventEventRelationMention.build());
        }
        newDT.eventEventRelationMentions(EventEventRelationMentions.create(resolvedEERMs.build()));
        return newDT.build();
    }

    public static void main(String[] args) throws Exception{
        String exampleDir = "/d4m/ears/expts/47837.072220.v1/expts/hume_test.072220.cx.v1/pyserif/pyserif_confidence_calibration/0/output";
        EventEventRelationPolarityResolver eventEventRelationPolarityResolver = new EventEventRelationPolarityResolver("/nfs/ld100/u10/jcai/new_7_23_2020/Hume/resource/causal_relation_word_lists/negation.txt");
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builder().build();
        for(File file :new File(exampleDir).listFiles()){
            DocTheory docTheory = serifXMLLoader.loadFrom(file);
            DocTheory resolvedDocTheory = eventEventRelationPolarityResolver.resolve(docTheory);
            // Write back logic is not needed here for debugging purpose
        }
    }
}
