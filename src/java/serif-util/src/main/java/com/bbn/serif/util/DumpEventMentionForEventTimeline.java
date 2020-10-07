package com.bbn.serif.util;

import com.bbn.bue.common.temporal.Timex2Time;
import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.Entity;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.Value;
import com.bbn.serif.theories.actors.ActorEntity;
import com.bbn.serif.types.EntityType;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableSet;

import org.apache.commons.lang3.tuple.Triple;
import org.joda.time.Interval;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class DumpEventMentionForEventTimeline {

    public static List<String> readLinesIntoList(String file) {
        List<String> lines = new ArrayList<>();
        int nLine = 0;

        try {
            BufferedReader reader;
            String sline;
            for(reader = new BufferedReader(new FileReader(file)); (sline = reader.readLine()) != null; lines.add(sline)) {
                if (nLine++ % 100000 == 0) {
                    System.out.println("# lines read: " + nLine);
                }
            }

            reader.close();
        } catch (IOException var5) {
            var5.printStackTrace();
        }

        return lines;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonTypeInfo(use=JsonTypeInfo.Id.MINIMAL_CLASS, include=JsonTypeInfo.As.PROPERTY, property="@class")
    public static class EventArgumentEntry{
        @JsonProperty
        String type;
        @JsonProperty
        String originalText;
        @JsonProperty
        String canonicalText;
        @JsonProperty
        int argStart;
        @JsonProperty
        int argEnd;

        public EventArgumentEntry(@JsonProperty String type,
            @JsonProperty String originalText,
            @JsonProperty String canonicalText,
            @JsonProperty int argStart,
            @JsonProperty int argEnd
        ){
            this.type = type;
            this.originalText = originalText;
            this.canonicalText = canonicalText;
            this.argStart = argStart;
            this.argEnd =argEnd;
        }

        @Override
        public String toString(){
            ObjectMapper mapper = new ObjectMapper();
            try{
                return mapper.writeValueAsString(this);
            }
            catch (Exception e){
                return "";
            }
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonTypeInfo(use=JsonTypeInfo.Id.MINIMAL_CLASS, include=JsonTypeInfo.As.PROPERTY, property="@class")
    public static class EventMentionWithTime{

        @JsonProperty
        String docId;
        @JsonProperty
        int sentStart;
        @JsonProperty
        int sentEnd;
        @JsonProperty
        int anchorStart;
        @JsonProperty
        int anchorEnd;
        @JsonProperty
        String sentStr;
        @JsonProperty
        String anchorStr;
        @JsonProperty
        String eventType;
        @JsonProperty
        long unixtimestamp;
        @JsonProperty
        List<EventArgumentEntry> arguments;

        @Override
        public boolean equals(Object o){
            if(!(o instanceof EventMentionWithTime))return false;
            EventMentionWithTime that = (EventMentionWithTime)o;
            return this.docId.equals(that.docId) &&
                    this.sentStart == that.sentStart &&
                    this.sentEnd == that.sentEnd &&
                    this.anchorStart == that.anchorStart &&
                    this.anchorEnd == that.anchorEnd &&
                    this.eventType.equals(that.eventType) &&
                    this.unixtimestamp == that.unixtimestamp;
        }

        @Override
        public String toString(){
            ObjectMapper mapper = new ObjectMapper();
            try{
                return mapper.writeValueAsString(this);
            }
            catch (Exception e){
                return "";
            }
        }

        public EventMentionWithTime(@JsonProperty String docId,
                                    @JsonProperty int sentStart,
                                    @JsonProperty int sentEnd,
                                    @JsonProperty int anchorStart,
                                    @JsonProperty int anchorEnd,
                                    @JsonProperty String sentStr,
                                    @JsonProperty String anchorStr,
                                    @JsonProperty String eventType,
                                    @JsonProperty List<EventArgumentEntry> arguments,
                                    @JsonProperty long unixtimestamp){
            this.docId = docId;
            this.sentStart = sentStart;
            this.sentEnd = sentEnd;
            this.anchorStart = anchorStart;
            this.anchorEnd = anchorEnd;
            this.sentStr = sentStr;
            this.anchorStr = anchorStr;
            this.unixtimestamp = unixtimestamp;
            this.arguments = arguments;
            this.eventType = eventType;
        }
    }

    static EventArgumentEntry getEventMentionArg(EventMention.MentionArgument mentionArgument, DocTheory docTheory) {
        String role = mentionArgument.role().asString();
        String argText = mentionArgument.span().tokenizedText().utf16CodeUnits();
        Optional<String> argCanonicalNameOptional = Optional.absent();

        Mention mention = mentionArgument.mention();

        Optional<Entity> entityOptional = mention.entity(docTheory);
        if(entityOptional.isPresent()) {
            ImmutableSet<ActorEntity> actorEntities = docTheory.actorEntities().forEntity(entityOptional.get());
            if(!actorEntities.isEmpty()) {
                ActorEntity actorEntity = actorEntities.iterator().next();
                argCanonicalNameOptional = Optional.of(actorEntity.actorName().asString());
            }
        }

        String argCanonicalName = argCanonicalNameOptional.isPresent()?argCanonicalNameOptional.get():"NA";

        return new EventArgumentEntry(role,argText,argCanonicalName,mention.span().startCharOffset().asInt(),mention.span().endCharOffset().asInt());
    }

    static Optional<Triple<String, String, Long>> getEventTimeArgDesc(EventMention.ValueMentionArgument valueMentionArgument, DocTheory docTheory) {
        String role = valueMentionArgument.role().asString();
        String argText = valueMentionArgument.span().tokenizedText().utf16CodeUnits();
        Optional<Long> unixtimestampOptional = Optional.absent();

        Optional<Value> potentialValueObj = valueMentionArgument.valueMention().documentValue();
        if (potentialValueObj.isPresent()) {
            Value potentialTimeValObj = potentialValueObj.get();
            if (potentialTimeValObj.asTimex2().isPresent()) {
                Timex2Time potentialTimex2Obj = potentialTimeValObj.asTimex2().get();
                if (potentialTimex2Obj.valueAsInterval().isPresent()) {
                    Interval interval = potentialTimex2Obj.valueAsInterval().get();
                    long unixtimestamp = interval.getStart().toDateTimeISO().getMillis();

                    return Optional.of(Triple.of(role, argText, unixtimestamp));
                }
            }
        }

        return Optional.absent();
    }


    public static void worker(String serifxmlFilePath,Writer writer) throws Exception{
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();
        Map<EntityType,Map<String,Integer>> remainingMap = new HashMap<>();
        List<File> buf1 = new ArrayList<>();
        buf1.add(new File(serifxmlFilePath));
        DocTheory dt = SerifIOUtils.docTheoriesFromFiles(buf1, serifXMLLoader).iterator().next();
        Set<EventMentionWithTime> outputBuffer = new HashSet<>();
        for(SentenceTheory st:dt.sentenceTheories()){
            for(EventMention eventMention : st.eventMentions()){
                List<EventArgumentEntry> eventArgumentEntryList = new ArrayList<>();
                Optional<String> timeOriginalText = Optional.absent();
                Optional<Long> unixtimestampOptional = Optional.absent();

                for(EventMention.Argument argument:eventMention.arguments()){
                    if(argument instanceof EventMention.MentionArgument) {
                        EventMention.MentionArgument mentionArgument = (EventMention.MentionArgument) argument;
                        EventArgumentEntry argDesc = getEventMentionArg(mentionArgument, dt);

                        if(!argDesc.canonicalText.equals("NA"))
                            eventArgumentEntryList.add(argDesc);
                    }

                    // get time
                    if(argument instanceof EventMention.ValueMentionArgument) {
                        EventMention.ValueMentionArgument valueMentionArgument = (EventMention.ValueMentionArgument) argument;

                        if(valueMentionArgument.role().asString().toLowerCase().equals("time")){
                            Optional<Triple<String, String, Long>> argDescOptional = getEventTimeArgDesc(valueMentionArgument, dt);
                            if(argDescOptional.isPresent()) {
                                unixtimestampOptional = Optional.of(argDescOptional.get().getRight());
                                timeOriginalText = Optional.of(valueMentionArgument.span().tokenizedText().utf16CodeUnits());
                            }
                        }
                    }
                }

                SynNode head = eventMention.anchorNode();

                if(unixtimestampOptional.isPresent()) {
                    outputBuffer.add(new EventMentionWithTime(
                        dt.docid().asString(),
                        st.span().startCharOffset().asInt(),
                        st.span().endCharOffset().asInt(),
                        head.span().startCharOffset().asInt(),
                        head.span().endCharOffset().asInt(),
                        st.span().tokenizedText().utf16CodeUnits(),
                        head.span().tokenizedText().utf16CodeUnits(),
                        eventMention.type().asString(),
                        eventArgumentEntryList,
                        unixtimestampOptional.get()
                    ));
                }
            }
        }

        for(EventMentionWithTime eventMentionWithTime:outputBuffer){
            writer.write(eventMentionWithTime+"\n");
        }
    }


    public static void main(String[] args) throws Exception{
//        String fileName = "/nfs/raid87/u12/hqiu/runjob/expts/causeex_pipeline/causeex_m9_wm_m12/nn_events/00000/genericity_output/ENG_NW_20100923_4099.serifxml";
//        String listOfFiles = "/home/hqiu/ld100/CauseEx-pipeline-WM/CauseEx/experiments/causeex_pipeline/expts/ss_for_wm_m12.v1.small/event_consolidation_serifxml_out.list";
//        String outputLineJsonPath  = "/home/hqiu/massive/tmp/test.ljson";
        if(args.length != 2){
            System.err.println("Usage: input_serifxml_list output_ljson_path");
        }
        String listOfFiles = args[0];
        String outputLineJsonPath = args[1];
        List<String> listOfPath = readLinesIntoList(listOfFiles);
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(new File(outputLineJsonPath)));
        for(String strFile : listOfPath){
            worker(strFile,bufferedWriter);
        }
        bufferedWriter.close();
    }
}
