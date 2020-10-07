package com.bbn.serif.util;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.*;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.Sets;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;


public class AddEventMentionByPOSTags {

    // static ImmutableSet<String> freq_not_triggers = ImmutableSet.of("government", "people",
    //        "state", "country", "president","farmers", "Nigerians", "year",
    //        "sector", "has", "said", "years", "have", "countries", "children", "cent", "had", "women",
    //        "made", "states", "Mr.", "percent", "group", "areas", "members", "part", "region", "world",
    //        "way", "number", "nation", "level", "groups", "study", "administration", "area", "leaders",
    //        "information", "party", "communities", "see", "president");

    static Set<String> freq_not_triggers = new HashSet<String>();
    //static Set<String> freq_pos_and_triggers = new HashSet<String>();
    static Set<String> noun_triggers = Sets.newHashSet();

    public static int numberOfAlphabetsInString(final String text) {
        int count = 0;
        for(int cIndex=0; cIndex<text.length(); cIndex++) {
            final char c = text.charAt(cIndex);
            if (('a' <= c && c <= 'z') || ('A' <= c && c <= 'Z')) {
                count += 1;
            }
        }
        return count;
    }

    public static int numberOfDashInString(final String text) {
        int count = 0;
        for(int cIndex=0; cIndex<text.length(); cIndex++) {
            final char c = text.charAt(cIndex);
            if(c == '-') {
                count += 1;
            }
        }
        return count;
    }

    public static boolean isInValidEventMentionString(final String text) {
        int MAX_NUM_WORDS = 5;
        if(text.split(" ").length>MAX_NUM_WORDS)
            return true;

        for(String tokenText : text.split(" ")) {
            if (tokenText.indexOf("'") != -1 ||
                    (numberOfAlphabetsInString(tokenText) + numberOfDashInString(tokenText)) != tokenText.length() ||
                    numberOfAlphabetsInString(tokenText) < 2)
                return true;
        }

        return false;
    }

    public static DocTheory addEventMentions(final DocTheory input) {
        final DocTheory.Builder docBuilder = input.modifiedCopyBuilder();
        int eventsAdded = 0;
        for (int i = 0; i < input.numSentences(); ++i) {
            final SentenceTheory st = input.sentenceTheory(i);

            final SentenceTheory.Builder sentBuilder = st.modifiedCopyBuilder();
            final ImmutableList.Builder<EventMention> newEventMentions =
                    ImmutableList.builder();

            // keep existing event mentions
            for (EventMention eventMention : st.eventMentions()) {
                newEventMentions.add(eventMention);
            }

            // add verb or noun as mentions
            for (Proposition proposition : st.propositions().asList()) {
                if (proposition.predHead().isPresent()) {
                    String text = proposition.predHead().get().head().tokenSpan().originalText().content().utf16CodeUnits();
                    String predType = proposition.predType().name().asString();

                    if(isInValidEventMentionString(text)) {
                        //System.out.println("Skipping due to astrophe " + text);
                        //System.out.println("Skipping due to length " + text);
                        //System.out.println("Skipping due to numberOfAlphabetsInString " + text);
                        continue;
                    }

                    if (freq_not_triggers.contains(text.trim().toLowerCase()))
                        continue;
                    //String pos_and_trigger = pos_and_trigger(proposition.predHead().get().head().headPOS().asString(),
                    //        text);
                    //if(!freq_pos_and_triggers.contains(pos_and_trigger))
                    //    continue;

                    if (predType.equalsIgnoreCase("verb") || predType.equalsIgnoreCase("noun")) {
                        final SynNode currentNode = proposition.predHead().get().head();
                        final String headPOS = currentNode.headPOS().asString();
                        final String headText = currentNode.tokenSpan().originalText().content().utf16CodeUnits();

                        // skip anything that's not verb or noun
                        if (!headPOS.startsWith("N") && !headPOS.startsWith("V"))
                            continue;

                        // skip proper nouns
                        if (headPOS.startsWith("NNP"))
                            continue;

                        // this is a command noun, but not in the set of noun_triggers whitelist
                        if (headPOS.startsWith("NN") && !noun_triggers.contains(headText.toLowerCase())) {
                            continue;
                        }

                        List<EventMention> eventMentions = GenericEventDetector.getEventMentions(currentNode, st, input);

                        newEventMentions.addAll(eventMentions);
                        for (EventMention eventMention : eventMentions) {
                            ++eventsAdded;

                            // System.out.println("pos\t" + text + "\t" + currentNode.headPOS().asString());
                            System.out.println("[event]\tprop\tdocid: " + input.docid().asString()
                                    + "\tsid: " + i
                                    + "\ttriggerPOS: " + eventMention.anchorNode().head().headPOS().asString().trim()
                                    + "\ttrigger: " + eventMention.anchorNode().tokenSpan().originalText().content().utf16CodeUnits()
                                    + "\textended: " + eventMention.pattern().get().asString()
                                    + "\targs: " + getEventArguments(eventMention, input));
                        }
                    }
                }
            }

            // add mentions
            for (Mention mention : st.mentions()) {
                String entityType = mention.entityType().name().asUnicodeFriendlyString().utf16CodeUnits();
                String mentionType = mention.mentionType().name();

                String text = mention.tokenSpan().tokenizedText(input).utf16CodeUnits();
                String headText = mention.head().tokenSpan().tokenizedText(input).utf16CodeUnits();

                // remove invalid mention
                if(isInValidEventMentionString(text))
                    continue;

                if(!noun_triggers.contains(headText.toLowerCase()))
                    continue;

                if (entityType.equals("OTH") && mentionType.equals("DESC")) {
                    EventMention em = EventMention
                            .builder(Symbol.from("Event"))
                            .setAnchorNode(mention.head())
                            .setAnchorPropFromNode(st)
                            .setScore(0.2)
                            .setPatternID(Symbol.from(text.replace("\n", " ").replace("\t", " ")))
                            .build();
                    newEventMentions.add(em);

                    System.out.println("[event]\tmention\tdocid: " + input.docid().asString()
                            + "\tsid: " + i
                            + "\ttriggerPOS: " + mention.head().headPOS().asString().trim()
                            + "\ttrigger: " + headText
                            + "\ttrigger: " + text);
                }
            }

            sentBuilder.eventMentions(new EventMentions.Builder()
                    .eventMentions(newEventMentions.build())
                    .build());
            docBuilder.replacePrimarySentenceTheory(st, sentBuilder.build());
        }

        if (eventsAdded > 0) {
            System.out.println("Added " + eventsAdded + " events to " + input.docid());
        }

        return docBuilder.build();
    }

    public static String getEventArguments(EventMention eventMention, DocTheory docTheory) {
        StringBuilder stringBuilder = new StringBuilder();
        for (EventMention.Argument argument : eventMention.arguments()) {
            String arg = argument.span().tokenizedText(docTheory).utf16CodeUnits();
            stringBuilder.append(argument.role().asString() + ":" + arg + ", ");
        }
        return stringBuilder.toString().trim();
    }

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

    public static void load_trigger_black_list(String strFileBlackList) throws IOException {
        if (strFileBlackList.trim().equals("NA"))
            return;

        // String file = "/nfs/mercury-04/u42/bmin/projects/CauseEx/M9_assessment/relations/learnit/causeex_m9.add_verbs_nouns/m9.trigger.blacklist.v2";
        String file = strFileBlackList;
        List<String> lines = readLinesIntoList(file);
        for (String line : lines) {
            freq_not_triggers.add(line.trim().toLowerCase());
        }
    }

    public static String pos_and_trigger(String pos, String trigger) {
        return (pos.trim() + "." + trigger.trim()).toLowerCase();
    }

    public static void load_noun_trigger_list(final String filename) throws IOException {
        final List<String> lines = readLinesIntoList(filename);
        for (String line : lines) {
            line = line.trim();
            if (line.startsWith("#"))
                continue;

            noun_triggers.add(line);
        }
    }

    /*
    public static void load_trigger_white_list(String strFileWhiteList) {
        if(strFileWhiteList.trim().equals("NA"))
            return;

        // String file = "/nfs/ld100/u10/bmin/repo_clean_for_exp/CauseEx/lib/generic_events/wm-m12.trigger.whitelist.v1";
        String file = strFileWhiteList;
        List<String> lines = readLinesIntoList(file);
        for(String line : lines) {
            // skip stop words
            if(line.startsWith("0"))
                continue;

            String [] items = line.trim().split("\t");
            if(items.length==2) {
                String pos = items[0].trim();
                pos = pos.substring(pos.lastIndexOf(" ")+1).trim();

                String trigger = items[1];

                freq_pos_and_triggers.add(pos_and_trigger(pos, trigger));
            }
        }
    }
    */

    public static void main(String[] args) throws IOException {
        String strListSerifXmlFiles = args[0];
        String strOutputDir = args[1];

        String strFileWhiteList = args[2];
        String strFileBlackList = args[3];

        load_trigger_black_list(strFileBlackList);
        load_noun_trigger_list(strFileWhiteList);
        //load_trigger_white_list(strFileWhiteList);

        List<File> filesToProcess = new ArrayList<File>();
        List<String> listStringFiles = readLinesIntoList(strListSerifXmlFiles);
        for (String strFile : listStringFiles) {
            System.out.println("Reading " + strFile);
            filesToProcess.add(new File(strFile));
        }

        SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();

        // read sentence theories
        for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
            DocTheory docTheoryWithNewEvents = addEventMentions(dt);

            String strOutputSerifXml = strOutputDir + "/" + dt.docid().asString() + ".xml";
            serifXMLWriter.saveTo(docTheoryWithNewEvents, strOutputSerifXml);
        }

    }
}
