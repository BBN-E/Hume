package com.bbn.serif.util.resolver.eventmentionresolver;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.Pair;
import com.bbn.serif.util.resolver.Resolver;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.FileReader;
import java.io.IOException;
import java.util.*;

public class FlipOppositeCFToPositiveResolver implements Resolver, EventMentionResolver {

    final Map<String,String> oldTypeToNewType;

    public FlipOppositeCFToPositiveResolver(String jsonFile) throws IOException, ParseException {
        JSONParser parser = new JSONParser();
        Object obj = parser.parse(new FileReader(jsonFile));
        oldTypeToNewType = new HashMap<>();
        JSONObject jsonObject = (JSONObject) obj;
        for (Object eventObject : jsonObject.keySet()) {
            String oldEventType = (String)eventObject;
            String newEventType = (String)(jsonObject.get(eventObject));
            oldTypeToNewType.put(oldEventType,newEventType);
        }
    }
    @Override
    public Optional<EventMention> resolve(EventMention em) {
        List<EventMention.EventType> newCFTypes = new ArrayList<>();
        Map<String,EventMention.EventType> existingTypeToEventTypeObj = new HashMap<>();
        for(EventMention.EventType existingCFType:em.factorTypes()){
            existingTypeToEventTypeObj.put(existingCFType.eventType().asString(),existingCFType);
        }
        for(EventMention.EventType existingCFType:em.factorTypes()){
            if(!this.oldTypeToNewType.containsKey(existingCFType.eventType().asString())){
                newCFTypes.add(existingCFType);
            }
            else{
                if(!existingTypeToEventTypeObj.containsKey(this.oldTypeToNewType.get(existingCFType.eventType().asString()))){
                    EventMention.EventType.Builder newCFType = existingCFType.modifiedCopyBuilder();
                    newCFType.setType(Symbol.from(this.oldTypeToNewType.get(existingCFType.eventType().asString())));
                    if(existingCFType.getMagnitude().isPresent()){
                        newCFType.setMagnitude(com.google.common.base.Optional.of(0.0-existingCFType.getMagnitude().get()));
                    }
                    newCFTypes.add(newCFType.build());
                    existingTypeToEventTypeObj.put(this.oldTypeToNewType.get(existingCFType.eventType().asString()),newCFType.build());
                }
                else{
                    System.out.println("[WARNING] conflicted CF types detected for event. Will only keep existing CF type.");
                }
            }
        }
        EventMention.Builder newEm = em.modifiedCopyBuilder();
        newEm.setFactorTypes(newCFTypes);
        return Optional.of(newEm.build());
    }
}
