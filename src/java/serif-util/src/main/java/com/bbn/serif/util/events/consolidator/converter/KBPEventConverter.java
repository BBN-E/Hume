package com.bbn.serif.util.events.consolidator.converter;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.base.Optional;
import com.google.common.collect.Lists;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Created by bmin on 10/22/18.
 */
public class KBPEventConverter {
  // Event type and argument mapping rules are defined in:
  // /nfs/ld100/u10/bmin/repo_clean_for_exp/CauseEx/util/python/knowledge_base/config_files/config_ontology.json


  static Set<String> kbpTypes = new HashSet<String>();
  static Map<String, String> kbpType2ontologyType = new HashMap<String, String>();
  //static Multimap<String, String> kbpType2multipleOntologyTypes = HashMultimap.create();

  static Map<String, Map<String, Map<String, String>>> eventType2role2entityType2role =
      new HashMap<String, Map<String, Map<String, String>>>();

    /*
    static ImmutableMap<String, ImmutableMap<String, String>> eventType2entityType2role =
            ImmutableMap.of(
                    "Attacker", ImmutableMap.of(
                            "default", "has_active_actor",
                            "VEH", "has_instrument",
                            "WEA", "has_instrument",
                            "FAC", "involves_goods_or_property",
                            "LOC", "involves_goods_or_property"),
                    "Instrument", ImmutableMap.of(
                            "default", "has_instrument"),
                    "Place", ImmutableMap.of(
                            "default", "located_at")
            );
            */

  public static boolean isKBPEvent(EventMention eventMention) {
    if (kbpTypes.contains(eventMention.type().asString())) {
      return true;
    } else {
      return false;
    }
  }

  // +2
  public static List<EventMention> toNormalizedEventMention(EventMention eventMention,
      SentenceTheory sentenceTheory) {
    List<EventMention> eventMentions = new ArrayList<EventMention>();

    String eventType = eventMention.type().asString();
    List<String> eventTypeNews = new ArrayList<String>();
    //if(kbpType2multipleOntologyTypes.containsKey(eventType))
    //    eventTypeNews.addAll(kbpType2multipleOntologyTypes.get(eventType));
    //else if(kbpType2ontologyType.containsKey(eventType))
    //    eventTypeNews.add(kbpType2ontologyType.get(eventType));
    if (kbpType2ontologyType.containsKey(eventType)) {
      eventTypeNews.add(kbpType2ontologyType.get(eventType));
    }

    List<EventMention.Argument> eventArgs = new ArrayList<EventMention.Argument>();
    for (EventMention.Argument argument : eventMention.arguments()) {
      String argRole = argument.role().asString();
      Optional<String> argRoleNew = Optional.absent();
      if (argument instanceof EventMention.MentionArgument) {
        EventMention.MentionArgument mentionArgument = (EventMention.MentionArgument) argument;
        String entityType = mentionArgument.mention().entityType().name().asString();
        String entityTypeAndSubType =
            entityType + "." + mentionArgument.mention().entitySubtype().name().asString();

        if (eventType2role2entityType2role.containsKey(eventType)) {
          if (eventType2role2entityType2role.get(eventType).containsKey(argRole)) {
            Map<String, String> entityType2argRole =
                eventType2role2entityType2role.get(eventType).get(argRole);
            if (entityType2argRole.containsKey(entityType) || entityType2argRole
                .containsKey(entityTypeAndSubType)) {
              if (entityType2argRole.containsKey(entityType)) {
                argRoleNew = Optional.of(entityType2argRole.get(entityType));
              } else {
                argRoleNew = Optional.of(entityType2argRole.get(entityTypeAndSubType));
              }
            } else {
              argRoleNew = Optional.of(entityType2argRole.get("default"));
            }
          }
        } else { // if the event type is not found
          if (eventType2role2entityType2role.get("default").containsKey(argRole)) {
            Map<String, String> entityType2argRole =
                eventType2role2entityType2role.get("default").get(argRole);
            if (entityType2argRole.containsKey(entityType) || entityType2argRole
                .containsKey(entityTypeAndSubType)) {
              if (entityType2argRole.containsKey(entityType)) {
                argRoleNew = Optional.of(entityType2argRole.get(entityType));
              } else {
                argRoleNew = Optional.of(entityType2argRole.get(entityTypeAndSubType));
              }
            } else {
              argRoleNew = Optional.of(entityType2argRole.get("default"));
            }
          }
        }

        if (argRoleNew.isPresent()) {
          eventArgs.add(EventMention.MentionArgument.from(
              Symbol.from(argRoleNew.get()), mentionArgument.mention(),
              mentionArgument.score())); // is there any reason this was previously set to 0.7f?
        }
      }

    }

    //System.out.println("eventType=" + eventType + " eventTypeNew=" + eventTypeNew.or("NONE"));
    for (String eventTypeNew : eventTypeNews) {
      // make deep copy of event arguments
      List<EventMention.Argument> eventArgsNew = new ArrayList<EventMention.Argument>();
      for (EventMention.Argument eventArg : eventArgs) {
        eventArgsNew.add(eventArg.copyWithDifferentScore(new Float(EventConsolidator.KBP_EVENT_SCORE).floatValue())); // KBP scores could be negative, so we just set it to a fixed value
      }

      EventMention em = EventMention
          .builder(Symbol.from(eventTypeNew))
          .setAnchorNode(eventMention.anchorNode())
          .setAnchorPropFromNode(sentenceTheory)
          .setScore(EventConsolidator.KBP_EVENT_SCORE)  // KBP scores could be negative, so we just set it to a fixed value
          .setArguments(eventArgsNew)
          .setModel(Symbol.from("KBP"))
          .setEventTypes(Lists.newArrayList(EventMention.EventType.from(Symbol.from(eventTypeNew), EventConsolidator.KBP_EVENT_SCORE, Optional.absent(), Optional.absent())))  // KBP scores could be negative, so we just set it to a fixed value
          .build();

      eventMentions.add(em);
    }

    return eventMentions;
        /*
        if (eventMention.pattern().isPresent()) {
            EventMention em = EventMention
                    .builder(Symbol.from(eventTypeNew.get()))
                            .setAnchorNode(eventMention.anchorNode())
                            .setAnchorPropFromNode(sentenceTheory)
                            .setScore(eventMention.score())     // is there any reason why this was hard-coded to 0.17 previously?
                            .setPatternID(eventMention.pattern().get())
                            .setArguments(eventArgs)
                            .setModel(Symbol.from("KBP"))
                            .build();
            return em;
        } else {
            EventMention em = EventMention
                    .builder(Symbol.from(eventTypeNew.get()))
                            .setAnchorNode(eventMention.anchorNode())
                            .setAnchorPropFromNode(sentenceTheory)
                            .setScore(eventMention.score())     // is there any reason why this was hard-coded to 0.17 previously?
                            .setArguments(eventArgs)
                            .setModel(Symbol.from("KBP"))
                            .build();
            return em;
        }
        */
  }

  public static Map<String, JsonNode> readJsonNodeIntoMap(JsonNode jsonNode) {
    Map<String, JsonNode> map = new HashMap<String, JsonNode>();

    Iterator<Map.Entry<String, JsonNode>> nodes = jsonNode.fields();
    while (nodes.hasNext()) {
      Map.Entry<String, JsonNode> entry = (Map.Entry<String, JsonNode>) nodes.next();
      map.put(entry.getKey(), entry.getValue());
    }

    return map;
  }

  public static Map<String, String> toMap(Map<String, JsonNode> map) {
    Map<String, String> newMap = new HashMap<String, String>();
    for (String key : map.keySet()) {
      newMap.put(key, map.get(key).textValue());
    }
    return newMap;
  }

  // +2
  public static void loadKBPEventAndRoleMapping(String strFileKBPeventMapping,
      final OntologyHierarchy ontologyHierarchy) throws IOException {
    String content = new String(Files.readAllBytes(Paths.get(strFileKBPeventMapping)));

    ObjectMapper mapper = new ObjectMapper();
    JsonNode l1 = mapper.readTree(content);
    JsonNode l2 = l1.get("mappings");

    JsonNode eventTypeMapping = l2.get("event");
    Map<String, JsonNode> map = readJsonNodeIntoMap(eventTypeMapping);
    for (String key : map.keySet()) {
      kbpTypes.add(key);
      final String ontologyType = map.get(key).textValue();
      ontologyHierarchy.assertEventTypeIsInOntology(ontologyType,
          "KBPEventConverter.loadKBPEventAndRoleMapping"); // schema checking
      kbpType2ontologyType.put(key, ontologyType);
    }

    JsonNode eventRoleMapping = l2.get("event-role");
    JsonNode eventRoleMappingDefault = eventRoleMapping.get("default");
    map = readJsonNodeIntoMap(eventRoleMappingDefault);
    eventType2role2entityType2role.put("default", new HashMap<String, Map<String, String>>());
    for (String key : map.keySet()) {        // key here is a role e.g. Source, Target, Place, ...
      Map<String, JsonNode> submap = readJsonNodeIntoMap(map.get(key));
      eventType2role2entityType2role.get("default")
          .put(key, toMap(submap));  // e.g. default -> Source (role) -> VEH -> has_artifact
    }

    JsonNode eventRoleMappingByEventType = eventRoleMapping.get("byEventType");
    map = readJsonNodeIntoMap(eventRoleMappingByEventType);
    for (String eventType : map.keySet()) {
      Map<String, JsonNode> submap = readJsonNodeIntoMap(map.get(eventType));
      for (String role : submap.keySet()) {
        if (!eventType2role2entityType2role.containsKey(eventType)) {
          eventType2role2entityType2role
              .put(eventType, new HashMap<String, Map<String, String>>());
        }
        eventType2role2entityType2role.get(eventType)
            .put(role, toMap(readJsonNodeIntoMap(submap.get(role))));
      }
    }

    // schema checking
    for (final String eventType : eventType2role2entityType2role.keySet()) {
      for (final String kbpRole : eventType2role2entityType2role.get(eventType).keySet()) {
        for (final String entityType : eventType2role2entityType2role.get(eventType).get(kbpRole)
            .keySet()) {
          final String ontologyRole =
              eventType2role2entityType2role.get(eventType).get(kbpRole).get(entityType);
          ontologyHierarchy.assertEventRoleIsInOntology(ontologyRole,
              "KBPEventConverter.loadKBPEventAndRoleMapping");
        }
      }
    }
  }
}
