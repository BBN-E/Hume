package com.bbn.serif.util;

import com.bbn.bue.common.files.FileUtils;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.io.SerifXMLWriter;
import com.bbn.serif.theories.*;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMentions;
import com.google.common.base.Optional;
import com.google.common.collect.*;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import javax.swing.text.html.Option;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

// Adds LDC events and event-event relations into SerifXML files
// This file draws heavily from EventEventRelationCreator

public class AddEventMentionFromLDC {
    /* START OF EVENT-EVENT RELATION CODE */
    // relation where the arguments are stored by offsets (CausalRelation from json)
    public static class RelationByOffset {
        JSONObject relation;
        String docID;
        String arg1Text;
        String arg2Text;
        Symbol semanticClass;
        Optional<String> pattern = Optional.absent();
        Optional<Double> confidence = Optional.absent();
        Optional<String> model = Optional.absent();
        long src_evt_id;
        long dst_evt_id;

        List<Pair<Long, Long>> arg1Offsets;
        List<Pair<Long, Long>> arg2Offsets;

        RelationByOffset(JSONObject relation) {
            this.relation = relation;
            this.docID = (String) relation.get("docid");
            this.arg1Text = (String) relation.get("arg1_text");
            this.arg2Text = (String) relation.get("arg2_text");
            this.src_evt_id = (long) relation.get("src_event_id");
            this.dst_evt_id = (long) relation.get("dst_event_id");
            this.semanticClass = Symbol.from( (String) relation.get("semantic_class") );
            this.arg1Offsets = getOffsets((JSONArray) relation.get("arg1_span_list"));
            this.arg2Offsets = getOffsets((JSONArray) relation.get("arg2_span_list"));
            if (relation.get("learnit_pattern") != null)
                this.pattern = Optional.of(getListOfPatterns((JSONArray)relation.get("learnit_pattern")));
            if (relation.get("confidence") != null)
                this.confidence = Optional.of((Double) relation.get("confidence"));
            if (relation.get("model") != null)
                this.model = Optional.of((String) relation.get("model"));
        }

        @Override
        public String toString() {
            StringBuilder stringBuilder = new StringBuilder();
            stringBuilder.append("docid: " + this.docID + ", ");
            stringBuilder.append("type: " + this.semanticClass + ", ");
            for(Pair<Long, Long> pair : this.arg1Offsets)
                stringBuilder.append("<a1: " + pair.getFirst().toString() + ", " + pair.getSecond().toString() + ">, ");
            for(Pair<Long, Long> pair : this.arg2Offsets)
                stringBuilder.append("<a2: " + pair.getFirst().toString() + ", " + pair.getSecond().toString() + ">, ");
            String ret = stringBuilder.toString().trim();
            if(ret.endsWith(","))
                ret = ret.substring(0, ret.length()-1);
            return ret;
        }

        @Override
        public int hashCode() {
            // note the hashcode does not include tokenSequence in order to avoid an infinite loop with
            // TokenSequence's hashCode!
            // return Objects.hash(this.docID, this.semanticClass, this.arg1Offsets.hashCode(), this.arg2Offsets.hashCode());
            return Objects.hash(this.toString());
        }

        @Override
        public boolean equals(final Object obj) {
            // note that equality does not look at the token sequence object to avoid an infinite loop
            // with TokenSequence's equality
            if (this == obj) {
                return true;
            }
            if (obj == null || getClass() != obj.getClass()) {
                return false;
            }
            final RelationByOffset other = (RelationByOffset) obj;

            if(this.toString().equals(other.toString()))
                return true;
            else
                return false;
        }

        boolean isTwoArrayListsWithSameValues(List<Pair<Long, Long>> list1, List<Pair<Long, Long>> list2)
        {
            //null checking
            if(list1==null && list2==null)
                return true;
            if((list1 == null && list2 != null) || (list1 != null && list2 == null))
                return false;

            if(list1.size()!=list2.size())
                return false;
            for(Object itemList1: list1)
            {
                if(!list2.contains(itemList1))
                    return false;
            }

            return true;
        }

        List<Pair<Long, Long>> getOffsets(JSONArray offsetList) {
            List<Pair<Long, Long>> results = new ArrayList<>();
            Iterator<JSONArray> iterator = offsetList.iterator();
            while (iterator.hasNext()) {
                JSONArray offsetPair = iterator.next();
                Long s = (Long) offsetPair.get(0);
                Long e = (Long) offsetPair.get(1);
                Pair<Long, Long> offsets = new Pair<>(s, e);
                results.add(offsets);
            }
            return results;
        }

        String getListOfPatterns(JSONArray learnPatterns) {
            StringBuilder stringBuilder = new StringBuilder();
            Iterator<Object> iterator = learnPatterns.iterator();
            while (iterator.hasNext()) {
                String learnitPattern = (String) iterator.next();
                stringBuilder.append("\t" + learnitPattern);
            }
            return stringBuilder.toString().trim();
        }
    }

    // Maps docid to list of relations read from json
    private static HashMap<String, ArrayList<RelationByOffset>> documentRelations;
    private static JSONParser parser;
    public static int eerCount;
    public static int dedupicatedCount = 0;
    public static HashSet<String> badEvents = new HashSet<>();

    static ArrayList<RelationByOffset> deduplicateRelations(ArrayList<RelationByOffset> relations) throws Exception {
        Map<String, RelationByOffset> string2relations = new HashMap<String, RelationByOffset>();

        for (RelationByOffset r1 : relations) {
            if(!string2relations.containsKey(r1.toString())) {
                string2relations.put(r1.toString(), r1);
            } else {
                System.out.println("duplicate relation: " + r1.toString());
                throw new Exception("duplicate relation");
            }

            RelationByOffset relationByOffset = string2relations.get(r1.toString());

            if(r1.equals(relationByOffset)) {
                if (r1.confidence.isPresent() && !relationByOffset.confidence.isPresent())
                    relationByOffset.confidence = r1.confidence;
                if (r1.pattern.isPresent() && !relationByOffset.pattern.isPresent())
                    relationByOffset.pattern = r1.pattern;
            }

            string2relations.put(relationByOffset.toString(), relationByOffset);
        }

        return new ArrayList<RelationByOffset>(string2relations.values());
    }

    static void findExactMatchEventsInRelationArgs(
            final RelationByOffset relation, final DocTheory dt,
            List<EventMention> allArg1s, List<EventMention> allArg2s)
    {
        String causeKey = relation.docID + "#" + Long.toString(relation.src_evt_id);
        String effectKey = relation.docID + "#" + Long.toString(relation.dst_evt_id);
        if (badEvents.contains(causeKey)) {
            System.out.println(causeKey);
            throw new IllegalArgumentException("causeKey is illegal");
        }
        if (badEvents.contains(effectKey)) {
            System.out.println(effectKey);
            throw new IllegalArgumentException("effectKey is illegal");
        }
        allArg1s.add(eventIdToEventMention.get(causeKey));
        allArg2s.add(eventIdToEventMention.get(effectKey));


        /* for (Pair<Long, Long> offset : relation.arg1Offsets) {
            allArg1s.addAll(findExactMatchEventsInSpan(offset, dt));
            System.out.println("allarg1s: " + Integer.toString(allArg1s.size()));
        }
        for (Pair<Long, Long> offset : relation.arg2Offsets) {
            allArg2s.addAll(findExactMatchEventsInSpan(offset, dt));
            System.out.println("allarg2s: " + Integer.toString(allArg2s.size()));
            // print(allArg2s.size(v));
        }*/
    }

    /* Requires that documentRelations be filled */
    private static DocTheory augmentDocTheoryWithCausalRelations(DocTheory dt) throws Exception {
        final DocTheory.Builder newDT = dt.modifiedCopyBuilder();

        if (!documentRelations.containsKey(dt.docid().toString())) {
            newDT.eventEventRelationMentions(EventEventRelationMentions.createEmpty());
            return newDT.build();
        }

        ArrayList<RelationByOffset> rawRelations = documentRelations.get(dt.docid().toString());
        ArrayList<RelationByOffset> relations = deduplicateRelations(rawRelations);
        dedupicatedCount += relations.size();

        final ImmutableList.Builder<EventEventRelationMention> results = ImmutableList.builder();

        for (RelationByOffset relation : relations) {

            // ICEWSEventMention objects
            List<ICEWSEventMention> allArg1sICEWS = new ArrayList<>();
            List<ICEWSEventMention> allArg2sICEWS = new ArrayList<>();

            // EventMention objects
            List<EventMention> allArg1sSerif = new ArrayList<>();
            List<EventMention> allArg2sSerif = new ArrayList<>();

            findExactMatchEventsInRelationArgs(
                    relation, dt, allArg1sSerif, allArg2sSerif);

            // These will store either ICEWSEventMentions or EventMentions
            List<Object> allArg1s = new ArrayList<>();
            List<Object> allArg2s = new ArrayList<>();


            allArg1s.addAll(allArg1sSerif);
            allArg2s.addAll(allArg2sSerif);

            if (allArg1s.size() == 0 || allArg2s.size() == 0) {
                System.out.println(relation.arg1Offsets);
                System.out.println(relation.arg2Offsets);
                System.out.println(relation.docID);
                // System.out.println(offsetCorrections.get(relation.docID));
                System.out.println(relation.arg1Text);
                System.out.println(relation.arg2Text);
                System.out.println(relation.semanticClass);
                System.out.println(relation.src_evt_id);
                System.out.println(relation.dst_evt_id);
                //continue;
                throw new IllegalArgumentException("relation does not seem to have arguments");
            }
            // continue;

            addEventPairsAsCausal(results, allArg1s, allArg2s, relation);
        }

        newDT.eventEventRelationMentions(EventEventRelationMentions.create(results.build()));
        return newDT.build();
    }

    static void addEventPairsAsCausal(
            ImmutableList.Builder<EventEventRelationMention> results,
            List<Object> allArg1s, List<Object> allArg2s, RelationByOffset relation)
    {
        for (Object arg1 : allArg1s) {
            for (Object arg2 : allArg2s) {
                EventEventRelationMention.Argument leftArg = makeArgument(arg1, "arg1");
                EventEventRelationMention.Argument rightArg = makeArgument(arg2, "arg2");
                eerCount += 1;
                final EventEventRelationMention eerm = new EventEventRelationMention.Builder()
                        .relationType(relation.semanticClass)
                        .leftEventMention(leftArg)
                        .rightEventMention(rightArg)
                        .build();
                results.add(eerm);
            }
        }
    }

    static EventEventRelationMention.Argument makeArgument(Object objectArg, String role) {
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

    // process json files and add them to documentRelations
    public static void loadJsonFile(File jsonFile) throws Exception{
        System.out.println("Loading " + jsonFile.getAbsolutePath());
        BufferedReader bufferedReader = null;
        int num_event_event_relations = 0;
        try {
            bufferedReader = new BufferedReader(new FileReader(jsonFile));
            Object obj = parser.parse(bufferedReader);
            JSONArray jsonArray = (JSONArray) obj;
            Iterator<JSONObject> iterator = jsonArray.iterator();
            while (iterator.hasNext()) {
                num_event_event_relations += 1;
                JSONObject relationJson = iterator.next();
                RelationByOffset rbo = new RelationByOffset(relationJson);
                if (!documentRelations.containsKey(rbo.docID))
                    documentRelations.put(rbo.docID, new ArrayList<>());
                documentRelations.get(rbo.docID).add(rbo);
            }
            System.out.println(Integer.toString(num_event_event_relations) + " relations loaded from json");
        } catch (Exception e) {
            throw e;
        }
        finally {
            try{
                if(bufferedReader!= null)bufferedReader.close();
            }
            catch (Exception e) {
                throw e;
            }
        }
    }
    /* END OF EVENT-EVENT RELATION CODE */

    /* START OF EVENT MENTION CODE */
    static Multimap<String, EventMentionInfoLDC> ldc_docid2eventmentions = HashMultimap.create();
    static HashMap<String, EventMention> eventIdToEventMention = new HashMap<>();
    static Map<String, Integer> doc2corrections = new HashMap<String, Integer>(); // offset corrections for each doc (used during annotation matching phase)

    static Set<String> eventIdSet = new HashSet<>(); // event id's processed during reading of event file
    static Set<String> eventIdSet_added = new HashSet<>(); // event id's that are actually added to the serifxml
    static int addedEventCount = 0; // number of events actually added
    static boolean DEBUG = false;

    // Check if s1_start/s1_end is contained with s2_start/s2_end (inclusive)
    public static boolean isInRange(int s1_start, int s1_end, int s2_start, int s2_end) {
        return s1_end<=s2_end && s1_end>=s2_start &&
                s1_start>=s2_start && s1_start<=s2_end;
    }

    // Examine the tokens in sentenceTheory, examining if there is an anchor node inside the sentenceTheory that exists within the eventMentionInfo offsets.
    // The anchor node is the last such token within the eventMentionInfo offsets.
    // The sentenceTheory token must have an offset correction applied to it, since we are comparing the offsets in the 'event annotation' space.
    // If no anchor node can be found, there is an issue: either with the event annotation itself or the SerifXML.
    public static Optional<SynNode> findAnchorNode(DocTheory docTheory, SentenceTheory sentenceTheory, EventMentionInfoLDC eventMentionInfo) {

        Optional<Token> bestToken = Optional.absent();
        for(int tid = sentenceTheory.tokenSequence().size()-1; tid>=0; tid--) {
            Token token = sentenceTheory.tokenSequence().token(tid);

            int num_char_correction = doc2corrections.get(docTheory.docid().asString());
            int token_start = token.startCharOffset().asInt() + num_char_correction;
            int token_end = token.endCharOffset().asInt() + num_char_correction;

            int em_start = eventMentionInfo.triggerOffset.getFirst().intValue();
            int em_end = eventMentionInfo.triggerOffset.getSecond().intValue();

            /*System.out.println("docid: " + docTheory.docid().asString());

            System.out.println("token: " + token_start + ", " + token_end);
            System.out.println("token " + token.tokenSpan().tokenizedText(docTheory).utf16CodeUnits() + "\t" + "sent: " + sentenceTheory.tokenSpan().tokenizedText(docTheory).utf16CodeUnits());

            System.out.println("eventMentionInfo: " + em_start + ", " + em_end);*/
            if (isInRange(token_start, token_end, em_start, em_end)) {
                if (DEBUG) {
                    System.out.println("em: " + eventMentionInfo.trigger_text);
                    System.out.println("token " + token.tokenSpan().tokenizedText(docTheory).utf16CodeUnits() + "\t" + "sent: " + sentenceTheory.tokenSpan().tokenizedText(docTheory).utf16CodeUnits());
                    System.out.print("--------");
                }

                bestToken = Optional.of(token);
                break;
            }
        }

        if(bestToken.isPresent()) {
            return Optional.of(sentenceTheory.parse().nodeForToken(bestToken.get()));
        }

        return Optional.absent();
    }

    // Build an event from a single event mention, required for writing the new SerifXML file.
    public static Event fromSingleEventMention(EventMention eventMention) {
        ArrayList arguments = Lists.newArrayList();

        ArrayList eventmentions = Lists.newArrayList();
        eventmentions.add(eventMention);

        return new Event(arguments, (new com.bbn.serif.theories.EventMentions.Builder()).eventMentions(eventmentions).build(), eventMention.type(), eventMention.genericity(), eventMention.modality(), eventMention.polarity(), eventMention.tense()
                , null);
    }

    // For the DocTheory input, attempt to add LDC event mentions into each of the sentenceTheory's of input.
    // If the LDC event mention cannot be added, use badEventWriter to write to a bad_events file.
    public static DocTheory addEventMentions(final DocTheory input, BufferedWriter badEventWriter) {
        final DocTheory.Builder docBuilder = input.modifiedCopyBuilder();
        int eventsAdded = 0;

        Multimap<Integer, EventMention> sid2em = HashMultimap.create();

        List<Event> events = new ArrayList<Event>();

        for(EventMentionInfoLDC eventMentionInfo : ldc_docid2eventmentions.get(input.docid().asString())) {
            boolean foundSynNode = false;
            String eventMentionInfoKey = input.docid().asString() + "#" + eventMentionInfo.getTriggerId();

            for (int i = 0; i < input.numSentences(); ++i) {
                final SentenceTheory st = input.sentenceTheory(i);
                Optional<SynNode> anchorNode = findAnchorNode(input, st, eventMentionInfo);

                if (anchorNode.isPresent()) {
                    EventMention em = EventMention
                            .builder(Symbol.from(eventMentionInfo.eventType))
                            .setAnchorNode(anchorNode.get())
                            .setAnchorPropFromNode(st)
                            .setScore(1.0)
                            .build();

                    if (DEBUG) {
                        System.out.println("SynNode: " + anchorNode.get().tokenSpan().tokenizedText(input) + "\t" + "text: " + eventMentionInfo.trigger_text.get());
                        System.out.println("docId: " + input.docid().asString() + " triggerId: " + eventMentionInfo.getTriggerId() + " offset1: " + anchorNode.get().tokenSpan().startCharOffset() + " offset2: " + anchorNode.get().tokenSpan().endCharOffset());
                    }

                    sid2em.put(i, em);
                    foundSynNode = true;
                    addedEventCount += 1;
                    if (eventIdSet_added.contains(eventMentionInfoKey)) {
                        throw new IllegalArgumentException("event mention info already recorded");
                    } else {
                        eventIdSet_added.add(eventMentionInfoKey);
                    }
                    eventIdToEventMention.put(eventMentionInfoKey, em);
                    break;
                }
            }

            if(!foundSynNode) {
                try {
                    if (badEventWriter != null) {
                        badEventWriter.write(eventMentionInfoKey);
                        badEventWriter.newLine();
                        badEvents.add(eventMentionInfoKey);
                    }
                }
                catch (Exception e) {
                    System.out.println("Error writing to file");
                }

                if (DEBUG) {
                    System.out.println("docId: " + input.docid().asString() + " triggerId: " + eventMentionInfo.getTriggerId());
                    System.out.println("Can't add event mention");
                }
            }
        }

        for (int i = 0; i < input.numSentences(); ++i) {
            final SentenceTheory st = input.sentenceTheory(i);
            final SentenceTheory.Builder sentBuilder = st.modifiedCopyBuilder();

            final ImmutableList.Builder<EventMention> newEventMentions =
                    ImmutableList.builder();

            for(EventMention eventMention : sid2em.get(i)) {
                newEventMentions.add(eventMention);
                events.add(fromSingleEventMention(eventMention));
            }

            sentBuilder.eventMentions(new EventMentions.Builder()
                    .eventMentions(newEventMentions.build())
                    .build());

            docBuilder.replacePrimarySentenceTheory(st, sentBuilder.build());
        }


        docBuilder.events(Events.create(events));
        docBuilder.icewsEventMentions(ICEWSEventMentions.createEmpty());

        if (eventsAdded > 0) {
            System.out.println("Added " + eventsAdded + " events to " + input.docid());
        }

        return docBuilder.build();
    }

    // Add all lines from file into a List<String>
    public static List<String> readLinesIntoList(String file) throws IOException {
        List<String> lines = new ArrayList<>();
        int nLine = 0;
        BufferedReader reader;
        String sline;
        for (reader = new BufferedReader(new FileReader(file)); (sline = reader.readLine()) != null; lines.add(sline)) {
            if (nLine++ % 100000 == 0) {
                if (DEBUG) {
                    System.out.println("# lines read: " + nLine);
                }
            }
        }
        reader.close();
        return lines;
    }

    // Load the event mentions from the event annotation file, updating docid2eventmentions accordingly.
    // Only the unique event triggers are recorded.
    public static Multimap<String, EventMentionInfoLDC> load_ldc_event_mentions(String fileLdcAnnotation, Multimap<String, EventMentionInfoLDC> docid2eventmentions) throws IOException {
        String filename = fileLdcAnnotation;
        final List<String> lines = readLinesIntoList(filename);
        int eventCount = 0;
        int num_lines = 0;

        for (String line : lines) {
            line = line.trim();
            try {
                String[] items = line.split("\t");

                String docid = items[1];
                String trigger_text = items[4];
                String type = items[5];
                String subtype = items[6];
                String subsubtype = items[7];

                String trigger_id = items[3];

                long char_start = Integer.parseInt(items[12]);
                long char_end = Integer.parseInt(items[13]);

                String eventType = type + "-" + subtype + "-" + subsubtype;

                Optional<Pair<Long, Long>> absent = Optional.absent();

                num_lines += 1;
                if (DEBUG) {
                    System.out.println("docid\t" + docid + "\t" + eventType + "\t" + char_start + "\t" + char_end);
                }

                // Since we are recording event triggers only, avoid duplicates in the annotation.
                if (eventIdSet.contains(docid + "#" + trigger_id)) {
                    continue;
                } else {
                    eventIdSet.add(docid + "#" + trigger_id);
                }

                Multimap<String, Map<String, String>> roleOffset = HashMultimap.create();
                EventMentionInfoLDC eventMentionInfo = new EventMentionInfoLDC(eventType, docid, absent, new Pair<Long, Long>(char_start, char_end), roleOffset, 1.0f, trigger_id);
                eventMentionInfo.setTriggerText(trigger_text);
                docid2eventmentions.put(docid, eventMentionInfo);
                eventCount += 1;
            } catch (Exception e) {
                if (DEBUG) {
                    e.printStackTrace();
                    System.out.println("line = " + line);
                }
            }
        }

        System.out.println("Number of lines in event annotation file: " + Integer.toString(num_lines));
        if (DEBUG) {
            System.out.println("eventCount: " + Integer.toString(eventCount));
        }
        return docid2eventmentions;
    }
    /* END OF EVENT MENTION CODE */

    // Returns the extension of a file, i.e. for a.b.c.list, list will be output.
    private static String getFileExtension(String fileName) {
        if(fileName.lastIndexOf(".") != -1 && fileName.lastIndexOf(".") != 0)
            return fileName.substring(fileName.lastIndexOf(".")+1);
        else return "";
    }

    // Read in metadata file and extract the offset (it is a negative number, to account for the transformation into event annotation space).
    // This offset is negative because the sgm file contains some header information that does not exist in the original annotation.
    public static Map<String, Integer> load_offset_correction(String metadataFile) {
        Map<String, Integer> doc2corrections = new HashMap<String, Integer>();

        try {
            List<String> lines = readLinesIntoList(metadataFile);
            for(String line : lines) {
                line = line.trim();
                if(line.isEmpty())
                    continue;

                String [] items = line.split("\t");
                doc2corrections.put(items[0].trim(), Integer.parseInt(items[7]));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return doc2corrections;
    }

    public static void main(String[] args) throws Exception {
        String strListSerifXmlFiles = args[0];
        String strOutputDir = args[1];
        String fileLdcAnnotation = args[2];
        System.out.println(fileLdcAnnotation);
        String metadataFile = args[3];
        boolean write_serifxml = Boolean.parseBoolean(args[4]);
        String eerJsonFile = args[5];

        // In the case that the fileLdcAnnotation is a list, this means that there are multiple event annotation files (e.g. in drop E83).
        // Process all the event annotation files, continuously updating the same ldc_docid2eventmentions map.
        if (getFileExtension(fileLdcAnnotation).equals("list")) {
            List<String> listStringFiles = readLinesIntoList(fileLdcAnnotation);
            System.out.println("List of files: " + listStringFiles);
            for (String filename : listStringFiles) {
                ldc_docid2eventmentions = load_ldc_event_mentions(filename, ldc_docid2eventmentions);
            }
        } else {
            ldc_docid2eventmentions = load_ldc_event_mentions(fileLdcAnnotation, ldc_docid2eventmentions);
        }

        doc2corrections = load_offset_correction(metadataFile);

        BufferedWriter badEventWriter = null;
        if (!write_serifxml) {
            File badEventFile = new File(strOutputDir + "/bad_events");
            FileOutputStream badeventFOS = new FileOutputStream(badEventFile);
            badEventWriter = new BufferedWriter(new OutputStreamWriter(badeventFOS));
        }

        List<File> serifFilesToProcess = new ArrayList<File>();
        List<String> listStringFiles = readLinesIntoList(strListSerifXmlFiles);
        for (String strFile : listStringFiles) {
            if (DEBUG) {
                System.out.println("Reading " + strFile);
            }
            serifFilesToProcess.add(new File(strFile));
        }

        SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();

        // Load EER's from json
        if (write_serifxml) {
            parser = new JSONParser();
            documentRelations = new HashMap<>();
            eerCount = 0;
            List<String> jsonInputs = new ArrayList<>();
            jsonInputs.add(eerJsonFile);
            for (String jsonInput : jsonInputs) {
                File jif = new File(jsonInput);
                if (jif.isFile())
                    loadJsonFile(jif);
                if (jif.isDirectory())
                    for (File jsonFile : jif.listFiles()) {
                        if (!jsonFile.isFile())
                            continue;
                        if (!jsonFile.getName().endsWith(".json"))
                            continue;
                        loadJsonFile(jsonFile);
                    }
            }
        }

        // Try to add event mentions to each docTheory
        for (final DocTheory dt : SerifIOUtils.docTheoriesFromFiles(serifFilesToProcess, serifXMLLoader)) {
            DocTheory docTheoryWithNewEvents = addEventMentions(dt, badEventWriter);

            // Actually write the new SerifXML file with the new docTheory
            if (write_serifxml) {
                DocTheory newDT = augmentDocTheoryWithCausalRelations(docTheoryWithNewEvents);
                String strOutputSerifXml = strOutputDir + "/" + newDT.docid().asString() + ".xml";
                serifXMLWriter.saveTo(newDT, strOutputSerifXml);
            }
        }
        System.out.println("Number of unique event triggers: " + eventIdSet.size());
        System.out.println("Number of event triggers actually added: " + Integer.toString(addedEventCount));
        System.out.println("Number of event-event relations actually added: " + Integer.toString(eerCount));

        if (badEventWriter != null) {
            badEventWriter.close();
        }
    }
}
