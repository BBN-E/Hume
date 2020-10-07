package com.bbn.serif.util;

import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.*;
import com.google.common.base.Optional;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Multiset;
import org.apache.commons.lang3.tuple.Triple;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

public class CalibrateConfidences {

    public static List<String> readLinesIntoList(String file) throws IOException {
        List<String> lines = new ArrayList<>();
        int nLine = 0;
        BufferedReader reader;
        String sline;
        for (reader = new BufferedReader(new FileReader(file)); (sline = reader.readLine()) != null; lines.add(sline)) {
            if (nLine++ % 100000 == 0) {
                System.out.println("# lines read: " + nLine);
            }
        }
        reader.close();
        return lines;
    }

    public static DocTheory rewriteRelationMentionConfidences(final DocTheory docTheory, Map<Triple<String, String, String>, Double> eventRelationTriples2confidence) {
        final DocTheory.Builder docBuilder = docTheory.modifiedCopyBuilder();

        ImmutableList.Builder<EventEventRelationMention> eventEventRelationMentions = ImmutableList.builder();


        for(EventEventRelationMention eventEventRelationMention : docTheory.eventEventRelationMentions()) {
            if(eventEventRelationMention.confidence().isPresent()) { // do not change the confidence if it's available
                eventEventRelationMentions.add(eventEventRelationMention);
            } else { // calibrate the confidence
                Optional<Triple<String, String, String>> tripleOptional = getRelationTriple(eventEventRelationMention, docTheory);
                double confidence = 0.55f; // default confidence is 0.55
                if (tripleOptional.isPresent() && eventRelationTriples2confidence.containsKey(tripleOptional.get())) {
                    confidence = eventRelationTriples2confidence.get(tripleOptional.get());
                }

                final EventEventRelationMention eerm = new EventEventRelationMention.Builder()
                        .relationType(eventEventRelationMention.relationType())
                        .leftEventMention(eventEventRelationMention.leftEventMention())
                        .rightEventMention(eventEventRelationMention.rightEventMention())
                        .confidence(confidence)
                        .pattern(eventEventRelationMention.pattern())
                        .model(eventEventRelationMention.model())
                        .build();
                eventEventRelationMentions.add(eerm);
            }
        }

        docBuilder.eventEventRelationMentions(EventEventRelationMentions.create(eventEventRelationMentions.build()));

        return docBuilder.build();
    }

    // This returns <Left event mention head text, relation type, right event mention head text>
    public static Optional<Triple<String, String, String>> getRelationTriple(EventEventRelationMention eventEventRelationMention, DocTheory docTheory) {
        if (eventEventRelationMention.leftEventMention() instanceof EventEventRelationMention.EventMentionArgument &&
                eventEventRelationMention.rightEventMention() instanceof EventEventRelationMention.EventMentionArgument) {
            EventMention leftArg = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.leftEventMention()).eventMention();
            EventMention rightArg = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.rightEventMention()).eventMention();
            String leftHeadText = leftArg.anchorNode().head().tokenSpan().tokenizedText(docTheory).utf16CodeUnits();
            String rightHeadText = rightArg.anchorNode().head().tokenSpan().tokenizedText(docTheory).utf16CodeUnits();
            String relationType = eventEventRelationMention.relationType().asString();

            Triple<String, String, String> triple = Triple.of(leftHeadText, relationType, rightHeadText);

            return Optional.of(triple);
        }
        else
            return Optional.absent();
    }

    public static void main(String [] args) throws IOException {
        String strListSerifXmlFiles = args[0];
        String strOutputDir = args[1];

        List<File> filesToProcess = new ArrayList<File>();
        List<String> listStringFiles = readLinesIntoList(strListSerifXmlFiles);
        for (String strFile : listStringFiles) {
            System.out.println("Reading " + strFile);
            filesToProcess.add(new File(strFile));
        }

        SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();

        Multiset<Triple<String, String, String>> eventRelationTriplesDenominator = HashMultiset.create(); // sum(count * 100)
        Multiset<Triple<String, String, String>> eventRelationTriplesNumerator = HashMultiset.create(); // sum(raw confidence * 100)
        Map<Triple<String, String, String>, Double> eventRelationTriples2confidence = new HashMap<Triple<String, String, String>, Double>(); // Averaged confidence

        for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
            for(EventEventRelationMention eventEventRelationMention : dt.eventEventRelationMentions()) {
                if (eventEventRelationMention.confidence().isPresent()) {
                    Optional<Triple<String, String, String>> triple = getRelationTriple(eventEventRelationMention, dt);
                    if(triple.isPresent()) {
                        double confidence = eventEventRelationMention.confidence().get();

                        int denominator = 100;
                        int numerator = (int) (100 * confidence);

                        eventRelationTriplesDenominator.add(triple.get(), denominator);
                        eventRelationTriplesNumerator.add(triple.get(), numerator);
                    }
                }
            }
        }

        // generate calibrated confidences for relations
        for(Triple<String, String, String> triple : eventRelationTriplesNumerator.elementSet())
            eventRelationTriples2confidence.put(triple, (double)eventRelationTriplesNumerator.count(triple)/eventRelationTriplesDenominator.count(triple));

        for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
            DocTheory docTheoryWithNewEvents = rewriteRelationMentionConfidences(dt, eventRelationTriples2confidence);

            String strOutputSerifXml = strOutputDir + "/" + dt.docid().asString() + ".xml";
            serifXMLWriter.saveTo(docTheoryWithNewEvents, strOutputSerifXml);
        }
    }
}
