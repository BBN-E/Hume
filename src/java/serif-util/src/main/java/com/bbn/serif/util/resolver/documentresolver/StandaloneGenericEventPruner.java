package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.*;
import com.bbn.serif.util.resolver.Resolver;
import com.bbn.serif.util.resolver.sentenceresolver.SentenceResolver;
import com.google.common.collect.Sets;

import javax.print.Doc;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class StandaloneGenericEventPruner implements DocumentResolver, Resolver {

    static Set<String> genericTypes = Sets.newHashSet(
            "http://ontology.causeex.com/ontology/odps/Event#Event",
            "http://ontology.causeex.com/ontology/odps/ICM#Factor",
            "/wm/concept/causal_factor"
    );
    @Override
    public DocTheory resolve(DocTheory dt) {


        Set<EventMention> emInEERM = new HashSet<>();
        for(EventEventRelationMention eventEventRelationMention: dt.eventEventRelationMentions()){
            EventMention leftEM = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.leftEventMention()).eventMention();
            EventMention rightEM = ((EventEventRelationMention.EventMentionArgument) eventEventRelationMention.rightEventMention()).eventMention();
            emInEERM.add(leftEM);
            emInEERM.add(rightEM);
        }
        DocTheory.Builder newDt = dt.modifiedCopyBuilder();
        for(int sentid = 0;sentid < dt.numSentences();++sentid){
            SentenceTheory sentenceTheory = dt.sentenceTheory(sentid);
            EventMentions.Builder newEventMentions = new EventMentions.Builder();
            for (EventMention oldEventMention : sentenceTheory.eventMentions()) {

                boolean onlyHaveGenericTypes = true;
                for(EventMention.EventType eventType:oldEventMention.eventTypes()){
                    if(!genericTypes.contains(eventType.eventType().toString())){
                        onlyHaveGenericTypes = false;
                        break;
                    }
                }
                for(EventMention.EventType factorType:oldEventMention.factorTypes()){
                    if(!genericTypes.contains(factorType.eventType().toString())){
                        onlyHaveGenericTypes = false;
                        break;
                    }
                }

                if(emInEERM.contains(oldEventMention)){
                    newEventMentions.addEventMentions(oldEventMention);
                }
                else{
                    if(onlyHaveGenericTypes){
                        System.out.println("WARNING: StandaloneGenericEventPruner DROPPING "+sentenceTheory.tokenSequence().span(oldEventMention.semanticPhraseStart().get(),oldEventMention.semanticPhraseEnd().get()).tokenizedText().utf16CodeUnits());
                    }
                    else{
                        newEventMentions.addEventMentions(oldEventMention);
                    }
                }

            }
            newDt.replacePrimarySentenceTheory(sentenceTheory,sentenceTheory.modifiedCopyBuilder().eventMentions(newEventMentions.build()).build());
        }
        return newDt.build();
    }
}
