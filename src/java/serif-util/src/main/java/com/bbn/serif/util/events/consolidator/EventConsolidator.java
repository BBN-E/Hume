package com.bbn.serif.util.events.consolidator;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.WordAndPOS;
import com.bbn.serif.theories.actors.ActorMention;
import com.bbn.serif.theories.DocTheory;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.Events;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.TokenSequence;
import com.bbn.serif.types.EntityType;
import com.bbn.serif.util.AddEventMentionByPOSTags;
import com.bbn.serif.util.Pair;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.events.consolidator.common.EventRoleConstants;
import com.bbn.serif.util.events.consolidator.common.EventTypeConstants;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.events.consolidator.common.SentenceNPs;
import com.bbn.serif.util.events.consolidator.proputil.PropositionUtils;

import com.google.common.base.Charsets;
import com.google.common.base.Optional;
import com.google.common.collect.HashMultimap;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableListMultimap;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Multimap;
import com.google.common.collect.Sets;
import com.google.common.io.Files;
import com.google.common.collect.ArrayListMultimap;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashMap;


public class EventConsolidator {

  int before_merge_count = 0;
  int after_merge_count = 0;

//    public static List<EventMention> mergeCompatibleEventMentions(final ImmutableList<EventMention> mentions, final OntologyHierarchy ontologyHierarchy, final SentenceTheory st) {
//        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();
//
//        final ImmutableSetMultimap<String, EventMention> mentionGroups = groupByAnchor(mentions);
//
//        for(final String node : mentionGroups.keySet()) {
//            List<EventMention> ms = Lists.newArrayList(mentionGroups.get(node));
//
//            Set<Integer> mergedIndices = Sets.newHashSet();
//            for(int i=0; (i+1)<ms.size(); i++) {
//                for(int j=(i+1); j<ms.size(); j++) {
//                    if(!mergedIndices.contains(i) && !mergedIndices.contains(j)) {
//                        if(ontologyHierarchy.isEventTypesCompatible(ms.get(i).type().asString(), ms.get(j).type().asString())) {
//                            final EventMention target_em = EventMentionUtils
//                                .getEventWithMoreArguments(ms.get(i), ms.get(j));
//                            if(ms.get(i).equals(target_em)) {
//                                ms.set(i, EventMentionUtils.mergeEventMentions(ms.get(i), ms.get(j), st));
//                                mergedIndices.add(j);
//                            } else {
//                                ms.set(j, EventMentionUtils.mergeEventMentions(ms.get(j), ms.get(i), st));
//                                mergedIndices.add(i);
//                            }
//                        }
//                    }
//                }
//            }
//
//            for(int i=0; i<ms.size(); i++) {
//                if(!mergedIndices.contains(i)) {
//                    ret.add(ms.get(i));
//                }
//            }
//        }
//
//        return ret.build();
//    }

  // +2
  public static List<ImmutableList<EventMention.EventType>> pruneIndividualUsingSamePathHierarchy(
      final List<ImmutableList<EventMention.EventType>> emEventTypes, final OntologyHierarchy oh) {

    final List<ImmutableList<EventMention.EventType>> ret = Lists.newArrayList();

    for(int index=0; index<emEventTypes.size(); index++) {
      Set<EventMention.EventType> discardTypes = Sets.newHashSet();

      ImmutableList<EventMention.EventType> types = emEventTypes.get(index);
      for(int i=0; (i+1) < types.size(); i++) {
        for(int j=(i+1); j<types.size(); j++) {
          final Optional<ImmutableList<String>> paths1 = oh.getHierarchy(types.get(i).eventType().asString());
          final Optional<ImmutableList<String>> paths2 = oh.getHierarchy(types.get(j).eventType().asString());

          if (!paths1.isPresent() && types.get(i).eventType().asString().compareTo(EventTypeConstants.EVENT) != 0) {
            System.out.println("ERROR: Cannot find " + types.get(i).eventType().asString() + " in the ontology");
          }
          if (!paths2.isPresent() && types.get(j).eventType().asString().compareTo(EventTypeConstants.EVENT) != 0) {
            System.out.println("ERROR: Cannot find " + types.get(j).eventType().asString() + " in the ontology");
          }

          if (paths1.isPresent() && paths2.isPresent()) {
            final Optional<Pair<String, String>> sameHierarchyPaths = oh.getSameHierarchyPath(paths1.get(), paths2.get());

            if (sameHierarchyPaths.isPresent()) {
              final String path1 = sameHierarchyPaths.get().getFirst();
              final String path2 = sameHierarchyPaths.get().getSecond();

              final String longerPath = oh.getLongerPath(path1, path2);
              if(longerPath.equalsIgnoreCase(path1)) {
                discardTypes.add(types.get(j));
              } else {
                discardTypes.add(types.get(i));
              }
            }
          }
        }
      }

      final ImmutableList.Builder<EventMention.EventType> acceptTypes = ImmutableList.builder();
      for(final EventMention.EventType type : types) {
        if(!discardTypes.contains(type)) {
          acceptTypes.add(type);
        }
      }
      ret.add(acceptTypes.build());
    }

    return ret;
  }

  // +2
  public static List<ImmutableList<EventMention.EventType>> prunePairUsingSamePathHierarchy(
      final ImmutableList<EventMention.EventType> types1,
      final ImmutableList<EventMention.EventType> types2, final OntologyHierarchy oh,
      final EventMention em1, final EventMention em2,
      final ImmutableList<EventMention> preferredMentions) {

    Set<EventMention.EventType> discardTypes1 = Sets.newHashSet();
    Set<EventMention.EventType> discardTypes2 = Sets.newHashSet();

    for(final EventMention.EventType type1 : types1) {
      for(final EventMention.EventType type2 : types2) {
        final Optional<ImmutableList<String>> paths1 = oh.getHierarchy(type1.eventType().asString());
        final Optional<ImmutableList<String>> paths2 = oh.getHierarchy(type2.eventType().asString());

        if (!paths1.isPresent() && type1.eventType().asString().compareTo(EventTypeConstants.EVENT) != 0) {
          System.out.println("ERROR: Cannot find " + type1.eventType().asString() + " in the ontology");
        }
        if (!paths2.isPresent() && type2.eventType().asString().compareTo(EventTypeConstants.EVENT) != 0) {
          System.out.println("ERROR: Cannot find " + type2.eventType().asString() + " in the ontology");
        }

        if (paths1.isPresent() && paths2.isPresent()) {
          final Optional<Pair<String, String>> sameHierarchyPaths = oh.getSameHierarchyPath(paths1.get(), paths2.get());

          if (sameHierarchyPaths.isPresent()) {
            // is one event mention preferred over the other?
            boolean prefer_type1 = false;
            boolean prefer_type2 = false;
            for (final EventMention em : preferredMentions) {
              if (em.equals(em1)) {
                prefer_type1 = true;
                break;
              }
            }
            for (final EventMention em : preferredMentions) {
              if (em.equals(em2)) {
                prefer_type2 = true;
                break;
              }
            }

            if (prefer_type1 && !prefer_type2) {
              // discard type2
              discardTypes2.add(type2);
            } else if (!prefer_type1 && prefer_type2) {
              // discard type1
              discardTypes1.add(type1);
            } else {
              final String path1 = sameHierarchyPaths.get().getFirst();
              final String path2 = sameHierarchyPaths.get().getSecond();

              final String longerPath = oh.getLongerPath(path1, path2);
              if(longerPath.equalsIgnoreCase(path1)) {
                // discard type2
                discardTypes2.add(type2);
              } else {
                // discard type1
                discardTypes1.add(type1);
              }
            }
          } else {
            System.out.println("sameHierarchyPaths or pathsSharingPrefix is not present");
          }
        } else {
          System.out
              .println("WARNING: paths1 or paths2 are not present, which should not happen");
        }

      }
    }

    List<ImmutableList<EventMention.EventType>> ret = Lists.newArrayList();

    final ImmutableList.Builder<EventMention.EventType> acceptTypes1 = ImmutableList.builder();
    for(final EventMention.EventType type1 : types1) {
      if(!discardTypes1.contains(type1)) {
        acceptTypes1.add(type1);
      }
    }
    ret.add(acceptTypes1.build());

    final ImmutableList.Builder<EventMention.EventType> acceptTypes2 = ImmutableList.builder();
    for(final EventMention.EventType type2 : types2) {
      if(!discardTypes2.contains(type2)) {
        acceptTypes2.add(type2);
      }
    }
    ret.add(acceptTypes2.build());

    return ret;
  }

  // +2
  public static ImmutableList<EventMention> mergeSamePathEventMentions(
      final ImmutableList<EventMention> mentions, final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies,
      final SentenceTheory st, final ImmutableList<EventMention> preferredMentions) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    final ImmutableSetMultimap<String, EventMention> mentionGroups =
        EventMentionUtils.groupByAnchor(mentions);

    for (final String node : mentionGroups.keySet()) {
      List<EventMention> ms = Lists.newArrayList(mentionGroups.get(node));

      // ========== prune event types ============
      List<ImmutableList<EventMention.EventType>> emEventTypes = new ArrayList<>();
      // capture existing EventMentionType
      for(final EventMention m : ms) {
        emEventTypes.add(ImmutableList.copyOf(m.eventTypes()));
      }

      final OntologyHierarchy oh = ontologyHierarchies.get(OntologyHierarchy.INTERNAL_ONTOLOGY);

      // first, go through each one individually to prune
      emEventTypes = pruneIndividualUsingSamePathHierarchy(emEventTypes, oh);

      // then go through pairs and prune
      int emEventTypesSize = emEventTypes.size();
      for (int i = 0; (i + 1) < emEventTypesSize; i++) {
        for (int j = (i + 1); j < emEventTypesSize; j++) {
          List<ImmutableList<EventMention.EventType>> acceptTypesForPair = prunePairUsingSamePathHierarchy(emEventTypes.get(i), emEventTypes.get(j), oh, ms.get(i), ms.get(j), preferredMentions);
          emEventTypes.set(i, acceptTypesForPair.get(0));
          emEventTypes.set(j, acceptTypesForPair.get(1));
        }
      }

      // ============= prune factor types =============
      List<ImmutableList<EventMention.EventType>> emFactorTypes = new ArrayList<>();

      // even if we are not supplying a factor ontology, we need to do the following, to ensure ms.size() == emEventTypes.size() == emFactorTypes.size()
      for(final EventMention m : ms) {
        emFactorTypes.add(ImmutableList.copyOf(m.factorTypes()));
      }
      if(ontologyHierarchies.containsKey(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY)) {
        // capture existing EventMentionType
        final OntologyHierarchy ohFactor = ontologyHierarchies.get(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY);

        // first, go through each one individually to prune
        emFactorTypes = pruneIndividualUsingSamePathHierarchy(emFactorTypes, ohFactor);

        // then go through pairs and prune
        for (int i = 0; (i + 1) < emFactorTypes.size(); i++) {
          for (int j = (i + 1); j < emFactorTypes.size(); j++) {
            List<ImmutableList<EventMention.EventType>> acceptTypesForPair = prunePairUsingSamePathHierarchy(emFactorTypes.get(i), emFactorTypes.get(j), ohFactor, ms.get(i), ms.get(j), preferredMentions);

            emFactorTypes.set(i, acceptTypesForPair.get(0));
            emFactorTypes.set(j, acceptTypesForPair.get(1));
          }
        }
      }

      for(int i=0; i < ms.size(); i++) {
        final Optional<EventMention> m = EventMentionUtils.reviseEventTypeAsNecessary(ms.get(i), emEventTypes.get(i), emFactorTypes.get(i));
        if(m.isPresent()) {
          ret.add(m.get());
        }
      }

    }

    return ret.build();
  }

  static EventMention MergeEventType(EventMention src,EventMention dst){
      // Cannot handle legacy EventType
      // Handle event type
      Map<String, EventMention.EventType> eventTypeMap = new HashMap<>();
      for(EventMention.EventType eventType: dst.eventTypes()){
          eventTypeMap.put(eventType.eventType().asString(),eventType);
      }
      for(EventMention.EventType eventType:src.eventTypes()){
          if(!eventTypeMap.containsKey(eventType.eventType().asString())){
              eventTypeMap.put(eventType.eventType().asString(),eventType);
          }
      }
      // Handle factor type
      Map<String, EventMention.EventType> factorTypeMap = new HashMap<>();
      for(EventMention.EventType factotType:dst.factorTypes()){
          factorTypeMap.put(factotType.eventType().asString(),factotType);
      }
      for(EventMention.EventType factorType:src.factorTypes()){
          if(!factorTypeMap.containsKey(factorType.eventType().asString())){
              factorTypeMap.put(factorType.eventType().asString(),factorType);
          }
      }
      EventMention.Builder modifiedDst = dst.modifiedCopyBuilder();
      modifiedDst.setEventTypes(new ArrayList<>(eventTypeMap.values()));
      modifiedDst.setFactorTypes(new ArrayList<>(factorTypeMap.values()));
      return modifiedDst.build();
  }

  // +2
  // Given 2 event mentions that share an anchor, use the event mention that has the covering arguments.But note that this does not limit comparisons to between events of the same event-type.
  public static ImmutableList<EventMention> mergeByCoveringArguments(
      final ImmutableList<EventMention> mentions,
      final SentenceTheory st) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    final ImmutableSetMultimap<String, EventMention> mentionGroups =
        EventMentionUtils.groupByAnchor(mentions);

    for (final String node : mentionGroups.keySet()) {
      List<EventMention> ms = Lists.newArrayList(mentionGroups.get(node));

      Set<Integer> mergedIndices = Sets.newHashSet();
      for (int i = 0; (i + 1) < ms.size(); i++) {
        for (int j = (i + 1); j < ms.size(); j++) {
          if (!mergedIndices.contains(i) && !mergedIndices.contains(j)) {
            final Optional<EventMention> coveringMention =
                EventMentionUtils.getEventWithCoveringArguments(ms.get(i), ms.get(j));
            if (coveringMention.isPresent()) {
              if (ms.get(i).equals(coveringMention.get())) {
                mergedIndices.add(j);
                ms.set(i,MergeEventType(ms.get(j),ms.get(i)));
              } else {
                mergedIndices.add(i);
                ms.set(j,MergeEventType(ms.get(i),ms.get(j)));
              }
            }
          }
        }
      }

      for (int i = 0; i < ms.size(); i++) {
        if (!mergedIndices.contains(i)) {
          ret.add(ms.get(i));
        }
      }
    }

    return ret.build();
  }

  // +1
  // construct an event argument with the new normalizedRole
  public static Optional<EventMention.Argument> constructNormalizedArgument(
      final EventMention.Argument arg, final String normalizedRole) {
    if (arg instanceof EventMention.ValueMentionArgument) {
      EventMention.Argument newArg = EventMention.ValueMentionArgument
          .from(Symbol.from(normalizedRole),
              ((EventMention.ValueMentionArgument) arg).valueMention(),
              arg.score());
      return Optional.of(newArg);
    } else if (arg instanceof EventMention.MentionArgument) {
      EventMention.Argument newArg = EventMention.MentionArgument
          .from(Symbol.from(normalizedRole),
              ((EventMention.MentionArgument) arg).mention(), arg.score());
      return Optional.of(newArg);
    } else {
      return Optional.absent();
    }
  }

  // +2
  public static EventMention normalizeEventArguments(final EventMention em) {
    Set<String> allowedRoles =
        Sets.newHashSet(EventRoleConstants.HAS_ACTOR, EventRoleConstants.HAS_ACTIVE_ACTOR,
            EventRoleConstants.HAS_AFFECTED_ACTOR, EventRoleConstants.HAS_LOCATION,
            EventRoleConstants.HAS_ORIGIN_LOCATION, EventRoleConstants.HAS_DESTINATION_LOCATION,
            EventRoleConstants.HAS_INTERMEDIATE_LOCATION, EventRoleConstants.HAS_ARTIFACT,
            EventRoleConstants.HAS_TIME, EventRoleConstants.HAS_START_TIME,
            EventRoleConstants.HAS_END_TIME, EventRoleConstants.HAS_DURATION);
    Set<String> seenIds = Sets.newHashSet();

    final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();

    for (final EventMention.Argument arg : em.arguments()) {
      final String role = arg.role().asString().toLowerCase();
      Optional<String> normalizedRole;

      if (role.equals("actor") || role.equals("person") || role.equals("entity")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_ACTOR);
      } else if (role.equals("active") || role.equals("agent") || role.equals("provider")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_ACTIVE_ACTOR);
      } else if (role.equals("affected") || role.equals("patient") || role.equals("recipient")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_AFFECTED_ACTOR);
      } else if (role.equals("place") || role.equals("location") || role.equals("has_location")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_LOCATION);
      } else if (role.equals("sourcelocation") || role.equals("origin")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_ORIGIN_LOCATION);
      } else if (role.equals("destinationlocation") || role.equals("targetlocation") || role
          .equals("destination")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_DESTINATION_LOCATION);
      } else if (role.equals("has_intermediate_location")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_INTERMEDIATE_LOCATION);
      } else if (role.equals("artifact") || role.equals("has_artifact")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_ARTIFACT);
      } else if (role.equals("has_time") || role.equals("time-within") || role.equals("time")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_TIME);
      } else if (role.equals("has_start_time")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_START_TIME);
      } else if (role.equals("has_end_time")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_END_TIME);
      } else if (role.equals("has_duration")) {
        normalizedRole = Optional.of(EventRoleConstants.HAS_DURATION);
      } else if (role.equals("speaker") || role.equals("vehicle") || role.equals("has_topic")
          || role.equals("position_or_role") || role
          .equals("associated_monetary_amount")) { // Should we skip these?
        continue;
      } else {
        normalizedRole = Optional.of(role);
      }

      if (normalizedRole.isPresent()) {
        if (!allowedRoles.contains(normalizedRole.get())) {
          System.out.println(
              "ERROR: EventConsolidator.normalizeEventArguments: Encountering event-role "
                  + normalizedRole.get() + " which is not allowed");
          System.exit(1);
        }

        final String id =
            normalizedRole.get() + ":" + arg.span().startCharOffset().asInt() + ":" + arg.span()
                .endCharOffset().asInt();
        if (!seenIds.contains(id)) {
          seenIds.add(id);
          Optional<EventMention.Argument> normalizedArg =
              constructNormalizedArgument(arg, normalizedRole.get());
          if (normalizedArg.isPresent()) {
            newArgsBuilder.add(normalizedArg.get());
          }
        }
      }
    }
    return EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build());
  }

//    public SentenceTheory normalizeEventArguments(final List<EventMention> eventMentions, final SentenceTheory st) {
//        List<EventMention> newEMs = Lists.newArrayList();
//        for(final EventMention em : eventMentions) {
//            newEMs.add(normalizeEventArguments(em));
//        }
//
//        final SentenceTheory.Builder sentBuilder = st.modifiedCopyBuilder();
//        final SentenceTheory newSt = sentBuilder.eventMentions(new EventMentions.Builder().eventMentions(newEMs).build()).build();
//        return newSt;
//    }

//    public String argumentInfo(final EventMention.Argument arg) {
//        UnicodeFriendlyString spanText;
//        Optional<UnicodeFriendlyString> headText = Optional.absent();
//        Optional<String> entityType = Optional.absent();
//        Optional<String> mentionType = Optional.absent();
//
//        if(arg instanceof EventMention.MentionArgument) {
//            final EventMention.MentionArgument a = (EventMention.MentionArgument) arg;
//            spanText = a.mention().span().text();
//            headText = Optional.of(a.mention().head().span().text());
//            entityType = Optional.of(a.mention().entityType().toString());
//            mentionType = Optional.of(a.mention().mentionType().name().toString());
//        } else if(arg instanceof EventMention.ValueMentionArgument) {
//            final EventMention.ValueMentionArgument a = (EventMention.ValueMentionArgument) arg;
//            spanText = a.valueMention().span().text();
//            entityType = Optional.of(a.valueMention().type().asString());
//        } else {
//            spanText = arg.span().text();
//        }
//
//        return "S=[" + spanText + "] H=[" + headText.or(UnicodeFriendlyStringBuilder.forInitialString("NONE").build()) + "] E=" + entityType.or("NONE") + " M=" + mentionType.or("NONE");
//    }


  // +2
  // discard event arguments whose spans are totally covered by another event argument, and satisfies some constraints
  public static final EventMention pruneOverlappingArgument(EventMention em) {
      final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();

      // first, group arguments by role
      final ImmutableListMultimap.Builder<String, EventMention.Argument> argByRoleBuilder = ImmutableListMultimap.builder();
      for (final EventMention.Argument arg : em.arguments()) {
          final String role = arg.role().asString();
          argByRoleBuilder.put(role, arg);
      }
      final ImmutableListMultimap<String, EventMention.Argument> argByRole = argByRoleBuilder.build();

      for (final String role : argByRole.keySet()) {
          final ImmutableList<EventMention.Argument> roleArgs = argByRole.get(role);

          // we directly add all arguments that are not mentions
          for (final EventMention.Argument arg : EventMentionUtils.getNonMentionArguments(roleArgs)) {
              newArgsBuilder.add(arg);
          }

          // we will only do deduplication among 'Mention' arguments
          final ImmutableList<EventMention.MentionArgument> mentionArguments = EventMentionUtils.getMentionArguments(roleArgs);

          // we divide up 'mentionArguments' into DESC vs non-DESC arguments
          List<EventMention.MentionArgument> descArguments = Lists.newArrayList();
          List<EventMention.MentionArgument> nonDescArguments = Lists.newArrayList();
          for (int i = 0; i < mentionArguments.size(); i++) {
              final EventMention.MentionArgument arg = mentionArguments.get(i);
              final Optional<String> mentionType = EventMentionUtils.getMentionType(arg);
              if(mentionType.isPresent() && mentionType.get().equals("DESC")) {
                  descArguments.add(arg);
              } else {
                  nonDescArguments.add(arg);
              }
          }

          Set<Integer> indicesToDrop = Sets.newHashSet();
          for(int i=0; i<nonDescArguments.size(); i++) {
              final EventMention.MentionArgument arg1 = nonDescArguments.get(i);
              for(int j=(i+1); j<nonDescArguments.size(); j++) {
                  final EventMention.MentionArgument arg2 = nonDescArguments.get(j);
                  // we only compare against arguments that are of the same entity type
                  if(arg1.mention().entityType().name().equalTo(arg2.mention().entityType().name())) {
                      if(EventMentionUtils.spanCoversUsingNameHead(arg1, arg2)) {
                          indicesToDrop.add(i);
                      } else if(EventMentionUtils.spanCoversUsingNameHead(arg2, arg1)) {
                          indicesToDrop.add(j);
                      }   
                  }
              }
          } 
          List<EventMention.MentionArgument> retainedMentionArguments = Lists.newArrayList();
          for(int i=0; i<nonDescArguments.size(); i++) {
              if(!indicesToDrop.contains(i)) {
                  retainedMentionArguments.add(nonDescArguments.get(i));
              }    
          }

          // now we compare among DESC arguments
          indicesToDrop = Sets.newHashSet();
          for(int i=0; i<descArguments.size(); i++) {
              final EventMention.MentionArgument arg1 = descArguments.get(i);
              for(int j=(i+1); j<descArguments.size(); j++) {
                  final EventMention.MentionArgument arg2 = descArguments.get(j);
                  // we only compare against arguments that are of the same entity type
                  if(arg1.mention().entityType().name().equalTo(arg2.mention().entityType().name())) {
                      if(EventMentionUtils.spanCovers(arg1, arg2)) {
                          indicesToDrop.add(i);
                      } else if(EventMentionUtils.spanCovers(arg2, arg1)) {
                          indicesToDrop.add(j);
                      }   
                  }
              }
          }

          // if a DESC arg covers any of the retainedmentionArguments (non DESC), we will discard it
          for(int i=0; i<descArguments.size(); i++) {
              final EventMention.MentionArgument arg1 = descArguments.get(i);
              if(!indicesToDrop.contains(i)) {
                  boolean covers = false;
                  for(int j=0; j<retainedMentionArguments.size(); j++) {
                      final EventMention.MentionArgument arg2 = retainedMentionArguments.get(j);
                      if(arg1.mention().entityType().name().equalTo(arg2.mention().entityType().name()) && EventMentionUtils.spanCovers(arg1, arg2)) {
                          covers = true;
                          break;
                      }
                  }
                  if(covers) {
                      indicesToDrop.add(i);
                  }
              }
          } 

          for(int i=0; i<descArguments.size(); i++) {
              if(!indicesToDrop.contains(i)) {
                  retainedMentionArguments.add(descArguments.get(i));
              }
          }

          for(int i=0; i<retainedMentionArguments.size(); i++) {
              newArgsBuilder.add(retainedMentionArguments.get(i));
          }

          //if(mentionArguments.size() > retainedMentionArguments.size()) {
          //    System.out.println("===========");
          //    for(int i=0; i<mentionArguments.size(); i++) {
          //        System.out.println(EventMentionUtils.getMentionType(mentionArguments.get(i))+":"+mentionArguments.get(i).mention().head().span().text().toString()+":"+mentionArguments.get(i).span().text().toString()); 
          //    }
          //    System.out.println(">>>>>>>>>>>");
          //    for(int i=0; i<retainedMentionArguments.size(); i++) {
          //        System.out.println(EventMentionUtils.getMentionType(retainedMentionArguments.get(i))+":"+retainedMentionArguments.get(i).mention().head().span().text().toString()+":"+retainedMentionArguments.get(i).span().text().toString()); 
          //    }
          //    System.out.println("===========");
          //}

      }

      return em.modifiedCopyBuilder().setArguments(newArgsBuilder.build()).build();
     
//      Set<Integer> indicesToDrop = Sets.newHashSet();
//      for (int i = 0; i < mentionArguments.size(); i++) {
//        final EventMention.MentionArgument arg1 = mentionArguments.get(i);
//        final Optional<String> arg1MentionType = EventMentionUtils.getMentionType(arg1);
//
//        for (int j = 0; j < mentionArguments.size(); j++) {
//          if (i != j) {
//            final EventMention.MentionArgument arg2 = mentionArguments.get(j);
//            final Optional<String> arg2MentionType = EventMentionUtils.getMentionType(arg2);
//
//            if (arg1.mention().entityType().name().equalTo(arg2.mention().entityType().name())) {
//              if (EventMentionUtils.spanCovers(arg1, arg2)) {
//                if (arg1MentionType.isPresent() && (arg1MentionType.get().equals("NAME")
//                                                        || arg1MentionType.get().equals("PART")
//                                                        || arg1MentionType.get().equals("PRON"))) {
//                  indicesToDrop.add(j);
//                } else if (arg1MentionType.isPresent() && arg1MentionType.get().equals("DESC")) {
//                  if (arg2MentionType.isPresent()) {
//                    if (arg2MentionType.get().equals("NAME") || arg2MentionType.get().equals("DESC")
//                        || arg2MentionType.get().equals("PRON")) {
//                      indicesToDrop.add(j);
//                    }
//                  }
//                }
//              } else if (EventMentionUtils.spanCovers(arg2, arg1)) {
//                if (arg2MentionType.isPresent() && (arg2MentionType.get().equals("NAME")
//                                                        || arg2MentionType.get().equals("PART")
//                                                        || arg2MentionType.get().equals("PRON"))) {
//                  indicesToDrop.add(i);
//                } else if (arg2MentionType.isPresent() && arg2MentionType.get().equals("DESC")) {
//                  if (arg1MentionType.isPresent()) {
//                    if (arg1MentionType.get().equals("NAME") || arg1MentionType.get().equals("DESC")
//                        || arg1MentionType.get().equals("PRON")) {
//                      indicesToDrop.add(i);
//                    }
//                  }
//                }
//              }
//            }
//          }
//        }
//      }

                /*
                if(indicesToDrop.size() > 0) {
                    for(int i=0; i<mentionArguments.size(); i++) {
                        if(!indicesToDrop.contains(i)) {
                            System.out.println("KEEP " + argumentInfo(mentionArguments.get(i)));
                        } else {
                            System.out.println("DROP " + argumentInfo(mentionArguments.get(i)));
                        }
                    }
                }
                */

//      for (int i = 0; i < mentionArguments.size(); i++) {
//        if (!indicesToDrop.contains(i)) {
//          newArgsBuilder.add(mentionArguments.get(i));
//        }
//      }
//    }
//    return em.modifiedCopyBuilder().setArguments(newArgsBuilder.build()).build();

  }

  // +1
  public static boolean isAllCaps(final String s) {
    for (int i = 0; i < s.length(); i++) {
      final char c = s.charAt(i);
      if (Character.isLowerCase(c)) {
        return false;
      }
    }
    return true;
  }

  // +1
  public static boolean containsDash(final String s) {
    for (int i = 0; i < s.length(); i++) {
      final char c = s.charAt(i);
      if (c == '-') {
        return true;
      }
    }
    return false;
  }

  // +1
  public static boolean containsDot(final String s) {
    for (int i = 0; i < s.length(); i++) {
      final char c = s.charAt(i);
      if (c == '.') {
        return true;
      }
    }
    return false;
  }

  public static boolean isAllLetter(final String s) {
    for (int i = 0; i < s.length(); i++) {
      final char c = s.charAt(i);
      if (!Character.isLetter(c)) {
        return false;
      }
    }
    return true;
  }

  // +2
  public static SentenceTheory removeEventMentionBasedOnKeyword(
      final OntologyHierarchy ontologyHierarchy, final SentenceTheory st,
      final ImmutableSet<String> adverbs, final ImmutableSet<String> prepositions,
      final ImmutableSet<String> verbs) {
    //List<EventMention> retainedEventMentions = Lists.newArrayList();
    final ImmutableList.Builder<EventMention> retainedEventMentionsBuilder =
        ImmutableList.builder();

    for (final EventMention em : st.eventMentions()) {
      final String anchorTextOriginal = em.anchorNode().head().span().text().toString();
      final String anchorText = anchorTextOriginal.toLowerCase();
      final String anchorPOS = em.anchorNode().headPOS().asString();

      if (em.type().asString().startsWith(EventTypeConstants.QUOTATION)) {
        System.out.println("removeEventMentionBasedOnKeyword: dropping " + em.type().asString()
            + " event-mention");
        continue;
      }

      if (adverbs.contains(anchorText) || prepositions.contains(anchorText)) {
        System.out.println("removeEventMentionBasedOnKeyword: adverb/preposition, anchorText=["
            + anchorTextOriginal + "]");
        continue;
      }
      if (!anchorPOS.startsWith("NN") && !anchorPOS.startsWith("VB") && !anchorPOS.equals("JJ")) {
        System.out.println(
            "removeEventMentionBasedOnKeyword: anchorPOS=" + anchorPOS + ", anchorText=["
                + anchorTextOriginal + "]");
        continue;
      }
      if (anchorPOS.startsWith("VB") && !verbs.contains(anchorText)) {
        System.out.println(
            "removeEventMentionBasedOnKeyword: anchor is a verb, but is not in verbs set, anchorText=["
                + anchorTextOriginal + "]");
        continue;
      }

      if (EventMentionUtils.anchorIsEntityMention(em, st)) {
        System.out.println(
            "removeEventMentionBasedOnKeyword: anchor is entity/value mention, anchorText=["
                + anchorTextOriginal + "]");
        continue;
      }

      if (isAllCaps(anchorTextOriginal)) {
        System.out.println("removeEventMentionBasedOnKeyword: anchor is all caps, anchorText=["
            + anchorTextOriginal + "]");
        continue;
      }

      if (!isAllLetter(anchorTextOriginal)) {
        System.out.println(
            "removeEventMentionBasedOnKeyword: anchor contains non-letters, anchorText=["
                + anchorTextOriginal + "]");
        continue;
      }

//            if(containsDash(anchorTextOriginal)) {
//                System.out.println("removeEventMentionBasedOnKeyword: anchor contains dash, anchorText=[" + anchorTextOriginal + "]");
//                continue;
//            }
//
//            if(containsDot(anchorTextOriginal)) {
//                System.out.println("removeEventMentionBasedOnKeyword: anchor contains dot, anchorText=[" + anchorTextOriginal + "]");
//                continue;
//            }

      final ImmutableSet<String> eventTypes =
          ontologyHierarchy.getEventTypesUsingKeyword(anchorText);
      if (eventTypes.contains("NO_EVENT")) {
        System.out.println("removeEventMentionBasedOnKeyword: matched keyword [" + anchorText
            + "] against NO_EVENT");
      } else {
        retainedEventMentionsBuilder.add(em);
      }
    }

    final SentenceTheory newSt = st.modifiedCopyBuilder().eventMentions(
        new EventMentions.Builder().eventMentions(retainedEventMentionsBuilder.build()).build())
        .build();
    return newSt;
  }

  // +1
  public static ImmutableList<EventMention> addEventMentionBasedOnKeyword(
      final OntologyHierarchy ontologyHierarchy, final SentenceTheory st) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    for (int tokenIndex = 0; tokenIndex < st.tokenSequence().size(); tokenIndex++) {
      SynNode node = st.parse().nodeForToken(st.tokenSequence().token(tokenIndex));

      OffsetRange<CharOffset> nodeOffset = node.head().span().charOffsetRange();
      final ImmutableList.Builder<EventMention> emWithSameAnchorNodeBuilder =
          ImmutableList.builder();
      for (final EventMention em : st.eventMentions()) {
        if (nodeOffset.equals(em.anchorNode().head().span().charOffsetRange())) {
          emWithSameAnchorNodeBuilder.add(em);
        }
      }
      final ImmutableList<EventMention> emWithSameAnchorNode = emWithSameAnchorNodeBuilder.build();

      final ImmutableList.Builder<EventMention.Argument> nodeArgumentsBuilder =
          ImmutableList.builder();
      Set<String> seenArgumentIds = Sets.newHashSet();
      for (final EventMention em : emWithSameAnchorNode) {
        for (final EventMention.Argument arg : em.arguments()) {
          final String id = arg.span().charOffsetRange().startInclusive().asInt() + " " + arg.span()
              .charOffsetRange().endInclusive().asInt() + " " + arg.role().asString();
          if (!seenArgumentIds.contains(id)) {
            seenArgumentIds.add(id);
            nodeArgumentsBuilder.add(arg);
          }
        }
      }
      final ImmutableList<EventMention.Argument> nodeArguments = nodeArgumentsBuilder.build();
      //if(emWithSameAnchorNode.size()==1) {
      //    nodeArguments = emWithSameAnchorNode.get(0).arguments();
      //}

      boolean eventAdded = false;
      if (tokenIndex > 0) {
        final String bigram = ontologyHierarchy
            .getLemmaForWord(st.tokenSequence().token(tokenIndex - 1).text().toString()) + " "
            + ontologyHierarchy
            .getLemmaForWord(st.tokenSequence().token(tokenIndex).text().toString());
        final ImmutableSet<String> biEventTypes =
            ontologyHierarchy.getEventTypesUsingKeyword(bigram);
        if (!biEventTypes.contains("NO_EVENT")) {
          for (final String et : biEventTypes) {
            // is there an existing event mention with the same anchor head?
            boolean existing = false;
            for (final EventMention em : st.eventMentions()) {
              if (nodeOffset.equals(em.anchorNode().head().span().charOffsetRange())
                  && em.type().asString().compareTo(et) == 0) {
                existing = true;
                break;
              }
            }

            if (!existing) {
              //System.out.println("addEventMentionBasedOnKeyword: matched keyword [" + bigram + "] against event type " + et);
              List<EventMention.EventType> ets = Lists.newArrayList(EventMention.EventType.from(Symbol.from(et), EventConsolidator.EVENTMENTION_BASED_ON_KEYWORD_SCORE, Optional.absent(), Optional.absent()));
              EventMention.Builder emBuilder = EventMention.builder(Symbol.from(et)).setAnchorNode(node).setAnchorPropFromNode(st).setScore(EventConsolidator.EVENTMENTION_BASED_ON_KEYWORD_SCORE).setModel(Symbol.from("Keyword"));
              if(ontologyHierarchy.getOntologyName().equals(OntologyHierarchy.INTERNAL_ONTOLOGY)) {
                emBuilder.setEventTypes(ets);
              } else if(ontologyHierarchy.getOntologyName().equals(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY)) {
                emBuilder.setFactorTypes(ets);
              }
              ret.add(emBuilder.build());
              eventAdded = true;
            }
          }
        }
      }

      // after trying to add events based on bigrams, we will try to add events based on unigrams
      final String unigram = ontologyHierarchy
          .getLemmaForWord(st.tokenSequence().token(tokenIndex).text().toString());
      final ImmutableSet<String> uniEventTypes =
          ontologyHierarchy.getEventTypesUsingKeyword(unigram);
      if (!uniEventTypes.contains("NO_EVENT")) {
        for (final String et : uniEventTypes) {
          // is there an existing event mention with the same anchor head?
          boolean existing = false;
          for (final EventMention em : st.eventMentions()) {
            if (nodeOffset.equals(em.anchorNode().head().span().charOffsetRange())
                && em.type().asString().compareTo(et) == 0) {
              existing = true;
              break;
            }
          }

          if (!existing) {
            //System.out.println("addEventMentionBasedOnKeyword: matched keyword [" + unigram + "] against event type " + et);

            final ImmutableList.Builder<EventMention.Argument> myArgumentsBuilder =
                ImmutableList.builder();
            for (final EventMention.Argument arg : nodeArguments) {
              myArgumentsBuilder.add(arg.copyWithDifferentScore(arg.score()));
            }

            List<EventMention.EventType> ets =
                Lists.newArrayList(EventMention.EventType.from(Symbol.from(et), EventConsolidator.EVENTMENTION_BASED_ON_KEYWORD_SCORE, Optional.absent(), Optional.absent()));
            EventMention.Builder emBuilder =
                EventMention.builder(Symbol.from(et)).setAnchorNode(node).setAnchorPropFromNode(st)
                    .setScore(EventConsolidator.EVENTMENTION_BASED_ON_KEYWORD_SCORE).setArguments(myArgumentsBuilder.build())
                    .setModel(Symbol.from("Keyword"));
            if (ontologyHierarchy.getOntologyName().equals(OntologyHierarchy.INTERNAL_ONTOLOGY)) {
              emBuilder.setEventTypes(ets);
            } else if (ontologyHierarchy.getOntologyName()
                .equals(OntologyHierarchy.CAUSAL_FACTOR_ONTOLOGY)) {
              emBuilder.setFactorTypes(ets);
            }
            ret.add(emBuilder.build());

            eventAdded = true;
          }
        }
      }

    }
    return ret.build();
  }

  /////////////////////

  // +1
  public static ImmutableListMultimap<String, EventMention> collectEventMentionsFromSurroundingSentences(
      final DocTheory docTheory, final int sentenceIndex, final int span) {
    final ImmutableListMultimap.Builder<String, EventMention> eventMentionsByTypeBuilder =
        ImmutableListMultimap.builder();

    for (int j = (sentenceIndex - span); j <= sentenceIndex;
         j++) {    // we determined that grabbing actors from following sentences is mostly noisy
      if (j >= 0 && j < docTheory.numSentences()) {
        for (final EventMention em : docTheory.sentenceTheory(j).eventMentions()) {
          final String eventType = em.type().asString();
          eventMentionsByTypeBuilder.put(eventType, em);
        }
      }
    }
    return eventMentionsByTypeBuilder.build();
  }

  // +1
  // If an event mention does not have has_actor nor has_active_actor nor has_affected_actor, then we grab those from neighboring previous sentence(s)
  public static DocTheory propagateEventArgumentsAcrossSentence(final DocTheory docTheory,
      int span) {
    final ImmutableSet<String> targetRoles = ImmutableSet.copyOf(Arrays
        .asList(EventRoleConstants.HAS_ACTOR, EventRoleConstants.HAS_ACTIVE_ACTOR,
            EventRoleConstants.HAS_AFFECTED_ACTOR));

    final DocTheory.Builder docBuilder = docTheory.modifiedCopyBuilder();
    docBuilder.events(Events.absent());

    for (int i = 0; i < docTheory.numSentences(); ++i) {
      // event types in this sentence
      final ImmutableSet.Builder<String> targetEventTypesBuilder = ImmutableSet.builder();
      for (final EventMention em : docTheory.sentenceTheory(i).eventMentions()) {
        targetEventTypesBuilder.add(em.type().asString());
      }
      final ImmutableSet<String> targetEventTypes = targetEventTypesBuilder.build();

      // TODO : now that we have a list of EventMentionType and EventMentionFactorType, it makes this grouping by eventType confusing
      // I shall not change this for the moment, to favor precision
      //
      // first, collect event mentions from surrounding sentences, grouped by eventType
      final ImmutableListMultimap<String, EventMention> eventMentionsByType =
          collectEventMentionsFromSurroundingSentences(docTheory, i, span);
      final ImmutableListMultimap<String, EventMention> eventMentionsByTypeIntraSentence =
          collectEventMentionsFromSurroundingSentences(docTheory, i, 0);

      // now aggregate arguments for the event types that are present in the current sentence
      final ImmutableListMultimap.Builder<String, EventMention.Argument>
          eventTypeToArgumentsBuilder = ImmutableListMultimap.builder();
      final ImmutableListMultimap.Builder<String, EventMention.Argument>
          eventTypeToArgumentsIntraSentenceBuilder = ImmutableListMultimap.builder();
      for (final String eventType : targetEventTypes) {
        final ImmutableList<EventMention.Argument> newArgs = EventMentionUtils
            .aggregateArgumentsFromEventMentions(eventMentionsByType.get(eventType));
        for (final EventMention.Argument arg : EventMentionUtils
            .filterForRoles(newArgs, targetRoles)) {
          eventTypeToArgumentsBuilder.put(eventType, arg);
        }
        final ImmutableList<EventMention.Argument> newArgsIntraSentence = EventMentionUtils
            .aggregateArgumentsFromEventMentions(eventMentionsByTypeIntraSentence.get(eventType));
        for (final EventMention.Argument arg : EventMentionUtils
            .filterForRoles(newArgsIntraSentence, targetRoles)) {
          eventTypeToArgumentsIntraSentenceBuilder.put(eventType, arg);
        }
      }
      final ImmutableListMultimap<String, EventMention.Argument> eventTypeToArguments =
          eventTypeToArgumentsBuilder.build();
      final ImmutableListMultimap<String, EventMention.Argument> eventTypeToArgumentsIntraSentence =
          eventTypeToArgumentsIntraSentenceBuilder.build();

      // now go through event mentions in this sentence, and replace their event arguments
      final ImmutableList.Builder<EventMention> newEventMentionsBuilder = ImmutableList.builder();
      for (final EventMention em : docTheory.sentenceTheory(i).eventMentions()) {
        if (em.type().asString().compareTo(EventTypeConstants.EVENT) != 0) {

          final ImmutableList<EventMention.Argument> currentArgs = EventMentionUtils
              .unionArguments(ImmutableList.copyOf(em.arguments()),
                  eventTypeToArgumentsIntraSentence.get(em.type().asString()));
          List<EventMention.Argument> args;
          if (!EventMentionUtils.hasRole(currentArgs, EventRoleConstants.HAS_ACTOR)
              && !EventMentionUtils.hasRole(currentArgs, EventRoleConstants.HAS_ACTIVE_ACTOR)
              && !EventMentionUtils.hasRole(currentArgs, EventRoleConstants.HAS_AFFECTED_ACTOR)) {
            args = EventMentionUtils
                .unionArguments(currentArgs, eventTypeToArguments.get(em.type().asString()));
          } else {
            args = Lists.newArrayList(currentArgs);
          }

          final ImmutableList.Builder<EventMention.Argument> myArgumentsBuilder =
              ImmutableList.builder();
          for (final EventMention.Argument arg : args) {
            myArgumentsBuilder.add(arg.copyWithDifferentScore(arg.score()));
          }

          final EventMention newEm =
              EventMentionUtils.newEventMentionWithArguments(em, myArgumentsBuilder.build());
          //final EventMention newEm = EventMentionUtils.newEventMentionWithArguments(em, eventTypeToArguments.get(em.type().asString()));
          newEventMentionsBuilder.add(newEm);
        } else {
          newEventMentionsBuilder.add(em);
        }
      }

      final SentenceTheory.Builder sentBuilder = docTheory.sentenceTheory(i).modifiedCopyBuilder();
      final SentenceTheory newSt = sentBuilder.eventMentions(
          new EventMentions.Builder().eventMentions(newEventMentionsBuilder.build()).build())
          .build();
      docBuilder.replacePrimarySentenceTheory(docTheory.sentenceTheory(i), newSt);

//            for(final EventMention em : newSt.eventMentions()) {
//                for(final EventMention oriEm : docTheory.sentenceTheory(i).eventMentions()) {
//                    if(em.anchorNode().span().equals(oriEm.anchorNode().span())) {
//                        if(em.arguments().size() > oriEm.arguments().size()) {
//                            System.out.println("======== surrounding sentences " + i + " ========");
//                            if(i > 0) {
//                                System.out.println(docTheory.sentenceTheory(i - 1).span().tokenizedText().toString());
//                            }
//                            System.out.println(docTheory.sentenceTheory(i).span().tokenizedText().toString());
//                            if((i+1) < docTheory.numSentences()) {
//                                System.out.println(docTheory.sentenceTheory(i + 1).span().tokenizedText().toString());
//                            }
//                            System.out.println("======== BEFORE ARG PROPAGATION ========");
//                            System.out.println(EventMentionUtils.eventString(oriEm));
//                            System.out.println("======== AFTER ARG PROPAGATION ========");
//                            System.out.println(EventMentionUtils.eventString(em));
//                        }
//                    }
//                }
//            }
    }

    DocTheory newDocTheory = docBuilder.build();
    return newDocTheory;
  }

  ///////////////////

  // +1
  public static ImmutableMap<String, String> readDocumentSourceType(final String metaInfoFile)
      throws IOException {
    final ImmutableMap.Builder<String, String> ret = ImmutableMap.builder();
    for (final String line : Files.asCharSource(new File(metaInfoFile), Charsets.UTF_8)
        .readLines()) {
      String[] tokens = line.split("\t");
      ret.put(tokens[0], tokens[4]);
    }
    return ret.build();
  }

  // +1
  // we want to make the trigger text more meaningful, so expand to its covering mention when possible
  public static Optional<SynNode> findNPforEventTriggers(SynNode anchorNode,
      SentenceTheory sentenceTheory) {
    Optional<Mention> mentionOptional = Optional.absent();

    Set<String> entityTypes = new HashSet<>(
        Arrays.asList("ART", "FAC", "GPE", "LOC", "PER", "ORG", "WEA", "VEH", "MONEY"));

    float minSpanCoveringRatio = 20;
    if (anchorNode.headPOS().asString().toLowerCase().startsWith("nn")) {
      for (Mention mention : sentenceTheory.mentions()) {
        if (!mention.isName() && !mention.isPronoun()
            && mention.mentionType().name().toString().compareTo("LIST") != 0 && !entityTypes
            .contains(mention.entityType().name().asString())) {
          if (mention.span().startCharOffset().asInt() <= anchorNode.span().startCharOffset()
              .asInt() &&
              mention.span().endCharOffset().asInt() >= anchorNode.span().endCharOffset().asInt()) {
            float spanCoveringRatio =
                (mention.span().endCharOffset().asInt() - mention.span().startCharOffset().asInt()
                     + 1) * 1.0f / (
                    anchorNode.span().endCharOffset().asInt() - anchorNode.span().startCharOffset()
                        .asInt() + 1);
            if (spanCoveringRatio < minSpanCoveringRatio) {
              minSpanCoveringRatio = spanCoveringRatio;
              mentionOptional = Optional.of(mention);
            }
          }
        }
      }
    }

    if (minSpanCoveringRatio < 5) {
      return Optional.of(mentionOptional.get().node());
    } else {
      return Optional.absent();
    }
  }

  private static int findEndOfNPTokenIndex(final int currentIndex, final List<Symbol> npTags) {
    int endTokenIndex = currentIndex;

    if (npTags.get(endTokenIndex).equalTo(B) || npTags.get(endTokenIndex).equalTo(I)) {
      while (((endTokenIndex + 1) < npTags.size()) && !npTags.get(endTokenIndex + 1).equalTo(O) && !npTags.get(endTokenIndex + 1).equalTo(B)) {
        endTokenIndex += 1;
      }
    }

    return endTokenIndex;
  }

  // +2
  public static EventMention addAnchorContextWindow(final EventMention em, final SentenceTheory st,
      final SentenceNPs sentenceNPs, final List<Integer> numberOfTypedEventForEachToken,
      final ImmutableList<WordAndPOS> wordPos, final ImmutableSet<String> lightVerbs) {
    final SynNode anchorNode = em.anchorNode();
    final List<Symbol> npTags =
        sentenceNPs.toMap().get(st.sentenceNumber()).npChunks();    // B, I, O

    int startTokenIndex = anchorNode.span().startToken().index();
    final String startTokenPosTag =
        st.parse().root().get().nthTerminal(startTokenIndex).parent().get().tag().toString();

    int endTokenIndex = anchorNode.span().endToken().index();
    final String endTokenPosTag =
        st.parse().root().get().nthTerminal(endTokenIndex).parent().get().tag().toString();

    // if I am in an NP, expand left
    if (npTags.get(startTokenIndex).equalTo(I)) {
      while ((startTokenIndex - 1) >= 0 && !npTags.get(startTokenIndex - 1).equalTo(O)) {
        startTokenIndex -= 1;
        if(npTags.get(startTokenIndex).equalTo(B)) {
          break;
        }
      }
    }
    /*
    if (npTags.get(startTokenIndex).equalTo(I)) {
      while ((startTokenIndex - 1) >= 0 && !npTags.get(startTokenIndex - 1).equalTo(O)) {
        startTokenIndex -= 1;
      }
    } else if (startTokenPosTag.startsWith("VB") && (startTokenIndex - 1) >= 0) {
      final int endCharOffset = st.parse().root().get().nthTerminal(startTokenIndex -1).span().endCharOffset().asInt();
      boolean foundMention = false;
      for (final Mention m : st.mentions()) {
        if ((endCharOffset == m.span().endCharOffset().asInt()) || (endCharOffset == m.head().span().endCharOffset().asInt())) {
          foundMention = true;
        }
      }
      if(foundMention) {
        while ((startTokenIndex - 1) >= 0 && !npTags.get(startTokenIndex - 1).equalTo(O)) {
          startTokenIndex -= 1;
        }
      }
    }
    */

    /*
    // if there is an "NP of" on my left, get it
    if ((startTokenIndex - 2) >= 0) {
      int startTokenIndexCopy = startTokenIndex;

      final String wordLeft1 =
          st.tokenSequence().token(startTokenIndex - 1).tokenizedText().utf16CodeUnits().toString();
      final String posTagL1 =
          st.parse().root().get().nthTerminal(startTokenIndex - 1).parent().get().tag().toString();
      if ((wordLeft1.equals("of") || posTagL1.startsWith("RB")) && !npTags.get(startTokenIndex - 2)
          .equalTo(O)) {
        startTokenIndex -= 2;
        while ((startTokenIndex - 1) >= 0 && !npTags.get(startTokenIndex - 1).equalTo(O)) {
          startTokenIndex -= 1;
        }
      }

      // check whether we are covering blocker words
      boolean block = false;
      boolean hasTypedEvent = false;
      for (int i = startTokenIndex; i < startTokenIndexCopy; i++) {
        if (semanticPhraseBlockerWords.contains(
            st.tokenSequence().token(i).tokenizedText().utf16CodeUnits().toString()
                .toLowerCase())) {
          block = true;
        }
        if (numberOfTypedEventForEachToken.get(i).intValue() > 0) {
          hasTypedEvent = true;
        }
      }
      if (block && hasTypedEvent) {
        startTokenIndex =
            startTokenIndexCopy;       // if we are blocked, then we do not extend left
      }
    }
    */

    endTokenIndex =
        findEndOfNPTokenIndex(endTokenIndex, npTags);   // expand right until end of current NP

    final Optional<Symbol> npTagR1 =
        (endTokenIndex + 1) < npTags.size() ? Optional.of(npTags.get(endTokenIndex + 1))
                                            : Optional.absent();
    /*
    final Optional<Symbol> npTagR2 =
        (endTokenIndex + 2) < npTags.size() ? Optional.of(npTags.get(endTokenIndex + 2))
                                            : Optional.absent();
    final Optional<Symbol> npTagR3 =
        (endTokenIndex + 3) < npTags.size() ? Optional.of(npTags.get(endTokenIndex + 3))
                                            : Optional.absent();
    final Optional<String> posTagR1 = (endTokenIndex + 1) < npTags.size() ? Optional
        .of(st.parse().root().get().nthTerminal(endTokenIndex + 1).parent().get().tag().toString())
                                                                          : Optional.absent();
    final Optional<String> posTagR2 = (endTokenIndex + 2) < npTags.size() ? Optional
        .of(st.parse().root().get().nthTerminal(endTokenIndex + 2).parent().get().tag().toString())
                                                                          : Optional.absent();
    final Optional<String> wR1 = (endTokenIndex + 1) < npTags.size() ? Optional
        .of(st.tokenSequence().token(endTokenIndex + 1).tokenizedText().utf16CodeUnits().toString())
                                                                     : Optional.absent();
    final Optional<String> wR2 = (endTokenIndex + 2) < npTags.size() ? Optional
        .of(st.tokenSequence().token(endTokenIndex + 2).tokenizedText().utf16CodeUnits().toString())
                                                                     : Optional.absent();

    int endTokenIndexCopy = endTokenIndex;
    */

    if (wordPos.get(endTokenIndex).POS().asString().startsWith("VB") && lightVerbs.contains(wordPos.get(endTokenIndex).word().asString().toLowerCase()) && npTagR1.isPresent() && !npTagR1.get().equalTo(O)) {
      endTokenIndex = findEndOfNPTokenIndex(endTokenIndex + 1, npTags);
    }

    /*
    if (npTagR1.isPresent() && !npTagR1.get().equalTo(O)) {                      // NP
      endTokenIndex = findEndOfNPTokenIndex(endTokenIndex + 1, npTags);
    } else if (posTagR1.isPresent() && (posTagR1.get().equals("IN") || posTagR1.get().equals("TO")
                                            || posTagR1.get().startsWith("RB"))) {

      boolean foundPerson = false;
      if((endTokenIndex + 2) < npTags.size()) {
        final int startCharOffset = st.parse().root().get().nthTerminal(endTokenIndex + 2).span().startCharOffset().asInt();
        for(final Mention m : st.mentions()) {
          if(m.entityType().name().asString().equals("PER")) {
            if ((startCharOffset == m.span().startCharOffset().asInt()) || (startCharOffset == m.head().span().startCharOffset().asInt())) {
              foundPerson = true;
            }
          }
        }
      }

      if(!wR1.get().equals("that") && !(wR1.get().equals("in") && foundPerson)) {  // if on right is "in PER" or "that", do not expand right
        if (npTagR2.isPresent() && !npTagR2.get().equalTo(O)) {
          endTokenIndex = findEndOfNPTokenIndex(endTokenIndex + 2, npTags);     // IN/TO/RB NP
        } else if (posTagR2.isPresent() && posTagR2.get().startsWith("VB") && !wR2.get()
            .equals("be")) {
          if (npTagR3.isPresent() && !npTagR3.get().equalTo(O)) {
            endTokenIndex = findEndOfNPTokenIndex(endTokenIndex + 3, npTags); // IN/TO/RB VB NP
          } else {
            endTokenIndex = endTokenIndex + 2;                                // IN/TO/RB VB
          }
        } else if (posTagR2.isPresent() && posTagR2.get().startsWith("RB") && npTagR3.isPresent()
            && !npTagR3.get().equalTo(O)) {
          endTokenIndex = findEndOfNPTokenIndex(endTokenIndex + 3, npTags);     // IN/TO/RB RB NP
        }
      }
    }

    boolean block = false;
    boolean hasTypedEvent = false;
    for (int i = (endTokenIndexCopy + 1); i <= endTokenIndex; i++) {
      if (semanticPhraseBlockerWords.contains(
          st.tokenSequence().token(i).tokenizedText().utf16CodeUnits().toString().toLowerCase())) {
        block = true;
      }
      if (numberOfTypedEventForEachToken.get(i).intValue() > 0) {
        hasTypedEvent = true;
      }
    }
    if (block && hasTypedEvent) {
      endTokenIndex = endTokenIndexCopy;
    }

    endTokenIndexCopy = endTokenIndex;
    if ((endTokenIndex + 2) < npTags.size()) {
      final String nextWord =
          st.tokenSequence().token(endTokenIndex + 1).tokenizedText().utf16CodeUnits().toString();
      if ((nextWord.equals("of") || nextWord.equals("to")) && !npTags.get(endTokenIndex + 2)
          .equalTo(O)) {
        endTokenIndex = findEndOfNPTokenIndex(endTokenIndex + 2, npTags);
      }
    }

    block = false;
    hasTypedEvent = false;
    for (int i = (endTokenIndexCopy + 1); i <= endTokenIndex; i++) {
      if (semanticPhraseBlockerWords.contains(
          st.tokenSequence().token(i).tokenizedText().utf16CodeUnits().toString().toLowerCase())) {
        block = true;
      }
      if (numberOfTypedEventForEachToken.get(i).intValue() > 0) {
        hasTypedEvent = true;
      }
    }
    if (block && hasTypedEvent) {
      endTokenIndex = endTokenIndexCopy;
    }
    */

    return em.modifiedCopyBuilder().setSemanticPhraseStart(startTokenIndex)
        .setSemanticPhraseEnd(endTokenIndex).build();
    //return em.modifiedCopyBuilder().setContextWindow(startTokenIndex + "-" + endTokenIndex).build();
  }

  // +2
  public static ImmutableList<EventMention> addAnchorContextWindowToEventMentions(
      final ImmutableList<EventMention> eventMentions, final SentenceNPs sentenceNPs,
      final SentenceTheory st, final List<Integer> numberOfTypedEventForEachToken,
      final ImmutableList<WordAndPOS> wordPos, final ImmutableSet<String> lightVerbs) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();
    for (final EventMention em : eventMentions) {
      ret.add(addAnchorContextWindow(em, st, sentenceNPs, numberOfTypedEventForEachToken, wordPos, lightVerbs));
    }
    return ret.build();
  }

  // +1
//    public static DocTheory promoteAnchorsToSpans(final DocTheory dt, final SentenceNPs sentenceNPs) {
//        final DocTheory.Builder docBuilder = dt.modifiedCopyBuilder();
//        docBuilder.events(Events.absent());
//
//        for (int i = 0; i < dt.numSentences(); i++) {
//            final SentenceTheory st = dt.sentenceTheory(i);
//
//            final ImmutableList.Builder<EventMention> allEventMentionsBuilder = ImmutableList.builder();
//            for(final EventMention em : st.eventMentions()) {
//                final int emStart = em.anchorNode().span().startCharOffset().asInt();
//                final int emEnd = em.anchorNode().span().endCharOffset().asInt();
//                final String eventType = em.type().asString();
//
//                final TokenSequence.Span anchorContextSpan = findAnchorContextSpan(em.anchorNode(), st, sentenceNPs);
//                em.setAnchorContextSpan(anchorContextSpan);
//                allEventMentionsBuilder.add(em);
//
//                final int startIndex = em.anchorNode().span().startIndex();
//                final int endIndex = em.anchorNode().span().endIndex();
//                StringBuffer s = new StringBuffer("");
//                for(int j=(startIndex-3); j<=(endIndex+3); j++) {
//                    if(j>=0 && j<st.tokenSequence().size()) {
//                        if(s.length() > 0) {
//                            s.append(" ");
//                        }
//                        if(j==startIndex) {
//                            s.append("<");
//                        }
//                        s.append(st.tokenSequence().token(j).span().tokenizedText().utf16CodeUnits().toString() + "/" + sentenceNPs.toMap().get(st.sentenceNumber()).npChunks().get(j).toString() + "/" + st.parse().root().get().nthTerminal(j).parent().get().tag().toString());
//                        if(j==endIndex) {
//                            s.append(">");
//                        }
//                    }
//                }
//
//                System.out.println("ANCHOR-EXPANSION-NP\t" + em.type().asString() + "\t|||" + em.anchorNode().span().tokenizedText().utf16CodeUnits().toString() + "\t|||" + em.anchorContextSpan().tokenizedText().utf16CodeUnits().toString() + "\t|||" + s.toString());
////                final Optional<SynNode> anchorNP = findNPforEventTriggers(em.anchorNode(), st);
////                if(anchorNP.isPresent()) {
////                    final String anchorText = em.anchorNode().span().tokenizedText().utf16CodeUnits().toString();
////                    final String anchorNPText = anchorNP.get().span().tokenizedText().utf16CodeUnits().toString();
////                    if(anchorNPText.length() > anchorText.length()) {
////                        System.out.println(
////                            "ANCHOR-EXPANSION-MENTION\t" + em.anchorNode().span().tokenizedText()
////                                .utf16CodeUnits().toString() + "\t" + anchorNP.get().span()
////                                .tokenizedText().utf16CodeUnits().toString() + "\t" + st.span()
////                                .tokenizedText().utf16CodeUnits().toString() + "\t" + em.type()
////                                .asString());
////                    }
////                    EventMention newEM = em.modifiedCopyBuilder().setAnchorNode(anchorNP.get()).build();
////                    allEventMentionsBuilder.add(newEM);
////                } else {
////                    allEventMentionsBuilder.add(em);
////                }
//            }
//
//            final SentenceTheory.Builder sentBuilder = st.modifiedCopyBuilder();
//            sentBuilder.eventMentions(new EventMentions.Builder().eventMentions(allEventMentionsBuilder.build()).build());
//            docBuilder.replacePrimarySentenceTheory(st, sentBuilder.build());
//        }
//
//        return docBuilder.build();
//    }


  // +2
  // Some (eventType, eventRole) event-arguments can only take on certain entity types
  public static EventMention pruneArgumentByEventTypeRoleEntityType(final EventMention em,
      final OntologyHierarchy ontologyHierarchy) {
    final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();

    for (final EventMention.Argument arg : em.arguments()) {
      final Optional<String> entityType = EventMentionUtils.getEntityTypeOfEventArgument(arg);
      if (entityType.isPresent()) {
        if (ontologyHierarchy.satisfyEventTypeRoleEntityTypeConstraints(em.type().asString(),
            arg.role().asString(), entityType.get())) {
          newArgsBuilder.add(arg);
        }
      }
    }

    return EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build());
  }

  // +2
  // Some eventRole can only take on certain entity types
  public static ImmutableList<EventMention> pruneEventMentionArgumentsUsingEntityTypeConstraint(
      final List<EventMention> ems) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();
    for (final EventMention em : ems) {
      ret.add(EventConsolidator.pruneEventArgumentUsingEntityTypeConstraint(em));
    }
    return ret.build();
  }

  // +2
  // Some eventRole can only take on certain entity types
  public static EventMention pruneEventArgumentUsingEntityTypeConstraint(final EventMention em) {
    Set<String> allowedActorEntityTypes =
        Sets.newHashSet(EntityType.PER.toString(), EntityType.ORG.toString(),
            EntityType.GPE.toString(), "REFUGEE");
    Set<String> allowedLocationEntityTypes =
        Sets.newHashSet(EntityType.GPE.toString(), EntityType.LOC.toString(),
            EntityType.FAC.toString());
    Set<String> disallowedArtifactEntityTypes =
        Sets.newHashSet(EntityType.PER.toString(), EntityType.ORG.toString(),
            EntityType.GPE.toString(), EntityType.LOC.toString(), EntityType.FAC.toString());
    Set<String> allowedTimeEntityTypes = Sets.newHashSet("TIMEX2");
    final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();

    for (final EventMention.Argument arg : em.arguments()) {
      final String role = arg.role().asString().toLowerCase();
      final Optional<String> entityType = EventMentionUtils.getEntityTypeOfEventArgument(arg);
      if (!entityType.isPresent()) {
        System.out.println(
            "Event argument [" + arg.span().text().utf16CodeUnits().toString() + "] with role "
                + role + " is not a EntityMention nor ValueMention!");
        System.exit(1);
      }

      if (role.equals(EventRoleConstants.HAS_ACTOR) && allowedActorEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_ACTIVE_ACTOR) && allowedActorEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_AFFECTED_ACTOR) && allowedActorEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_LOCATION) && allowedLocationEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_ORIGIN_LOCATION) && allowedLocationEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_DESTINATION_LOCATION)
          && allowedLocationEntityTypes.contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_INTERMEDIATE_LOCATION)
          && allowedLocationEntityTypes.contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_ARTIFACT) && !disallowedArtifactEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_TIME) && allowedTimeEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_START_TIME) && allowedTimeEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_END_TIME) && allowedTimeEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else if (role.equals(EventRoleConstants.HAS_DURATION) && allowedTimeEntityTypes
          .contains(entityType.get())) {
        newArgsBuilder.add(arg);
      } else {
        System.out.println(
            "WARNING pruneEventArgumentUsingEntityTypeConstraint: discarding role=" + role
                + " entityType=" + entityType.get());
      }
    }
    return EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build());
  }

  // +2
  public static ImmutableList<EventMention.EventType> aggregateEventTypes(
      final ImmutableList<EventMention> mentions) {
    final ImmutableList.Builder<EventMention.EventType> ret = ImmutableList.builder();

    Map<String, Double> scores = Maps.newHashMap(); // stores the max score for each event type
    for (final EventMention em : mentions) {
      for(final EventMention.EventType et : em.eventTypes()) {
        if (!scores.containsKey(et.eventType().asString())) {
          scores.put(et.eventType().asString(), et.score());
        } else {
          final double currentScore = scores.get(et.eventType().asString());
          if (et.score() > currentScore) {
            scores.put(et.eventType().asString(), et.score());
          }
        }
      }
    }

    // is there a typed event?
    boolean hasTyped = false;
    for (final String type : scores.keySet()) {
      if (!type.equals(EventTypeConstants.EVENT) && !type.contains("/Event#Event")) {
        hasTyped = true;
        break;
      }
    }

    for (final String type : scores.keySet()) {
      if (hasTyped) {   // if there is at least 1 valid event_type, then we do not output Generic 'Event' in <EventMentionType>
        if (!type.equals(EventTypeConstants.EVENT)) {
          ret.add(EventMention.EventType.from(Symbol.from(type), scores.get(type), Optional.absent(), Optional.absent()));
        }
      } else {
        ret.add(EventMention.EventType.from(Symbol.from(type), scores.get(type), Optional.absent(), Optional.absent()));
      }
    }

    return ret.build();
  }

  // +2
  public static ImmutableList<EventMention.EventType> aggregateFactorTypes(
      final ImmutableList<EventMention> mentions) {
    final ImmutableList.Builder<EventMention.EventType> ret = ImmutableList.builder();

    Map<String, Double> scores = Maps.newHashMap(); // stores the max score for each factor type
    for (final EventMention em : mentions) {
      for (final EventMention.EventType factor : em.factorTypes()) {
        if (!scores.containsKey(factor.eventType().asString())) {
          scores.put(factor.eventType().asString(), factor.score());
        } else {
          final double currentScore = scores.get(factor.eventType().asString());
          if (factor.score() > currentScore) {
            scores.put(factor.eventType().asString(), factor.score());
          }
        }
      }
    }

    for (final String type : scores.keySet()) {
      ret.add(EventMention.EventType.from(Symbol.from(type), scores.get(type), Optional.absent(), Optional.absent()));
    }
    return ret.build();
  }

  public static EventMention bestScoringCandidate(final List<EventMention> ems) {
    double bestScore = 0.0;
    int bestEmIndex = 0;

    for(int i=0; i<ems.size(); i++) {
      final EventMention em = ems.get(i);
      if(em.score() > bestScore) {
        bestScore = em.score();
        bestEmIndex = i;
      }
    }

    return ems.get(bestEmIndex);
  }

  // We select the EventMention whose anchorNode is shortest-distance to the covering-SynNode. The covering-SynNode is the SynNode that covers the entire semanticPhrase
  public static EventMention selectCanonicalEventMention(final ImmutableList<EventMention> mentions,
      final SentenceTheory st, final String offsetString,
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes, final ImmutableSet<String> lightVerbs) {

    final String[] offsets = offsetString.split("-");
    final int offsetStart = new Integer(offsets[0]).intValue();
    final int offsetEnd = new Integer(offsets[1]).intValue();
    final TokenSequence.Span extendedSpan =
        (offsetEnd - offsetStart) > 0 ? st.tokenSequence().token(offsetStart).span()
            .extendRight(offsetEnd - offsetStart) : st.tokenSequence().token(offsetStart).span();

    final ImmutableList<WordAndPOS> wordPos = EventMentionUtils.getWordPosOfEachToken(st);

    final String phrase = extendedSpan.tokenizedText().utf16CodeUnits().toString();

    List<EventMention> candidates = Lists.newArrayList();

    // if the word before the rightmost preposition is not a light verb, return that
    for(int i=offsetEnd; i>=offsetStart; i--) {   // search for rightmost preposition
      if(wordPos.get(i).POS().asString().equals("IN")) {
        if(i > offsetStart) {
          final int wordIndexBeforePreposition = i-1;
          //final String w = wordPos.get(wordIndexBeforePreposition).word().asString();

          if(!lightVerbs.contains(wordPos.get(wordIndexBeforePreposition).word().asString().toLowerCase())) {
            for (final EventMention em : mentions) {
              if (em.anchorNode().head().span().startIndex() == wordIndexBeforePreposition) {
                candidates.add(em);
              }
            }
          }

          if(candidates.size() > 0) {
            return bestScoringCandidate(candidates);
          } else {
            break;
          }
        }
      }
    }
    candidates.clear();

    // return the first VERB that is not light verb
    for(int i=offsetStart; i<=offsetEnd; i++) {
      if(wordPos.get(i).POS().asString().startsWith("VB") && !lightVerbs.contains(wordPos.get(i).word().asString().toLowerCase())) {
        for(final EventMention em : mentions) {
          if(em.anchorNode().head().span().startIndex() == i) {
            candidates.add(em);
          }
        }
        if(candidates.size() > 0) {
          return bestScoringCandidate(candidates);
        }
      }
    }
    candidates.clear();

    // return the last NOUN that is not light verb
    for(int i=offsetEnd; i>=offsetStart; i--) {
      if(wordPos.get(i).POS().asString().startsWith("NN") && !wordPos.get(i).POS().asString().startsWith("NNP")) {
        for(final EventMention em : mentions) {
          if(em.anchorNode().head().span().startIndex() == i) {
            candidates.add(em);
          }
        }
        if(candidates.size() > 0) {
          return bestScoringCandidate(candidates);
        }
      }
    }
    candidates.clear();

    // just return the first anchor according to tokens order
    for(int i=offsetStart; i<=offsetEnd; i++) {
      for (final EventMention em : mentions) {
        if (em.anchorNode().head().span().startIndex() == i) {
          candidates.add(em);
        }
      }
      if(candidates.size() > 0) {
        return bestScoringCandidate(candidates);
      }
    }

    /*
    List<String> outlines = Lists.newArrayList();
    outlines.add("selectCanonicalEventMention: " + phrase);
    for(final EventMention em : mentions) {
      final String anchorText = em.anchorNode().span().tokenizedText().utf16CodeUnits().toString();

      String beforePrepositionMarker = "";
      if(wordIndexBeforePreposition.isPresent() && em.anchorNode().head().span().startIndex() == wordIndexBeforePreposition.get()) {
        beforePrepositionMarker = "*";
      }

      String inEntityMentionMarker = "";
      final int anchorStartCharOffset = em.anchorNode().head().span().startCharOffset().asInt();
      final int anchorEndCharOffset = em.anchorNode().head().span().endCharOffset().asInt();
      for(final Mention m : st.mentions()) {
        final int mStartCharOffset = m.head().span().startCharOffset().asInt();
        final int mEndCharOffset = m.head().span().endCharOffset().asInt();

        if((mStartCharOffset <= anchorStartCharOffset) && (anchorEndCharOffset <= mEndCharOffset)) {
          inEntityMentionMarker = "EM:" + m.entityType().name().asString();
        }
      }

      final String anchorPOS = wordPos.get(em.anchorNode().head().span().endIndex()).POS().asString();

      outlines.add("- " + em.type().asString() + " " + anchorText + ":" + anchorPOS + "  " + beforePrepositionMarker + " " + inEntityMentionMarker);
    }

    if(mentions.size() > 1) {
      for(String line : outlines) {
        System.out.println(line);
      }
    }
    */

    /*
    final Optional<SynNode> extendedSynNode =
        EventMentionUtils.findCoveringSynNode(st, extendedSpan);

    int shortestPathLength = Integer.MAX_VALUE;
    Optional<EventMention> emNearestExtendedSynNode = Optional.absent();
    if (extendedSynNode.isPresent()) {

      for (final EventMention em : mentions) {
        final Optional<Integer> pathLength = PropositionPath
            .getPathLengthBetweenSynNodes(extendedSynNode.get(), em.anchorNode(), synToPathNodes);
        if (pathLength.isPresent()) {
          if (pathLength.get() < shortestPathLength) {
            shortestPathLength = pathLength.get();
            emNearestExtendedSynNode = Optional.of(em);
          }
        }
      }

    }

    if (emNearestExtendedSynNode.isPresent()) {
      return emNearestExtendedSynNode.get();
    } else {
      return mentions.get(0);
    }
    */

    return mentions.get(0);   // shouldn't reach here
  }

  // +2
  // The assumption here is that all the input mentions are from the same sentence. This is true in the way this function is called.
  public static ImmutableList<EventMention> groupEventMentionsBySemanticPhrase(
      final ImmutableList<EventMention> mentions,
      final Map<SynNode, PropositionUtils.PathNode> synToPathNodes, final SentenceTheory st,
      final ImmutableSet<String> lightVerbs) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    Multimap<String, EventMention> offsetToEventMention = HashMultimap.create();
    for (final EventMention em : mentions) {
      final String offsetString =
          em.semanticPhraseStart().get().toString() + "-" + em.semanticPhraseEnd().get().toString();
      offsetToEventMention.put(offsetString, em);
    }

    final ImmutableList<String> offsetStrings = ImmutableList.copyOf(offsetToEventMention.keySet());
    List<IntPair> offsets = Lists.newArrayList();
    for (int i = 0; i < offsetStrings.size(); i++) {
      final String[] tokens = offsetStrings.get(i).split("-");
      offsets
          .add(IntPair.from(new Integer(tokens[0]).intValue(), new Integer(tokens[1]).intValue()));
    }

    List<Integer> indexToCoveringOffset = Lists.newArrayList();
    for (int i = 0; i < offsetStrings.size(); i++) {
      int maxCoveringIndex = i;
      for (int j = 0; j < offsetStrings.size(); j++) {
        if (i != j) {
          if (offsets.get(j).covers(offsets.get(i)) && offsets.get(j)
              .covers(offsets.get(maxCoveringIndex))) {
            maxCoveringIndex = j;
          }
        }
      }
      indexToCoveringOffset.add(maxCoveringIndex);
    }

    Multimap<String, EventMention> offsetToCoveredEventMentions = HashMultimap.create();
    for (int i = 0; i < offsetStrings.size(); i++) {
      final String currentOffsetString = offsetStrings.get(i);
      final String coveringOffsetString = offsetStrings.get(indexToCoveringOffset.get(i));
      offsetToCoveredEventMentions
          .putAll(coveringOffsetString, offsetToEventMention.get(currentOffsetString));
    }

    //Optional<Integer> getPathLengthBetweenSynNodes(final SynNode source, final SynNode target, final Map<SynNode, PropositionUtils.PathNode> synToPathNodes)

    for (final String offsetString : offsetToCoveredEventMentions.keySet()) {
      final String[] offsetTokens = offsetString.split("-");
      final int start = new Integer(offsetTokens[0]).intValue();
      final int end = new Integer(offsetTokens[1]).intValue();

      ImmutableList.Builder<EventMention.Anchor> anchors = ImmutableList.builder();
      Set<TokenSequence.Span> seenAnchorSpans = Sets.newHashSet();
      for (final EventMention em : offsetToCoveredEventMentions.get(offsetString)) {
        if (!seenAnchorSpans.contains(em.anchorNode().span())) {
          anchors.add(EventMention.Anchor.from(em.anchorNode(), em.anchorProposition().orNull()));
          seenAnchorSpans.add(em.anchorNode().span());
        }
      }

      final ImmutableList<EventMention.EventType> eventTypes =
          aggregateEventTypes(ImmutableList.copyOf(offsetToCoveredEventMentions.get(offsetString)));
      final ImmutableList<EventMention.EventType> factorTypes = aggregateFactorTypes(
          ImmutableList.copyOf(offsetToCoveredEventMentions.get(offsetString)));

      final ImmutableList<EventMention.Argument> newArguments = EventMentionUtils
          .aggregateArgumentsFromEventMentions(
              ImmutableList.copyOf(offsetToCoveredEventMentions.get(offsetString)));

      final EventMention canonicalEventMention = selectCanonicalEventMention(
          ImmutableList.copyOf(offsetToCoveredEventMentions.get(offsetString)), st, offsetString,
          synToPathNodes, lightVerbs);

      final ImmutableList<WordAndPOS> wordPos = EventMentionUtils.getWordPosOfEachToken(st);
      
      ret.add(canonicalEventMention.modifiedCopyBuilder()
          .setSemanticPhraseStart(start)
          .setSemanticPhraseEnd(end)
          .setEventTypes(eventTypes)
          .setFactorTypes(factorTypes)
          .setAnchors(anchors.build())
          .setArguments(newArguments)
          .build());
    }

    return ret.build();
  }

  private static boolean currentTokenIsPropositionHead(final SynNode currentNode,
      final SentenceTheory st) {
    for (Proposition proposition : st.propositions().asList()) {
      if (proposition.predHead().isPresent()) {
        String text =
            proposition.predHead().get().head().tokenSpan().originalText().content()
                .utf16CodeUnits();
        String predType = proposition.predType().name().asString();

        if (AddEventMentionByPOSTags.isInValidEventMentionString(text)) {
          continue;
        }

        //if (freq_not_triggers.contains(text.trim().toLowerCase()))
        //    continue;

        if (predType.equalsIgnoreCase("verb") || predType.equalsIgnoreCase("noun")) {
          final SynNode predHeadNode = proposition.predHead().get().head();
          final String headPOS = predHeadNode.headPOS().asString();
          final String headText =
              predHeadNode.tokenSpan().originalText().content().utf16CodeUnits();

          // skip anything that's not verb or noun
          if (!headPOS.startsWith("N") && !headPOS.startsWith("V")) {
            continue;
          }

          // skip proper nouns
          if (headPOS.startsWith("NNP")) {
            continue;
          }

          if (predHeadNode.span().equals(currentNode.span())) {
            return true;
          }
        }
      }
    }
    return false;
  }

  private static boolean satisfyWordAndPosPatterns(final ImmutableList<WordAndPOS> wordPos,
      final int startIndex, final int endIndex) {
    //Set<String> blackWords = Sets.newHashSet("before", "after", "while", "because", "despite", "but", "across", "following", "along", "within", "since", "between", "upon", "caused", "cause", "when", "where");

    if (startIndex >= endIndex) {
      return false;
    }

    if (wordPos.get(startIndex + 1).word().asString().toLowerCase().equals("and")) {
      return false;
    }

    for (int i = (startIndex + 1); i <= endIndex; i++) {
      if (wordPos.get(i).word().asString().toLowerCase().equals("and")) {
        final int j = i + 1;
        if ((j <= endIndex) && wordPos.get(j).POS().asString().startsWith("VB")) {
          return false;
        }
      }
      if (wordPos.get(i).word().asString().toLowerCase().equals("due")) {
        final int j = i + 1;
        if ((j <= endIndex) && wordPos.get(j).word().asString().toLowerCase().equals("to")) {
          return false;
        }
      }
    }

    for (int i = (startIndex + 1); i <= endIndex; i++) {
      final String w = wordPos.get(i).word().asString().toLowerCase();
      if (EventConsolidator.semanticPhraseBlockerWords.contains(w)) {
        return false;
      }
    }

    return true;
  }

  // +2
  public static ImmutableList<EventMention> addLightVerbs(final ImmutableSet<String> lightVerbs,
      final ImmutableList<EventMention> allEventMentions, final SentenceTheory st,
      final String docid, final SentenceNPs sentenceNPs) {
    Set<String> blackWords =
        Sets.newHashSet("abandon", "aid", "arrived", "buy", "collaboration", "contact",
            "contrast", "coordination", "cropping", "deployed", "displacement", "education",
            "emergency", "fall", "fighting", "income", "interventions", "interviewed", "issued",
            "leaving", "left", "living", "located", "lost", "move", "planted", "play",
            "prepared", "presented", "produced", "production", "purchase", "reflected",
            "released", "request", "required", "requires", "require", "respond", "response",
            "responding", "restricted", "resumed", "said", "sale", "sales", "sanitation", "saw",
            "say", "sell", "services", "signed", "sold", "stood", "stop", "strategies",
            "suspended", "taken", "take", "taking", "targeted", "targeting", "think", "took",
            "traded", "trade", "trained", "transported", "treated", "treatment", "vaccinated",
            "watch", "work", "glimpse", "listen", "love", "originate", "overhear", "scramble");

    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    final ImmutableList<WordAndPOS> wordPos = EventMentionUtils.getWordPosOfEachToken(st);
    final ImmutableList<SynNode> synnodes = EventMentionUtils.getSynNodeOfEachToken(st);

    List<Integer> numberOfTypedEventForEachToken = Lists.newArrayList();
    for (final SynNode node : synnodes) {
      numberOfTypedEventForEachToken.add(new Integer(
          EventMentionUtils.findTypedEventMentionUsingSynNode(allEventMentions, node).size()));
    }

    //List<EventMention> genericEventsToRemove = Lists.newArrayList();    // we made new events based on these light-verbs, so we need to remove Generic events

    final ImmutableList<EventMention> eventMentions = EventConsolidator
        .addAnchorContextWindowToEventMentions(allEventMentions, sentenceNPs, st,
            numberOfTypedEventForEachToken, wordPos, lightVerbs);

    for (final EventMention em : eventMentions) {
      if (!em.type().asString().equals(EventTypeConstants.EVENT)) {
        ret.add(em);
        continue;
      }

      if (!currentTokenIsPropositionHead(em.anchorNode().head(), st)) {
        ret.add(em);
        continue;
      }

      final String anchorHeadWord = em.anchorNode().headWord().asString().toLowerCase();
      if (!lightVerbs.contains(anchorHeadWord) || blackWords.contains(anchorHeadWord)) {
        ret.add(em);
        continue;
      }

      final int semanticPhraseStart = em.semanticPhraseStart().get().intValue();
      final int semanticPhraseEnd = em.semanticPhraseEnd().get().intValue();
      final String contextString =
          st.tokenSequence().span(semanticPhraseStart, semanticPhraseEnd).tokenizedText()
              .utf16CodeUnits().toString();

      if (!satisfyWordAndPosPatterns(wordPos, semanticPhraseStart,
          em.anchorNode().span().startIndex()) || !satisfyWordAndPosPatterns(wordPos,
          em.anchorNode().span().endIndex(), semanticPhraseEnd)) {
        ret.add(em);
        continue;
      }

      // for prefix, traverse right to left, to find typed EventMention nearest to anchor
      Optional<Integer> prefixDistance = Optional.absent();
      List<EventMention> prefixAdditions = Lists.newArrayList();
      for (int i = em.anchorNode().span().startIndex() - 1; i >= semanticPhraseStart; i--) {
        final ImmutableList<EventMention> typedEventMentions =
            EventMentionUtils.findTypedEventMentionUsingSynNode(eventMentions, synnodes.get(i));
        if (typedEventMentions.size() > 0) {
          prefixDistance = Optional.of(new Integer(em.anchorNode().span().startIndex() - i));

          for (final EventMention typedEm : typedEventMentions) {
            final EventMention newEm = typedEm.modifiedCopyBuilder().setAnchorNode(em.anchorNode())
                .setSemanticPhraseStart(em.semanticPhraseStart().get())
                .setSemanticPhraseEnd(em.semanticPhraseEnd().get()).build();
            prefixAdditions.add(newEm);
          }
          break;
        }
      }

      // for suffix, traverse left to right, to find typed EventMention nearest to anchor
      Optional<Integer> suffixDistance = Optional.absent();
      List<EventMention> suffixAdditions = Lists.newArrayList();
      for (int i = em.anchorNode().span().endIndex() + 1; i <= semanticPhraseEnd; i++) {
        final ImmutableList<EventMention> typedEventMentions =
            EventMentionUtils.findTypedEventMentionUsingSynNode(eventMentions, synnodes.get(i));
        if (typedEventMentions.size() > 0) {
          suffixDistance = Optional.of(new Integer(i - em.anchorNode().span().endIndex()));

          for (final EventMention typedEm : typedEventMentions) {
            final EventMention newEm = typedEm.modifiedCopyBuilder().setAnchorNode(em.anchorNode())
                .setSemanticPhraseStart(em.semanticPhraseStart().get())
                .setSemanticPhraseEnd(em.semanticPhraseEnd().get()).build();
            suffixAdditions.add(newEm);
          }
          break;
        }
      }

      if ((prefixAdditions.size() > 0) && (suffixAdditions.size() > 0)) {
        if (prefixDistance.get().intValue() <= suffixDistance.get().intValue()) {
          ret.addAll(prefixAdditions);
          for (final EventMention m : prefixAdditions) {
            System.out.println(
                "LIGHT-VERBS:\t" + docid + "\t" + m.type().asString() + "\t" + m.anchorNode().span()
                    .tokenizedText().utf16CodeUnits().toLowerCase() + "\t" + contextString);
          }
        } else {
          ret.addAll(suffixAdditions);
          for (final EventMention m : suffixAdditions) {
            System.out.println(
                "LIGHT-VERBS:\t" + docid + "\t" + m.type().asString() + "\t" + m.anchorNode().span()
                    .tokenizedText().utf16CodeUnits().toLowerCase() + "\t" + contextString);
          }
        }
      } else if (prefixAdditions.size() > 0) {
        ret.addAll(prefixAdditions);
        for (final EventMention m : prefixAdditions) {
          System.out.println(
              "LIGHT-VERBS:\t" + docid + "\t" + m.type().asString() + "\t" + m.anchorNode().span()
                  .tokenizedText().utf16CodeUnits().toLowerCase() + "\t" + contextString);
        }
      } else if (suffixAdditions.size() > 0) {
        ret.addAll(suffixAdditions);
        for (final EventMention m : suffixAdditions) {
          System.out.println(
              "LIGHT-VERBS:\t" + docid + "\t" + m.type().asString() + "\t" + m.anchorNode().span()
                  .tokenizedText().utf16CodeUnits().toLowerCase() + "\t" + contextString);
        }
      } else {
        ret.add(em);
      }
    }

//        for(int i=0; i<(wordPos.size()-1); i++) {
//            final ImmutableList<EventMention> emsOnLightVerb = EventMentionUtils.findEventMentionUsingSynNode(eventMentions, synnodes.get(i));
//            boolean foundTypedEvent = hasTypedEvent(emsOnLightVerb);
//
//            final String lightWord = wordPos.get(i).word().asString().toLowerCase();
//            if(lightVerbs.contains(lightWord) && !blackWords.contains(lightWord) && !foundTypedEvent && currentTokenIsPropositionHead(synnodes.get(i), st)) {
//                int semanticTokenIndex = i;
//
//                boolean sawComma = false;
//                for(int j=i+1; j<synnodes.size(); j++) {
//                    if(wordPos.get(j).word().asString().equals(",")) {
//                        sawComma = true;
//                    }
//                    final ImmutableList<EventMention> ems = EventMentionUtils.findEventMentionUsingSynNode(eventMentions, synnodes.get(j));
//                    if(hasTypedEvent(ems)) {
//                        semanticTokenIndex = j;
//                        break;
//                    }
//                }
//
//                if((semanticTokenIndex > i) && (semanticTokenIndex - i)<=7 && !sawComma && statisfyWordAndPosPatterns(wordPos, i, semanticTokenIndex)) {
//                    final ImmutableList<EventMention> ems = EventMentionUtils.findEventMentionUsingSynNode(eventMentions, synnodes.get(semanticTokenIndex));
//                    final TokenSequence.Span extendedSpan = synnodes.get(i).span().extendRight(semanticTokenIndex - i);
//                    final Optional<SynNode> extendedSynNode = EventMentionUtils.findCoveringSynNode(st, extendedSpan);
//                    if(extendedSynNode.isPresent()) {
//                        for(final EventMention em : ems) {
//                            if(em.type().asString().equals(EventTypeConstants.EVENT)) {
//                                continue;
//                            }
//
//                            StringBuffer s = new StringBuffer();
//                            for(int k=i; k<=semanticTokenIndex; k++) {
//                                s.append(wordPos.get(k).asWordSlashPOS());
//                                s.append(" ");
//                            }
//                            System.out.println("LIGHT-VERBS: " + docid + " " + em.type().asString() + " " + s.toString());
//                            System.out.println("ANCHOR-EXPANSION-LIGHT\t" + wordPos.get(i).word().asString() + "\t" + extendedSynNode.get().span().tokenizedText().utf16CodeUnits().toString() + "\t" + st.span().tokenizedText().utf16CodeUnits().toString() + "\t" + em.type().asString());
//
//                            final EventMention newEm = em.modifiedCopyBuilder().setAnchorNode(extendedSynNode.get()).build();
//
//                            // before I add this, check that there isn't already an existing event mention with the same span and event-type
//                            boolean isExisting = false;
//                            for(final EventMention m : eventMentions) {
//                                if(m.type().asString().equals(newEm.type().asString()) && m.anchorNode().span().equals(newEm.anchorNode().span())) {
//                                    isExisting = true;
//                                    break;
//                                }
//                            }
//                            if(!isExisting) {
//                                ret.add(newEm);
//                            }
//                        }
//
//                        if(ems.size() > 0) {
//                            for(final EventMention em : emsOnLightVerb) {
//                                if(em.type().asString().equals(EventTypeConstants.EVENT)) {
//                                    genericEventsToRemove.add(em);
//                                }
//                            }
//                        }
//                    }
//                }
//            }
//        }
//
//        int removeCount = 0;
//        for(final EventMention em : eventMentions) {
//            boolean remove = false;
//            for(final EventMention em2 : genericEventsToRemove) {
//                if(em.anchorNode().equals(em2.anchorNode())) {
//                    remove = true;
//                    break;
//                }
//            }
//            if(!remove) {
//                ret.add(em);
//            } else {
//                removeCount += 1;
//            }
//        }
//
//        System.out.println("LIGHT-REMOVE " + removeCount);

    return ret.build();

  }

  // e.g. given "efforts to launch", we could like to attack "efforts" which is semantically light, to the "launch" event mention
  public static ImmutableList<EventMention> attachCorefLightAnchor(final ImmutableSet<String> lightWords, final ImmutableList<EventMention> eventMentions, final SentenceTheory st, final String docid, final SentenceNPs sentenceNPs) {
    if(st.isEmpty()) {
      return eventMentions;
    }

    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    final ImmutableList<WordAndPOS> wordPos = EventMentionUtils.getWordPosOfEachToken(st);
    final ImmutableList<SynNode> synnodes = EventMentionUtils.getSynNodeOfEachToken(st);
    final List<Symbol> npTags = sentenceNPs.toMap().get(st.sentenceNumber()).npChunks();	// BIO

    Map<String, String> emAttachMap = new HashMap<String, String>();
    for(final EventMention em : eventMentions) {
      final String anchorHw = em.anchorNode().headWord().asString().toLowerCase();
      if(!lightWords.contains(anchorHw)) {
        continue;
      }

      // the current anchor is a semantically light word, let's see whether it is in a construction that's viable for attachment
      final int anchorEndTokenIndex = em.anchorNode().span().endToken().index();
      if( ((anchorEndTokenIndex+2) < wordPos.size()) && (wordPos.get(anchorEndTokenIndex+1).POS().asString().equals("IN") || wordPos.get(anchorEndTokenIndex+1).word().asString().toLowerCase().equals("to")) ) {
        int endIndex = anchorEndTokenIndex;	// just initialize to any position before anchorEndTokenIndex+2
        if(wordPos.get(anchorEndTokenIndex+2).POS().asString().startsWith("VB")) {  // verb after preposition
          endIndex = anchorEndTokenIndex + 2;
        } else if(!npTags.get(anchorEndTokenIndex+2).equalTo(O)) {		// noun phrase after preposition
          endIndex = findEndOfNPTokenIndex(anchorEndTokenIndex+2, npTags);
        }

        for(int i=(anchorEndTokenIndex+2); i<=endIndex; i++) {
          final ImmutableList<EventMention> emToAttachTo = EventMentionUtils.findEventMentionUsingSynNode(eventMentions, synnodes.get(i));
          if(emToAttachTo.size() > 0) {

            StringBuilder s = new StringBuilder();
            for(int j=anchorEndTokenIndex; j<=endIndex; j++) {
              s.append(" ");
              s.append(st.tokenSequence().token(j).span().tokenizedText().utf16CodeUnits().toString());
            }
            //System.out.println(docid);
            //System.out.println(st.span().tokenizedText().utf16CodeUnits().toString());
            //System.out.println("attachCorefLightAnchor, joining:" + s.toString());

            for(final EventMention parentEm : emToAttachTo) {
              emAttachMap.put(EventMentionUtils.eventMentionTokenIndicesToString(em), EventMentionUtils.eventMentionTokenIndicesToString(parentEm));
            }
            break;
          }
        }
      }
    }

    // the following will let us know, for each EventMention e, whether there is/are event mention(s) that is attaching to e  
    Set<String> idsInvolvedInAttachment = new HashSet<String>();
    Multimap<String, String> parentToChildren = ArrayListMultimap.create();
    for(Map.Entry<String, String> entry : emAttachMap.entrySet()) {
      String child = entry.getKey();
      String parent = entry.getValue();
      //System.out.println("attachCorefLightAnchor, attaching child=" + child + " to parent=" + parent);
      // in case we get cases like: "ability to increase in launching", you actually want "ability" to attach to "launching"
      while(emAttachMap.containsKey(parent)) {
        parent = emAttachMap.get(parent);
      }
      parentToChildren.put(parent, child);
      idsInvolvedInAttachment.add(child);
      idsInvolvedInAttachment.add(parent); 
    }

    Map<String, EventMention> idToEventMention = new HashMap<String, EventMention>();
    for(final EventMention em : eventMentions) {
      final String emId = EventMentionUtils.eventMentionTokenIndicesToString(em);
      idToEventMention.put(emId, em);
      if(!idsInvolvedInAttachment.contains(emId)) {
        ret.add(em);
      }
    }

    for(final String parentId : parentToChildren.keySet()) {
      List<EventMention.Anchor> anchors = new ArrayList<EventMention.Anchor>();
      anchors.addAll(idToEventMention.get(parentId).anchors());
      //System.out.println("parent anchors size=" + idToEventMention.get(parentId).anchors().size());
      for(final String childId : parentToChildren.get(parentId)) {
        //System.out.println("attachCorefLightAnchor: childId=" + childId + " parentId=" + parentId);
        //final EventMention childEm = idToEventMention.get(childId);
        //if(childEm.anchorProposition().isPresent()) {
        //  anchors.add(EventMention.Anchor.from(childEm.anchorNode(), childEm.anchorProposition().get()));
        //} else {
        //  anchors.add(EventMention.Anchor.from(childEm.anchorNode(), null));
        //}
        //anchors.add(EventMention.Anchor.from(idToEventMention.get(childId).anchorNode());
        anchors.addAll(idToEventMention.get(childId).anchors());
        //System.out.println("child anchors.size=" + idToEventMention.get(childId).anchors().size());
      }
      //for(final EventMention.Anchor anchor : anchors) {
      //  System.out.println("anchor=" + anchor.anchorNode().head().span().tokenizedText().utf16CodeUnits().toString());
      //}
      ret.add(idToEventMention.get(parentId).modifiedCopyBuilder().setAnchors(anchors).build());
    }
  
    return ret.build();
  }


  public static float calibrateEventArgumentScoreUsingMentionType(final EventMention.Argument arg, float argScore) {
    float newArgScore = argScore;

    final Optional<String> mentionType = EventMentionUtils.getMentionType(arg);
    if(mentionType.isPresent()) {
      if(mentionType.get().toLowerCase().equals("name")) { // score unchanged
        newArgScore = newArgScore;
      } else if(mentionType.get().toLowerCase().equals("desc")) {
        newArgScore = newArgScore * 0.75f;
      } else {
        newArgScore = newArgScore * 0.5f;
      } 
    }

    return newArgScore;
  } 

  public static float calibrateEventArgumentScoreUsingAwake(final EventMention.Argument arg, float argScore, final Set<String> offsets) {
    float newArgScore = argScore; 

    if(arg instanceof EventMention.MentionArgument) {
      final EventMention.MentionArgument mentionArg = (EventMention.MentionArgument) arg;
      final Mention mention = mentionArg.mention();
      final int start = mention.tokenSpan().startCharOffset().asInt();
      final int end = mention.tokenSpan().endCharOffset().asInt();
      if(!offsets.contains(Integer.toString(start) + "_" + Integer.toString(end))) {
        newArgScore = newArgScore * 0.75f;
      }
    }

    return newArgScore;
  }

  public static double calibrateEventActorScore(final EventMention.Argument arg, final Set<String> offsets) {
    float argScore = arg.score();
    argScore = EventConsolidator.calibrateEventArgumentScoreUsingMentionType(arg, argScore);
    argScore = EventConsolidator.calibrateEventArgumentScoreUsingAwake(arg, argScore, offsets);
    return argScore;
  }

  public static double calibrateEventLocationScore(final EventMention.Argument arg, final Set<String> offsets) {
    float argScore = arg.score();
    argScore = EventConsolidator.calibrateEventArgumentScoreUsingMentionType(arg, argScore);
    argScore = EventConsolidator.calibrateEventArgumentScoreUsingAwake(arg, argScore, offsets);
    return argScore;
  }

  public static ImmutableList<EventMention> calibrateEventMentionConfidence(final SentenceTheory st) {
    final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

    // first, let's get the offsets of all Awake mentions in this sentence
    Set<String> actorOffsets = new HashSet<String>();
    for(final ActorMention actor : st.actorMentions()) {
      final Mention mention = actor.mention();
      final int start = mention.tokenSpan().startCharOffset().asInt();
      final int end = mention.tokenSpan().endCharOffset().asInt();
      actorOffsets.add(Integer.toString(start) + "_" + Integer.toString(end));
    }
 
    for(final EventMention em : st.eventMentions()) {
      double maxFactorTypeScore = 0;
      double maxEventTypeScore = 0;
      double maxActorScore = 0;
      double maxLocationScore = 0;

      // get max score for factor types
      for (EventMention.EventType eventType : em.factorTypes()) {
        if(eventType.score() > maxFactorTypeScore)
          maxFactorTypeScore = eventType.score();
      }

      // get max score for event types
      for (EventMention.EventType eventType : em.eventTypes()) {
        if(eventType.score() > maxEventTypeScore)
          maxEventTypeScore = eventType.score();
      }

      for(final EventMention.Argument arg : em.arguments()) {
        final String role = arg.role().asString();
        if(role.equals(EventRoleConstants.HAS_ACTOR) || role.equals(EventRoleConstants.HAS_AFFECTED_ACTOR) || role.equals(EventRoleConstants.HAS_ACTIVE_ACTOR)) {
          double score = EventConsolidator.calibrateEventActorScore(arg, actorOffsets);
          if(score > maxActorScore) {
            maxActorScore = score;
          }
        } else if(role.equals(EventRoleConstants.HAS_LOCATION) || role.equals(EventRoleConstants.HAS_ORIGIN_LOCATION) ||
                  role.equals(EventRoleConstants.HAS_DESTINATION_LOCATION) || role.equals(EventRoleConstants.HAS_INTERMEDIATE_LOCATION)) {
          double score = EventConsolidator.calibrateEventLocationScore(arg, actorOffsets);
          if(score > maxLocationScore) {
            maxLocationScore = score;
          }
        }
      }

      // minimal score is 0.4
      // we just sum up the 4 components and normalize them into [0, 0.6]. Final socre is in [0.4, 1]
      double aggregatedScore = (maxFactorTypeScore + maxEventTypeScore + maxActorScore + maxLocationScore)*0.6f/4.0;

      if(EventMentionUtils.eventMentionHasJustGenericEvent(em) || EventMentionUtils.eventMentionHasJustGenericFactor(em)) {
        aggregatedScore = aggregatedScore * 0.5;
      }

      double finalScore = 0.4f + aggregatedScore;
      ret.add(em.modifiedCopyBuilder().setScore(finalScore).build());
    }

    return ret.build();
  } 

  public static double EVENTMENTION_BASED_ON_KEYWORD_SCORE = 0.7;
  public static double KBP_EVENT_SCORE = 0.7;

  private static final Symbol B = Symbol.from("B");
  private static final Symbol I = Symbol.from("I");
  private static final Symbol O = Symbol.from("O");

  public static final ImmutableSet<String> semanticPhraseBlockerWords = ImmutableSet.copyOf(
      Sets.newHashSet("before", "after", "while", "because", "despite", "but", "across",
          "following", "along", "within", "since", "between", "upon", "caused", "cause", "when",
          "where", "and", "or", "to", "lead", "result", "affecting", "affected"));

  public static class IntPair {

    private final int first;
    private final int second;

    private IntPair(final int first, final int second) {
      this.first = first;
      this.second = second;
    }

    public static IntPair from(final int first, final int second) {
      return new IntPair(first, second);
    }

    public int first() {
      return first;
    }

    public int second() {
      return second;
    }

    public boolean covers(final IntPair p) {
      if ((this.first <= p.first()) && (p.second() <= this.second)) {
        return true;
      } else {
        return false;
      }
    }
  }

}

