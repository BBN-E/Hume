package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.*;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Sets;

import java.util.*;

public class TrendEventDropper implements DocumentResolver, Resolver {

    static Set<String> trendTypes = Sets.newHashSet(
            "http://ontology.causeex.com/ontology/odps/Event#Increase",
            "http://ontology.causeex.com/ontology/odps/Event#Decrease"
    );

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

    @Override
    public DocTheory resolve(DocTheory dt) {
        Set<EventMention> droppedEMs = new HashSet<>();
        DocTheory.Builder newDt = dt.modifiedCopyBuilder();
        Map<EventMention,EventMention> oldEventMentionToNewEventMention = new HashMap<>();
        for(int sentid = 0;sentid < dt.numSentences();++sentid){
            SentenceTheory sentenceTheory = dt.sentenceTheory(sentid);
            EventMentions.Builder newEventMentions = new EventMentions.Builder();
            for(EventMention eventMention: sentenceTheory.eventMentions()){
                boolean onlyContainsTrendTypes = true;
                boolean containsTrendTypes = false;
                for(EventMention.EventType eventType: eventMention.eventTypes()){
                    if(trendTypes.contains(eventType.eventType().asString())){
                        containsTrendTypes = true;
                    }
                    else{
                        onlyContainsTrendTypes = false;
                    }
                }
                if(eventMention.factorTypes().size()>0){
                    onlyContainsTrendTypes = false;
                }
                if(containsTrendTypes && onlyContainsTrendTypes){
                    droppedEMs.add(eventMention);
                }
                else{
                    if(containsTrendTypes){
                        EventMention.Builder newEm = eventMention.modifiedCopyBuilder();
                        List<EventMention.EventType> eventTypes = new ArrayList<>();
                        for(EventMention.EventType eventType: eventMention.eventTypes()){
                            if(!trendTypes.contains(eventType.eventType().asString())){
                                eventTypes.add(eventType);
                            }
                        }
                        newEm.setEventTypes(eventTypes);
                        EventMention newEMBuilt = newEm.build();
                        oldEventMentionToNewEventMention.put(eventMention,newEMBuilt);
                        newEventMentions.addEventMentions(newEMBuilt);
                    }
                    else{
                        oldEventMentionToNewEventMention.put(eventMention,eventMention);
                        newEventMentions.addEventMentions(eventMention);
                    }
                }
            }
            newDt.replacePrimarySentenceTheory(sentenceTheory,sentenceTheory.modifiedCopyBuilder().eventMentions(newEventMentions.build()).build());
        }

        ImmutableList.Builder<EventEventRelationMention> resolvedEERMs = ImmutableList.builder();
        for (EventEventRelationMention eventEventRelationMentionOld : dt.eventEventRelationMentions()) {
            EventMention leftEventMention = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMentionOld.leftEventMention()).eventMention();
            EventMention rightEventMention = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMentionOld.rightEventMention()).eventMention();
            if(!droppedEMs.contains(leftEventMention) && !droppedEMs.contains(rightEventMention)){
                EventMention resolvedLeftEM = oldEventMentionToNewEventMention.getOrDefault(leftEventMention,leftEventMention);
                EventMention resolvedRightEM = oldEventMentionToNewEventMention.getOrDefault(rightEventMention,rightEventMention);
                EventEventRelationMention.Builder newEventEventRelationMention = new EventEventRelationMention.Builder();
                newEventEventRelationMention.relationType(eventEventRelationMentionOld.relationType())
                        .leftEventMention(makeArgument(resolvedLeftEM, "arg1"))
                        .rightEventMention(makeArgument(resolvedRightEM, "arg2"))
                        .confidence(eventEventRelationMentionOld.confidence())
                        .pattern(eventEventRelationMentionOld.pattern())
                        .model(eventEventRelationMentionOld.model())
                        .polarity(eventEventRelationMentionOld.polarity())
                        .triggerText(eventEventRelationMentionOld.triggerText());
                resolvedEERMs.add(newEventEventRelationMention.build());
            }
        }
        newDt.eventEventRelationMentions(EventEventRelationMentions.create(resolvedEERMs.build()));
        return newDt.build();
    }
}
