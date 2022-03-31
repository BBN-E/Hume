package com.bbn.serif.util.resolver.documentresolver;

import com.bbn.serif.theories.*;
import com.bbn.serif.util.resolver.Resolver;
import com.google.common.collect.Sets;

import java.util.*;

public class SimpleEntityCreator implements DocumentResolver, Resolver {
    @Override
    public DocTheory resolve(DocTheory docTheory) {
        Set<Mention> touchedMentions = new HashSet<>();
        for(SentenceTheory sentenceTheory:docTheory.nonEmptySentenceTheories()){
            touchedMentions.addAll(sentenceTheory.mentions().asList());
        }
        Set<Mention> entityCoveredMentions = new HashSet<>();
        for(Entity entity:docTheory.entities()){
            for(Mention mention:entity.mentionSet()){
                entityCoveredMentions.add(mention);
            }
        }
        Set<Mention> unCoveredMentions = Sets.difference(touchedMentions,entityCoveredMentions);
        if(unCoveredMentions.size()>0){
            List<Entity> entities = new ArrayList<>(docTheory.entities().asList());
            for(Mention mention : unCoveredMentions){
                Entity.Builder entity = new Entity.Builder();
                entity.addMentionSet(mention);
                Map<Mention, MentionConfidence> mentionConf = new HashMap<>();
                mentionConf.put(mention,MentionConfidence.DEFAULT);
                entity.confidences(mentionConf);
                entity.generic(true);
                entity.type(mention.entityType());
                entity.subtype(mention.entitySubtype());
                entities.add(entity.build());
            }
            return docTheory.modifiedCopyBuilder().entities(Entities.create(entities,"0.8")).build();
        }
        else{
            return docTheory;
        }
    }
}
