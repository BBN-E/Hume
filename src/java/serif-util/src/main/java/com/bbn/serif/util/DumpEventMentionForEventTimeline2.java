package com.bbn.serif.util;

import com.bbn.bue.common.temporal.Timex2Time;
import com.bbn.serif.io.SerifIOUtils;
import com.bbn.serif.io.SerifXMLLoader;
import com.bbn.serif.theories.*;
import com.bbn.serif.theories.actors.ActorEntity;
import com.bbn.serif.types.EntityType;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableSet;
import org.joda.time.Interval;

import java.io.*;
import java.util.*;

public class DumpEventMentionForEventTimeline2 {


    public static List<String> readLinesIntoList(String file) throws IOException {
        List<String> lines = new ArrayList<>();
        int nLine = 0;


        BufferedReader reader;
        String sline;
        for(reader = new BufferedReader(new FileReader(file)); (sline = reader.readLine()) != null; lines.add(sline)) {

        }

        reader.close();


        return lines;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonTypeInfo(use=JsonTypeInfo.Id.MINIMAL_CLASS, include=JsonTypeInfo.As.PROPERTY, property="@class")
    public static class EventArgumentEntry{
        @JsonProperty
        String type;
        @JsonProperty
        String canonicalText;
        @JsonProperty
        int argStartIdx;
        @JsonProperty
        int argEndIdx;

        public EventArgumentEntry(@JsonProperty String type,
                                  @JsonProperty String canonicalText,
                                  @JsonProperty int argStartIdx,
                                  @JsonProperty int argEndIdx
        ){
            this.type = type;
            this.canonicalText = canonicalText;
            this.argStartIdx = argStartIdx;
            this.argEndIdx =argEndIdx;
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
    public static class EventFrame {

        @JsonProperty
        final String docId;
        @JsonProperty
        final int sentIdx;
        @JsonProperty
        final int anchorStartIdx;
        @JsonProperty
        final int anchorEndIdx;
        @JsonProperty
        final List<String> sentInTokens;
        @JsonProperty
        final String eventType;
        @JsonProperty
        final long startTime;
        @JsonProperty
        final long endTime;
        @JsonProperty
        final List<EventArgumentEntry> arguments;

        @Override
        public boolean equals(Object o){
            if(!(o instanceof EventFrame))return false;
            EventFrame that = (EventFrame)o;
            return this.docId.equals(that.docId) &&
                    this.sentIdx == that.sentIdx &&
                    this.anchorStartIdx == that.anchorStartIdx &&
                    this.anchorEndIdx == that.anchorEndIdx &&
                    this.eventType.equals(that.eventType) &&
                    this.startTime == that.startTime &&
                    this.endTime == that.endTime;
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

        public EventFrame(@JsonProperty String docId,
                          @JsonProperty int sentIdx,
                          @JsonProperty int anchorStartIdx,
                          @JsonProperty int anchorEndIdx,
                          @JsonProperty List<String> sentInTokens,
                          @JsonProperty String eventType,
                          @JsonProperty List<EventArgumentEntry> arguments,
                          @JsonProperty long startTime,
                          @JsonProperty long endTime){
            this.docId = docId;
            this.sentIdx = sentIdx;
            this.anchorStartIdx = anchorStartIdx;
            this.anchorEndIdx = anchorEndIdx;
            this.sentInTokens = sentInTokens;
            this.eventType = eventType;
            this.arguments = arguments;
            this.startTime = startTime;
            this.endTime = endTime;
        }
    }

    static EventArgumentEntry getEventMentionArg(EventMention.MentionArgument mentionArgument, DocTheory docTheory) {
        String role = mentionArgument.role().asString();
        Optional<String> argCanonicalNameOptional = Optional.absent();
        Mention mention = mentionArgument.mention();
        Optional<Entity> entityOptional = mention.entity(docTheory);
        if(entityOptional.isPresent()) {
            ImmutableSet<ActorEntity> actorEntities = docTheory.actorEntities().forEntity(entityOptional.get());
            if(!actorEntities.isEmpty()) {
                ActorEntity actorEntity = actorEntities.iterator().next();
                argCanonicalNameOptional = Optional.of(actorEntity.actorName().asString());
            }
            else if(entityOptional.get().representativeName().isPresent()){
                argCanonicalNameOptional = Optional.of(entityOptional.get().representativeName().get().mention().span().tokenizedText().utf16CodeUnits());
            }
        }
        String argCanonicalName = argCanonicalNameOptional.isPresent()?argCanonicalNameOptional.get():"NA";

        return new EventArgumentEntry(role,argCanonicalName,mention.span().startToken().index(),mention.span().endToken().index());
    }

    static Optional<Pair<Long,Long>> getEventTimeArgDesc(EventMention.ValueMentionArgument valueMentionArgument, DocTheory docTheory) {
        long earlyestStartTime = Long.MAX_VALUE;
        long latestEndTime = Long.MIN_VALUE;

        Optional<Value> potentialValueObj = valueMentionArgument.valueMention().documentValue();
        if (potentialValueObj.isPresent()) {
            Value potentialTimeValObj = potentialValueObj.get();
            if (potentialTimeValObj.asTimex2().isPresent()) {
                Timex2Time potentialTimex2Obj = potentialTimeValObj.asTimex2().get();
                if (potentialTimex2Obj.valueAsInterval().isPresent()) {
                    Interval interval = potentialTimex2Obj.valueAsInterval().get();
                    long unixtimestampStart = interval.getStart().toDateTimeISO().getMillis();
                    long unixtimestampEnd = interval.getEnd().toDateTimeISO().getMillis();
                    earlyestStartTime = Math.min(earlyestStartTime,unixtimestampStart);
                    latestEndTime = Math.max(latestEndTime,unixtimestampEnd);
                }
            }
        }
        if(earlyestStartTime < Long.MAX_VALUE){
            return Optional.of(new Pair<>(earlyestStartTime,latestEndTime));
        }
        return Optional.absent();
    }


    public static void worker(String serifxmlFilePath, Writer writer) throws Exception{
        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().build();
        Map<EntityType, Map<String,Integer>> remainingMap = new HashMap<>();
        List<File> buf1 = new ArrayList<>();
        buf1.add(new File(serifxmlFilePath));
        DocTheory dt = SerifIOUtils.docTheoriesFromFiles(buf1, serifXMLLoader).iterator().next();
        Set<EventFrame> outputBuffer = new HashSet<>();
        for(SentenceTheory st:dt.sentenceTheories()){
            List<String> sentenceInTokens = new ArrayList<>();
            for(Token token: st.tokenSequence()){
                sentenceInTokens.add(token.tokenizedText().utf16CodeUnits());
            }
            for(EventMention eventMention : st.eventMentions()){
                List<EventArgumentEntry> eventArgumentEntryList = new ArrayList<>();
                long earlyestStartTime = Long.MAX_VALUE;
                long latestEndTime = Long.MIN_VALUE;
                boolean shouldAdded = false;
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

                        if(valueMentionArgument.role().asString().toLowerCase().contains("time")){
                            Optional<Pair<Long,Long>> argDescOptional = getEventTimeArgDesc(valueMentionArgument, dt);
                            if(argDescOptional.isPresent()) {
                                earlyestStartTime = Math.min(argDescOptional.get().getFirst(),earlyestStartTime);
                                latestEndTime = Math.max(argDescOptional.get().getSecond(),latestEndTime);
                                shouldAdded = true;
                            }
                        }
                    }
                }
                if(shouldAdded) {
                    for(EventMention.EventType eventType:eventMention.factorTypes()){
                        outputBuffer.add(new EventFrame(
                                dt.docid().asString(),
                                st.sentenceNumber(),
                                eventMention.semanticPhraseStart().get(),
                                eventMention.semanticPhraseEnd().get(),
                                sentenceInTokens,
                                eventType.eventType().asString(),
                                eventArgumentEntryList,
                                earlyestStartTime,
                                latestEndTime
                        ));
                    }
                }
            }
        }

        for(EventFrame eventMentionWithTime:outputBuffer){
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
