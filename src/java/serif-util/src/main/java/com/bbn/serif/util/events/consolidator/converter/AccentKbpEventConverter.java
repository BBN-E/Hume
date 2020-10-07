package com.bbn.serif.util.events.consolidator.converter;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.ValueMention;
import com.bbn.serif.theories.icewseventmentions.ICEWSEventMention;
import com.bbn.serif.util.events.consolidator.common.EventRoleConstants;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.Lists;

import org.apache.commons.lang3.tuple.Pair;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;


public class AccentKbpEventConverter {

  static Map<String, Map<String, Map<String, Map<String, String>>>>
      schema2eventType2eventId2key2value
      = new HashMap<String, Map<String, Map<String, Map<String, String>>>>();

  static Map<String, String> cameoCodeToEventType = new HashMap<String, String>();


  // Maintain a global mapping table So we can see the conversion process.
  public static Map<ICEWSEventMention, Set<EventMention>> icewsEventMentionEventMentionMap = new HashMap<>();

  public static void LoadCameoCodeToEventType(String strFileMapping) {
    List<String> lines = readLinesIntoList(strFileMapping);
    for (String line : lines) {
      line = line.trim();
      if (!line.isEmpty()) {
        String[] items = line.split("\t");
        String cameoCode = items[0].trim();
        String eventType = items[1].trim();
        System.out.println("cameo:\t" + cameoCode + "\ttype:\t" + eventType);
        cameoCodeToEventType.put(cameoCode, eventType);
      }
    }
  }

  public static String toString(ICEWSEventMention icewsEventMention, DocTheory docTheory) {
    StringBuilder stringBuilder = new StringBuilder();
    stringBuilder.append("ICEWS\t" + "\t" + icewsEventMention.code().asString() + "\t" +
        cameoCodeToEventType.get(icewsEventMention.code().asString()) + "\n");
    for (ICEWSEventMention.ICEWSEventParticipant icewsEventParticipant : icewsEventMention
        .eventParticipants()) {
      String role = icewsEventParticipant.role().asUnicodeFriendlyString().utf16CodeUnits();
      Mention mention = icewsEventParticipant.actorMention().mention();
      if (role.equalsIgnoreCase("source")) {
        stringBuilder.append(
            "ICEWS\t" + "source:\t" + mention.tokenSpan().tokenizedText(docTheory)
                .utf16CodeUnits()
                + "\n");
      } else if (role.equalsIgnoreCase("target")) {
        stringBuilder.append(
            "ICEWS\t" + "target:\t" + mention.tokenSpan().tokenizedText(docTheory)
                .utf16CodeUnits()
                + "\n");
      } else {
        stringBuilder.append(
            "ICEWS\t" + role + ":\t" + mention.tokenSpan().tokenizedText(docTheory)
                .utf16CodeUnits()
                + "\n");
      }
    }

    return stringBuilder.toString();
  }

  public static String toString(EventMention eventMention, DocTheory docTheory) {
    StringBuilder stringBuilder = new StringBuilder();
    stringBuilder
        .append("type:\t" + eventMention.type().asUnicodeFriendlyString().utf16CodeUnits() + "\n");

    stringBuilder.append(
        "\t" + "trigger:\t" + eventMention.anchorNode().tokenSpan().tokenizedText(docTheory)
            .utf16CodeUnits() + "\n");

    for (EventMention.Argument argument : eventMention.arguments()) {
      String role = argument.role().asString();
      if (argument instanceof EventMention.MentionArgument) {
        argument = (EventMention.MentionArgument) argument;
        stringBuilder.append(
            "\t" + role + ":\t" + argument.tokenSpan().tokenizedText(docTheory).utf16CodeUnits()
                + "\n");
      } else if (argument instanceof EventMention.ValueMentionArgument) {
        argument = (EventMention.ValueMentionArgument) argument;
        stringBuilder.append(
            "\t" + role + ":\t" + argument.tokenSpan().tokenizedText(docTheory).utf16CodeUnits()
                + "\n");
      } else if (argument instanceof EventMention.EventMentionArgument) {
        argument = (EventMention.EventMentionArgument) argument;
        stringBuilder.append(
            "\t" + role + ":\t" + argument.tokenSpan().tokenizedText(docTheory).utf16CodeUnits()
                + "\n");
      } else if (argument instanceof EventMention.SpanArgument) {
        argument = (EventMention.SpanArgument) argument;
        stringBuilder.append(
            "\t" + role + ":\t" + argument.tokenSpan().tokenizedText(docTheory).utf16CodeUnits()
                + "\n");
      } else {
        System.out.println("Error in event arguments");
      }
    }

    return stringBuilder.toString();
  }

  // +2
  public static List<Pair<SentenceTheory, EventMention>> toEventMentions(
      ICEWSEventMention icewsEventMention, DocTheory docTheory) {
    List<Pair<SentenceTheory, EventMention>> eventMentions =
        new ArrayList<Pair<SentenceTheory, EventMention>>();

    if (!icewsEventMention.propositions().isEmpty()) {

      // find sentence
      SentenceTheory sentenceTheory = null;
      for (int sid = 0; sid < docTheory.numSentences(); sid++) {
        SentenceTheory sentenceTheoryCurrent = docTheory.sentenceTheory(sid);

        if (!sentenceTheoryCurrent.isEmpty() && icewsEventMention.propositions().get(0).predHead()
            .isPresent()) {
          if (sentenceTheoryCurrent.span().charOffsetRange().overlaps(
              icewsEventMention.propositions().get(0).predHead().get().span()
                  .charOffsetRange())) {
            sentenceTheory = sentenceTheoryCurrent;
          }
        }
      }

      // if this ACCENT event is not in any sentence theory
      if (sentenceTheory == null) {
        return eventMentions;
      }

      if (icewsEventMention.propositions().get(0).predHead().isPresent()) {
        // SynNode anchorNode = icewsEventMention.propositions().get(0).predHead().get();

        SynNode anchorNode1 = null;
        SynNode anchorNode2 = null;
        SynNode anchorNode3 = null;
        if (icewsEventMention.propositions().size() >= 3) {
          if (icewsEventMention.propositions().get(2).predHead().isPresent()) {
            anchorNode3 = icewsEventMention.propositions().get(2).predHead().get();
          }
        }
        if (icewsEventMention.propositions().size() >= 2) {
          if (icewsEventMention.propositions().get(1).predHead().isPresent()) {
            anchorNode2 = icewsEventMention.propositions().get(1).predHead().get();
          }
        }
        if (icewsEventMention.propositions().size() >= 1) {
          if (icewsEventMention.propositions().get(0).predHead().isPresent()) {
            anchorNode1 = icewsEventMention.propositions().get(0).predHead().get();
          }
        }

        EventMention newEventMention1 = null;
        EventMention newEventMention2 = null;
        EventMention newEventMention3 = null;

        Mention actor1 = null;
        Mention actor2 = null;
        Mention loc = null;
        ValueMention time = null;

        for (ICEWSEventMention.ICEWSEventParticipant icewsEventParticipant : icewsEventMention
            .eventParticipants()) {
          String role = icewsEventParticipant.role().asUnicodeFriendlyString().utf16CodeUnits();
          Mention mention = icewsEventParticipant.actorMention().mention();
          if (role.equalsIgnoreCase("source")) {
            actor1 = mention;
          } else if (role.equalsIgnoreCase("target")) {
            actor2 = mention;
          } else if (role.equalsIgnoreCase("location")) {
            loc = mention;
          }
        }

        if (icewsEventMention.timeValueMention().isPresent()) {
          time = icewsEventMention.timeValueMention().get();
        }

        if (cameoCodeToEventType.containsKey(icewsEventMention.code().asString())) {
          String cameoEventType = cameoCodeToEventType.get(icewsEventMention.code().asString());

          if (schema2eventType2eventId2key2value.get("CAMEO").containsKey(cameoEventType)) {
            Map<String, Map<String, String>> eventId2key2value
                = schema2eventType2eventId2key2value.get("CAMEO").get(cameoEventType);
            if (eventId2key2value.containsKey("event3")) {
              String newEventType = eventId2key2value.get("event3").get("type");
              List<EventMention.Argument> eventArgs =
                  toEventArgList("event3", eventId2key2value, actor1, actor2, loc, time);

              SynNode anchorNode = anchorNode1;
              if (anchorNode3 != null) {
                anchorNode = anchorNode3;
              } else if (anchorNode2 != null) {
                anchorNode = anchorNode2;
              }

              newEventMention3 = toEventMention(newEventType, anchorNode, sentenceTheory,
                  icewsEventMention.patternId(), eventArgs);
            }
            if (eventId2key2value.containsKey("event2")) {
              String newEventType = eventId2key2value.get("event2").get("type");
              List<EventMention.Argument> eventArgs =
                  toEventArgList("event2", eventId2key2value, actor1, actor2, loc, time);

              SynNode anchorNode = anchorNode1;
              if (anchorNode2 != null) {
                anchorNode = anchorNode2;
              }

              newEventMention2 = toEventMention(newEventType, anchorNode, sentenceTheory,
                  icewsEventMention.patternId(), eventArgs);
            }
            if (eventId2key2value.containsKey("event1")) {
              String newEventType = eventId2key2value.get("event1").get("type");
              List<EventMention.Argument> eventArgs =
                  toEventArgList("event1", eventId2key2value, actor1, actor2, loc, time);

              SynNode anchorNode = anchorNode1;

              newEventMention1 = toEventMention(newEventType, anchorNode, sentenceTheory,
                  icewsEventMention.patternId(), eventArgs);
            }

            // add has_topic
            if (eventId2key2value.containsKey("event1")) {
              if (eventId2key2value.get("event1").containsKey("topic")) {
                List<EventMention.Argument> args =
                    new ArrayList<EventMention.Argument>(newEventMention1.arguments());
                if (eventId2key2value.get("event1").get("topic").equals("event2")
                    && newEventMention1 != null && newEventMention2 != null) {
                  EventMention.EventMentionArgument arg
                      = EventMention.EventMentionArgument
                      .from(Symbol.from("has_topic"), newEventMention2, 0.7f);
                  args.add(arg);
                }
                if (eventId2key2value.get("event1").get("topic").equals("event3")
                    && newEventMention1 != null && newEventMention3 != null) {
                  EventMention.EventMentionArgument arg
                      = EventMention.EventMentionArgument
                      .from(Symbol.from("has_topic"), newEventMention3, 0.7f);
                  args.add(arg);
                }
                newEventMention1 =
                    newEventMention1
                        .modifiedCopyBuilder()
                        .setArguments(args).setModel(Symbol.from("ACCENT")).build();
              }
            }
            if (eventId2key2value.containsKey("event2")) {
              if (eventId2key2value.get("event2").containsKey("topic")) {
                List<EventMention.Argument> args =
                    new ArrayList<EventMention.Argument>(newEventMention2.arguments());
                if (eventId2key2value.get("event2").get("topic").equals("event1")
                    && newEventMention1 != null && newEventMention2 != null) {
                  EventMention.EventMentionArgument arg
                      = EventMention.EventMentionArgument
                      .from(Symbol.from("has_topic"), newEventMention1, 0.7f);
                  args.add(arg);
                }
                if (eventId2key2value.get("event2").get("topic").equals("event3")
                    && newEventMention2 != null && newEventMention3 != null) {
                  EventMention.EventMentionArgument arg
                      = EventMention.EventMentionArgument
                      .from(Symbol.from("has_topic"), newEventMention3, 0.7f);
                  args.add(arg);
                }
                newEventMention2 =
                    newEventMention2
                        .modifiedCopyBuilder()
                        .setArguments(args).setModel(Symbol.from("ACCENT")).build();
              }
            }
            if (eventId2key2value.containsKey("event3")) {
              if (eventId2key2value.get("event3").containsKey("topic")) {
                List<EventMention.Argument> args =
                    new ArrayList<EventMention.Argument>(newEventMention3.arguments());
                if (eventId2key2value.get("event3").get("topic").equals("event1")
                    && newEventMention3 != null && newEventMention1 != null) {
                  EventMention.EventMentionArgument arg
                      = EventMention.EventMentionArgument
                      .from(Symbol.from("has_topic"), newEventMention1, 0.7f);
                  args.add(arg);
                }
                if (eventId2key2value.get("event3").get("topic").equals("event2")
                    && newEventMention3 != null && newEventMention2 != null) {
                  EventMention.EventMentionArgument arg
                      = EventMention.EventMentionArgument
                      .from(Symbol.from("has_topic"), newEventMention2, 0.7f);
                  args.add(arg);
                }
                newEventMention3 =
                    newEventMention3
                        .modifiedCopyBuilder()
                        .setArguments(args).setModel(Symbol.from("ACCENT")).build();
              }
            }

            if (newEventMention1 != null) {
              eventMentions.add(Pair.of(sentenceTheory, newEventMention1));
            }
            if (newEventMention2 != null) {
              eventMentions.add(Pair.of(sentenceTheory, newEventMention2));
            }
            if (newEventMention3 != null) {
              eventMentions.add(Pair.of(sentenceTheory, newEventMention3));
            }
          }
        }
      }
    }

    return eventMentions;
  }

  public static List<Pair<SentenceTheory, EventMention>> toEventMentions(EventMention eventMention,
      SentenceTheory sentenceTheory) {
    List<Pair<SentenceTheory, EventMention>> eventMentions =
        new ArrayList<Pair<SentenceTheory, EventMention>>();

    SynNode anchorNode = eventMention.anchorNode();

    EventMention newEventMention1 = null;
    EventMention newEventMention2 = null;

    String eventType = eventMention.type().asString();

    if (schema2eventType2eventId2key2value.get("KBP").containsKey(eventType)) {
      Map<String, Map<String, String>> eventId2key2value
          = schema2eventType2eventId2key2value.get("KBP").get(eventType);

      if (eventId2key2value.containsKey("event2")) {
        String newEventType = eventId2key2value.get("event2").get("type");
        List<EventMention.Argument> eventArgs = new ArrayList<>(eventMention.arguments());

        newEventMention2 = toEventMention(newEventType, anchorNode, sentenceTheory,
            Symbol.from("NA"), eventArgs);
      }
      if (eventId2key2value.containsKey("event1")) {
        String newEventType = eventId2key2value.get("event1").get("type");
        List<EventMention.Argument> eventArgs = new ArrayList<>(eventMention.arguments());

        newEventMention1 = toEventMention(newEventType, anchorNode, sentenceTheory,
            Symbol.from("NA"), eventArgs);
      }

      if (newEventMention1 != null) {
        eventMentions.add(Pair.of(sentenceTheory, newEventMention1));
      }
      if (newEventMention2 != null) {
        eventMentions.add(Pair.of(sentenceTheory, newEventMention2));
      }
    }

    return eventMentions;
  }

  // +1
  static List<EventMention.Argument> toEventArgList(String eventId,
      Map<String, Map<String, String>> eventId2key2value,
      Mention actor1, Mention actor2, Mention loc, ValueMention time) {
    List<EventMention.Argument> eventArgs = new ArrayList<EventMention.Argument>();
    if (eventId2key2value.get(eventId).containsKey("actor1") && actor1 != null) {
      String newRole = eventId2key2value.get(eventId).get("actor1");
      EventMention.Argument arg =
          EventMention.MentionArgument.from(Symbol.from(newRole), actor1, 0.7f);
      eventArgs.add(arg);
    }
    if (eventId2key2value.get(eventId).containsKey("actor2") && actor2 != null) {
      String newRole = eventId2key2value.get(eventId).get("actor2");
      EventMention.Argument arg =
          EventMention.MentionArgument.from(Symbol.from(newRole), actor2, 0.7f);
      eventArgs.add(arg);
    }
    if (eventId2key2value.get(eventId).containsKey("loc1") && loc != null) {
      String newRole = eventId2key2value.get(eventId).get("loc1");
      EventMention.Argument arg =
          EventMention.MentionArgument.from(Symbol.from(newRole), loc, 0.7f);
      eventArgs.add(arg);
    }

    // add time
    if (time != null) {
      EventMention.Argument arg = EventMention.ValueMentionArgument
          .from(Symbol.from(EventRoleConstants.HAS_TIME), time, 0.7f);
      eventArgs.add(arg);
    }

    return eventArgs;
  }

  // +2
  static EventMention toEventMention(String type,
      SynNode anchorNode,
      SentenceTheory sentenceTheory,
      Symbol patternId,
      List<EventMention.Argument> eventArgs) {
    EventMention em = EventMention
        .builder(Symbol.from(type))
        .setAnchorNode(anchorNode)
        .setAnchorPropFromNode(sentenceTheory)
        .setScore(AccentKbpEventConverter.ACCENT_EVENT_SCORE)
        .setPatternID(patternId)
        .setArguments(eventArgs)
        .setModel(Symbol.from("ACCENT"))
        .setEventTypes(Lists.newArrayList(EventMention.EventType.from(Symbol.from(type), AccentKbpEventConverter.ACCENT_EVENT_SCORE, Optional.absent(), Optional.absent())))
        .build();

    return em;
  }

  // +1
  public static void readEventMappingJson(String jsonFile,
      final OntologyHierarchy ontologyHierarchy) {
    JSONParser parser = new JSONParser();

    try {
      Object obj = parser.parse(new FileReader(jsonFile));

      JSONObject jsonObject = (JSONObject) obj;

      for (Object schemaObj : jsonObject.keySet()) {
        String schema = (String) schemaObj; // CAMEO or KBP

        if (!schema2eventType2eventId2key2value.containsKey(schema)) {
          schema2eventType2eventId2key2value
              .put(schema, new HashMap<String, Map<String, Map<String, String>>>());
        }

        JSONObject schemaObjs = (JSONObject) jsonObject.get(schema);

        for (Object eventTypeObject : schemaObjs.keySet()) {
          String eventType = (String) eventTypeObject;

          if (!schema2eventType2eventId2key2value.get(schema).containsKey(eventType)) {
            schema2eventType2eventId2key2value.get(schema)
                .put(eventType, new HashMap<String, Map<String, String>>());
          }

          JSONObject eventMap = (JSONObject) schemaObjs.get(eventType);

          for (Object eventIdObj : eventMap.keySet()) {
            String eventId = (String) eventIdObj; // event1-3

            if (!schema2eventType2eventId2key2value.get(schema).get(eventType)
                .containsKey(eventId)) {
              schema2eventType2eventId2key2value.get(schema).get(eventType)
                  .put(eventId, new HashMap<String, String>());
            }

            Map<String, String> key2value =
                schema2eventType2eventId2key2value.get(schema).get(eventType).get(eventId);

            JSONObject eventObj = (JSONObject) eventMap.get(eventId);
            String type = (String) eventObj.get("type");
            ontologyHierarchy.assertEventTypeIsInOntology(type,
                "AccentKbpEventConverter.readEventMappingJson");            // schema check

            key2value.put("type", type);

            if (eventObj.containsKey("topic")) {
              if (eventObj.get("topic") != null) {
                String eventTopic = (String) eventObj.get("topic");
                key2value.put("topic", eventTopic);
              }
            }
            if (eventObj.containsKey("args")) {
              JSONObject argsObj = (JSONObject) eventObj.get("args");
              for (Object keyObject : argsObj.keySet()) {
                String key = (String) keyObject;
                String value = (String) ((JSONArray) argsObj.get(key)).get(0);
                ontologyHierarchy.assertEventRoleIsInOntology(value,
                    "AccentKbpEventConverter.readEventMappingJson");   // schema check
                key2value.put(key, value);
              }
            }
          }
        }
      }

    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  public static List<String> readLinesIntoList(String file) {
    List<String> lines = new ArrayList<String>();

    int nLine = 0;

    try {
      BufferedReader reader = new BufferedReader(new FileReader(file));
      String sline;
      while ((sline = reader.readLine()) != null) {
        if (nLine++ % 100000 == 0) {
          System.out.println("# lines read: " + nLine);
        }

        lines.add(sline);
      }
      reader.close();
    } catch (IOException e) {
      e.printStackTrace();
    }

    return lines;
  }

  // +2
  public static ImmutableMultimap<SentenceTheory, EventMention> mapAccentEventForDoc(
      final DocTheory docTheory) {
    final ImmutableMultimap.Builder<SentenceTheory, EventMention> ret = ImmutableMultimap.builder();
    icewsEventMentionEventMentionMap.clear();
    for (ICEWSEventMention icewsEventMention : docTheory.icewsEventMentions()) {
//            String icewsEventString = toString(icewsEventMention, docTheory);
//            System.out.println("=========================");
//            System.out.println("====== before");
//            System.out.println(icewsEventString);
      final List<Pair<SentenceTheory, EventMention>> eventMentions =
          toEventMentions(icewsEventMention, docTheory);
//            System.out.println("====== after");
//            for(int idx=0; idx<eventMentions.size(); idx++) {
//                Pair<SentenceTheory, EventMention> pair = eventMentions.get(idx);
//                System.out.println("== event" + idx);
//                String eventString = toString(pair.getRight(), docTheory);
//                System.out.println(eventString);
//                System.out.println("======");
//            }

      for (final Pair<SentenceTheory, EventMention> eventMentionPair : eventMentions) {
        ret.put(eventMentionPair.getKey(), eventMentionPair.getValue());

        //Maintain global mapping table
        Set<EventMention> buf = icewsEventMentionEventMentionMap.getOrDefault(icewsEventMention,new HashSet<>());
        buf.add(eventMentionPair.getValue());
        icewsEventMentionEventMentionMap.put(icewsEventMention,buf);
      }
    }

    return ret.build();
  }

//    public static Pair<ImmutableMultimap<SentenceTheory, EventMention>, ImmutableMultimap<SentenceTheory, EventMention>> mapKBPEventForDoc(final DocTheory docTheory) {
//        final ImmutableMultimap.Builder<SentenceTheory, EventMention> addRet = ImmutableMultimap.builder();
//        final ImmutableMultimap.Builder<SentenceTheory, EventMention> removeRet = ImmutableMultimap.builder();
//
//        for(int sid=0; sid<docTheory.numSentences(); sid++) {
//            final SentenceTheory sentenceTheory=docTheory.sentenceTheory(sid);
//
//            for(final EventMention eventMention : sentenceTheory.eventMentions()) {
//                final List<Pair<SentenceTheory, EventMention>> eventMentions = toEventMentions(eventMention, sentenceTheory);
//
//                if(!eventMentions.isEmpty()) {
//                    for(final Pair<SentenceTheory, EventMention> eventMentionPair : eventMentions) {
//                        addRet.put(eventMentionPair.getKey(), eventMentionPair.getValue());
//                    }
//
//                    // update must-remove event mentions
//                    removeRet.put(sentenceTheory, eventMention);
//                }
//            }
//        }
//
//        return Pair.of(addRet.build(), removeRet.build());
//    }

//    public static void main(String [] args) throws IOException {
//        String strListSerifXmls = "/nfs/raid87/u10/users/bmin/Runjobs/expts/causeex_pipeline/causeex_m17.sample_500.v1/event_consolidation_serifxml_out.list";
//        String strJsonFile = "/nfs/ld100/u10/bmin/repo_clean_for_exp_causeex/CauseEx/util/python/knowledge_base/data_files/event_mapping.json";
//        String strOutputDir = "/nfs/ld100/u10/bmin/temp/test_out/";
//        String strFileMapping = "/nfs/ld100/u10/bmin/repo_clean_for_exp_causeex/CauseEx/lib/serif_data/accent/cameo_code_to_event_type.txt";
//
//        readEventMappingJson(strJsonFile);
//        LoadCameoCodeToEventType(strFileMapping);
//
//        List<File> filesToProcess = new ArrayList<File>();
//        List<String> listStringFiles = readLinesIntoList(strListSerifXmls);
//        for(String strFile : listStringFiles)
//            filesToProcess.add(new File(strFile));
//
//        SerifXMLLoader serifXMLLoader = SerifXMLLoader.builderWithDynamicTypes().allowSloppyOffsets().build();
//        SerifXMLWriter serifXMLWriter = SerifXMLWriter.create();
//
//        // read sentence theories
//        for (DocTheory docTheory : SerifIOUtils.docTheoriesFromFiles(filesToProcess, serifXMLLoader)) {
//            System.out.println("=== Processing " + docTheory.docid().asString());
//
//            // newly created event mentions
//            Map<SentenceTheory, List<EventMention>> sentenceTheory2eventMentions = new HashMap<SentenceTheory, List<EventMention>>();
//            // event mentions to remove
//            Map<SentenceTheory, Set<EventMention>> sentenceTheory2mustRemoveEventMentions = new HashMap<SentenceTheory, Set<EventMention>>();
//
//            // convert ICEWS events
//            for(ICEWSEventMention icewsEventMention : docTheory.icewsEventMentions()) {
//                String icewsEventString = toString(icewsEventMention, docTheory);
//                System.out.println("=========================");
//                System.out.println("====== before");
//                System.out.println(icewsEventString);
//
//                List<Pair<SentenceTheory, EventMention>> eventMentions = toEventMentions(icewsEventMention, docTheory);
//                System.out.println("====== after");
//                for(int idx=0; idx<eventMentions.size(); idx++) {
//                    Pair<SentenceTheory, EventMention> pair = eventMentions.get(idx);
//                    System.out.println("== event" + idx);
//                    String eventString = toString(pair.getRight(), docTheory);
//                    System.out.println(eventString);
//                    System.out.println("======");
//                }
//
//                for(Pair<SentenceTheory, EventMention> eventMentionPair : eventMentions) {
//                    if(!sentenceTheory2eventMentions.containsKey(eventMentionPair.getKey()))
//                        sentenceTheory2eventMentions.put(eventMentionPair.getKey(), new ArrayList<EventMention>());
//                    sentenceTheory2eventMentions.get(eventMentionPair.getKey()).add(eventMentionPair.getValue());
//                }
//
//            }
//
//            // convert KBP events
//            for(int sid=0; sid<docTheory.numSentences(); sid++) {
//                SentenceTheory sentenceTheory=docTheory.sentenceTheory(sid);
//
//                for(EventMention eventMention : sentenceTheory.eventMentions()) {
//
//                    List<Pair<SentenceTheory, EventMention>> eventMentions = toEventMentions(eventMention, sentenceTheory);
//
//                    if(!eventMentions.isEmpty()) {
//                        String kbpEventString = toString(eventMention, docTheory);
//                        System.out.println("=========================");
//                        System.out.println("====== before");
//                        System.out.println(kbpEventString);
//
//                        System.out.println("====== after");
//                        for (int idx = 0; idx < eventMentions.size(); idx++) {
//                            Pair<SentenceTheory, EventMention> pair = eventMentions.get(idx);
//                            System.out.println("== event" + idx);
//                            String eventString = toString(pair.getRight(), docTheory);
//                            System.out.println(eventString);
//                            System.out.println("======");
//                        }
//
//                        for(Pair<SentenceTheory, EventMention> eventMentionPair : eventMentions) {
//                            if(!sentenceTheory2eventMentions.containsKey(eventMentionPair.getKey()))
//                                sentenceTheory2eventMentions.put(eventMentionPair.getKey(), new ArrayList<EventMention>());
//                            sentenceTheory2eventMentions.get(eventMentionPair.getKey()).add(eventMentionPair.getValue());
//                        }
//
//                        // update must-remove event mentions
//                        if(!sentenceTheory2mustRemoveEventMentions.containsKey(sentenceTheory))
//                            sentenceTheory2mustRemoveEventMentions.put(sentenceTheory, new HashSet<EventMention>());
//                        sentenceTheory2mustRemoveEventMentions.get(sentenceTheory).add(eventMention);
//                    }
//                }
//            }
//
//            // update docTheory
//            for(SentenceTheory sentenceTheory : sentenceTheory2eventMentions.keySet()) {
//                List<EventMention> eventMentionList = new ArrayList<EventMention>();
//
//                // add exiting event mentions
//                for(EventMention eventMention : sentenceTheory.eventMentions()) {
//                    // skip event mentions that must be removed
//                    if(sentenceTheory2mustRemoveEventMentions.containsKey(sentenceTheory)) {
//                        if(sentenceTheory2mustRemoveEventMentions.get(sentenceTheory).contains(eventMention))
//                            continue;
//                    }
//
//                    eventMentionList.add(eventMention);
//                }
//
//                // add event mentions converted from ICEWS events
//                eventMentionList.addAll(sentenceTheory2eventMentions.get(sentenceTheory));
//
//                docTheory = docTheory.modifiedCopyBuilder()
//                        .events(Events.absent())
//                        .replacePrimarySentenceTheory(sentenceTheory,
//                                sentenceTheory.modifiedCopyBuilder().eventMentions(EventMentions.create(sentenceTheory.parse(), eventMentionList)).build())
//                        .build();
//            }
//
//            String strOutputSerifXml = strOutputDir + docTheory.docid().asString() + ".xml";
//            serifXMLWriter.saveTo(docTheory, strOutputSerifXml);
//        }
//    }

    public static double ACCENT_EVENT_SCORE = 0.7;
}
