package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.*;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;

import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.util.events.consolidator.converter.AccentKbpEventConverter;
import com.bbn.serif.util.resolver.Resolver;
import org.json.simple.parser.ParseException;

import java.io.File;
import java.io.IOException;
import java.util.*;

import com.google.common.collect.HashMultimap;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.Multimap;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Lists;
import com.bbn.bue.common.symbols.Symbol;


public final class EventEventRelationReAttachResolver implements DocumentResolver, Resolver {

    public EventEventRelationReAttachResolver() {
    }


    // TODO: this will get the first event mention with an anchor match; needs to choose EM smarter.
    public Optional<EventMention> getBestEventMention(Set<EventMention> eventMentions,
                                                      Multimap<SynNode, EventMention> anchor2eventMentions) {
        for(EventMention eventMention: eventMentions){
            if (eventMention.anchorNode() != null) {
                SynNode synNode = eventMention.anchorNode();

                for (EventMention eventMentionNew : anchor2eventMentions.get(synNode)) {
                    return Optional.of(eventMentionNew);
                }
                for (EventMention eventMentionNew : anchor2eventMentions.get(synNode.head())) {
                    return Optional.of(eventMentionNew);
                }
            }
            for (EventMention.Anchor anchor : eventMention.anchors()) {
                SynNode synNode = anchor.anchorNode();
                for (EventMention eventMentionNew : anchor2eventMentions.get(synNode)) {
                    return Optional.of(eventMentionNew);
                }
                for (EventMention eventMentionNew : anchor2eventMentions.get(synNode.head())) {
                    return Optional.of(eventMentionNew);
                }
            }
        }
        return Optional.absent();
    }

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



    public Optional<EventEventRelationMention> reAttachEventMentionArgs(EventEventRelationMention eventEventRelationMention,
                                                                        Multimap<SynNode, EventMention> anchor2eventMentions) {
        Set<EventMention> leftEventMentionsOld = new HashSet<>();
        Set<EventMention> rightEventMentionsOld = new HashSet<>();
        if(eventEventRelationMention.leftEventMention() instanceof EventEventRelationMention.ICEWSEventMentionArgument){
            ICEWSEventMention leftIcewsEventMention = ((EventEventRelationMention.ICEWSEventMentionArgument) eventEventRelationMention.leftEventMention()).icewsEventMention();
            Set<EventMention> possibleNewEventMentions = AccentKbpEventConverter.icewsEventMentionEventMentionMap.getOrDefault(leftIcewsEventMention,new HashSet<>());
            leftEventMentionsOld.addAll(possibleNewEventMentions);
        }
        else if(eventEventRelationMention.leftEventMention() instanceof EventEventRelationMention.EventMentionArgument){
            leftEventMentionsOld.add(((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.leftEventMention()).eventMention());
        }
        if(eventEventRelationMention.rightEventMention() instanceof EventEventRelationMention.ICEWSEventMentionArgument){
            ICEWSEventMention rightIcewsEventMention = ((EventEventRelationMention.ICEWSEventMentionArgument) eventEventRelationMention.rightEventMention()).icewsEventMention();
            Set<EventMention> possibleNewEventMentions = AccentKbpEventConverter.icewsEventMentionEventMentionMap.getOrDefault(rightIcewsEventMention,new HashSet<>());
            rightEventMentionsOld.addAll(possibleNewEventMentions);
        }
        else if(eventEventRelationMention.rightEventMention() instanceof EventEventRelationMention.EventMentionArgument){
            rightEventMentionsOld.add(((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.rightEventMention()).eventMention());
        }


        Optional<EventMention> leftEventMentionNew = getBestEventMention(leftEventMentionsOld, anchor2eventMentions);
        Optional<EventMention> rightEventMentionNew = getBestEventMention(rightEventMentionsOld, anchor2eventMentions);

        if (leftEventMentionNew.isPresent() && rightEventMentionNew.isPresent()) {
            if(leftEventMentionNew.get() != rightEventMentionNew.get()){
                EventEventRelationMention eerm = new EventEventRelationMention.Builder()
                        .relationType(eventEventRelationMention.relationType())
                        .leftEventMention(makeArgument(leftEventMentionNew.get(), "arg1"))
                        .rightEventMention(makeArgument(rightEventMentionNew.get(), "arg2"))
                        .confidence(eventEventRelationMention.confidence())
                        .pattern(eventEventRelationMention.pattern())
                        .model(eventEventRelationMention.model())
                        .polarity(eventEventRelationMention.polarity())
                        .triggerText(eventEventRelationMention.triggerText())
                        .build();
                return Optional.of(eerm);
            }
        }
//        if (!leftEventMentionNew.isPresent()) {
//            System.out.println("Missing Left");
//            System.out.println(leftEventMentionOld.span().tokenizedText().utf16CodeUnits());
//            System.out.println(leftEventMentionOld.type().asString());
//        }
//        if (!rightEventMentionNew.isPresent()) {
//            System.out.println("Missing Right");
//            System.out.println(rightEventMentionOld.span().tokenizedText().utf16CodeUnits());
//            System.out.println(rightEventMentionOld.type().asString());
//        }
        return Optional.absent();
    }

    public Multimap<SynNode, EventMention> buildSynNode2EventMentionCache(final DocTheory docTheory) {
        Multimap<SynNode, EventMention> anchor2eventMentions = HashMultimap.create();
        for (int i = 0; i < docTheory.numSentences(); ++i) {
            final SentenceTheory sentenceTheory = docTheory.sentenceTheory(i);
            for (final EventMention em : sentenceTheory.eventMentions()) {
                if (em.anchorNode() != null) {
                    anchor2eventMentions.put(em.anchorNode(), em);
                    if(em.anchorNode().head() != em.anchorNode()){
                        anchor2eventMentions.put(em.anchorNode().head(),em);
                    }
                }
                for (EventMention.Anchor anchor : em.anchors()) {
                    anchor2eventMentions.put(anchor.anchorNode(), em);
                    if(anchor.anchorNode().head() != anchor.anchorNode()){
                      anchor2eventMentions.put(anchor.anchorNode().head(),em);
                    }
                }
            }
        }

        return anchor2eventMentions;
    }

    public static class EERMIdentifierKey{
        EventMention left;
        EventMention right;
        Symbol relationType;
        public EERMIdentifierKey(EventEventRelationMention eventEventRelationMention){
            this.left = ((EventEventRelationMention.EventMentionArgument)eventEventRelationMention.leftEventMention()).eventMention();
            this.right = ((EventEventRelationMention.EventMentionArgument)eventEventRelationMention.rightEventMention()).eventMention();
            this.relationType = eventEventRelationMention.relationType();
        }

        @Override
        public int hashCode(){
            int prime = 31;
            int ret = left.hashCode();
            ret = ret * prime + right.hashCode();
            ret = ret * prime + relationType.hashCode();
            return ret;
        }

        @Override
        public boolean equals(Object o){
            if(!(o instanceof EERMIdentifierKey)){
                return false;
            }
            EERMIdentifierKey that = (EERMIdentifierKey)o;
            return this.left.equals(that.left) && this.right.equals(that.right) && this.relationType.equals(that.relationType);
        }

    }

    public List<EventEventRelationMention> deDuplicateEERM(Collection<EventEventRelationMention> eventEventRelationMentions){
        Map<EERMIdentifierKey,List<EventEventRelationMention>> keyToEERM = new HashMap<>();
        for(EventEventRelationMention eventEventRelationMention : eventEventRelationMentions){
            EERMIdentifierKey eermIdentifierKey = new EERMIdentifierKey(eventEventRelationMention);
            List<EventEventRelationMention> buf = keyToEERM.getOrDefault(eermIdentifierKey,new ArrayList<>());
            buf.add(eventEventRelationMention);
            keyToEERM.put(eermIdentifierKey,buf);
        }
        List<EventEventRelationMention> ret = new ArrayList<>();
        for(EERMIdentifierKey key: keyToEERM.keySet()){
            List<EventEventRelationMention> buf = keyToEERM.get(key);
            Collections.sort(buf, new Comparator<EventEventRelationMention>() {
                @Override
                public int compare(EventEventRelationMention o1, EventEventRelationMention o2) {
                    double leftConfidence = o1.confidence().or(0.0);
                    double rightConfidence = o2.confidence().or(0.0);
                    return (int)((rightConfidence-leftConfidence)*1000);
                }
            });
            ret.add(buf.get(0));
        }
        return ret;
    }

    public String getAnchorAndTypes(EventEventRelationMention.Argument argument, DocTheory docTheory) {
        if(argument instanceof EventEventRelationMention.ICEWSEventMentionArgument){
            System.err.println("Invalid EER argument: ICEWSEventMentionArgument. Exit");
            System.exit(-1);
        }
        else if(argument instanceof EventEventRelationMention.EventMentionArgument) {
            EventMention eventMention = ((EventEventRelationMention.EventMentionArgument) argument).eventMention();
            StringBuilder stringBuilder = new StringBuilder();
            stringBuilder.append(eventMention.type().toString() + "|");
            for(EventMention.EventType eventType : eventMention.eventTypes())
                stringBuilder.append(eventType.eventType().toString() + "|");
            for(EventMention.EventType eventType : eventMention.factorTypes())
                stringBuilder.append(eventType.eventType().toString() + "|");
            stringBuilder.append(":");
            stringBuilder.append(eventMention.anchorNode().tokenSpan().tokenizedText(docTheory).utf16CodeUnits() + "|");
            for(EventMention.Anchor anchor : eventMention.anchors()) {
                stringBuilder.append(anchor.anchorNode().tokenSpan().tokenizedText(docTheory).utf16CodeUnits() + "|");
            }
            return stringBuilder.toString();
        }

        return "";
    }

    public String getStringForEventEventRelation(EventEventRelationMention eventEventRelationMention, DocTheory docTheory) {
        if(eventEventRelationMention.leftEventMention() instanceof EventEventRelationMention.ICEWSEventMentionArgument ||
                eventEventRelationMention.leftEventMention() instanceof EventEventRelationMention.ICEWSEventMentionArgument){
            System.err.println("Invalid EER argument: ICEWSEventMentionArgument. Exit");
            System.exit(-1);
        }

        EventMention leftEM = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.leftEventMention()).eventMention();
        EventMention rightEM = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.rightEventMention()).eventMention();

        if(leftEM.sentenceTheory(docTheory).sentenceNumber()!=rightEM.sentenceTheory(docTheory).sentenceNumber()) {
            System.err.println("Invalid EER argument pairs: not in the same sentence. Exit");
            System.exit(-1);
        }

        String sentenceText = leftEM.sentenceTheory(docTheory).tokenSpan().tokenizedText(docTheory).utf16CodeUnits();

        String leftArg = getAnchorAndTypes(eventEventRelationMention.leftEventMention(), docTheory);
        String rightArg = getAnchorAndTypes(eventEventRelationMention.rightEventMention(), docTheory);

        return sentenceText + "\n" + eventEventRelationMention.relationType().toString() + "\n" + leftArg + "\n" + rightArg;
    }

    public final DocTheory resolve(final DocTheory docTheory) {

        final DocTheory.Builder newDT = docTheory.modifiedCopyBuilder();

        Multimap<SynNode, EventMention> anchor2eventMentions = buildSynNode2EventMentionCache(docTheory);

        List<EventEventRelationMention> duplicatedEERMs = new ArrayList<>();
        for (EventEventRelationMention eventEventRelationMentionOld : docTheory.eventEventRelationMentions()) {
            /*
            System.out.println("===== EER old");
            String eerStringOld = getStringForEventEventRelation(eventEventRelationMentionOld, docTheory);
            System.out.println(eerStringOld);
            */

            Optional<EventEventRelationMention> eventEventRelationMentionNew = reAttachEventMentionArgs(eventEventRelationMentionOld, anchor2eventMentions);
            if (eventEventRelationMentionNew.isPresent()) {
                duplicatedEERMs.add(eventEventRelationMentionNew.get());
//                System.err.println("Scored!");

                /*
                System.out.println("===== EER new");
                String eerStringNew = getStringForEventEventRelation(eventEventRelationMentionNew.get(), docTheory);
                System.out.println(eerStringNew);
                */
            } else {
                System.out.println("WARNING: DROPPING EventEventRelationMention MIS");
//                System.exit(-1);
            }
        }

        /*
        for (EventEventRelationMention eventEventRelationMention : duplicatedEERMs) {
            System.out.println("===== EER old");
            String eerString = getStringForEventEventRelation(eventEventRelationMention, docTheory);
            System.out.println(eerString);
        }
        */
        List<EventEventRelationMention> deDuplicatedEERMS = deDuplicateEERM(duplicatedEERMs);
        for(int i = 0;i < (duplicatedEERMs.size()-deDuplicatedEERMS.size());++i){
            System.out.println("WARNING: DROPPING EventEventRelationMention DUP");
        }
        /*
        for (EventEventRelationMention eventEventRelationMention : deDuplicatedEERMS) {
            System.out.println("===== EER new");
            String eerString = getStringForEventEventRelation(eventEventRelationMention, docTheory);
            System.out.println(eerString);
        }
        */

        ImmutableList.Builder<EventEventRelationMention> eerms = ImmutableList.builder();
        for(EventEventRelationMention eerm : deDuplicatedEERMS){
            eerms.add(eerm);
        }
        newDT.eventEventRelationMentions(EventEventRelationMentions.create(eerms.build()));
        return newDT.build();
    }

}
