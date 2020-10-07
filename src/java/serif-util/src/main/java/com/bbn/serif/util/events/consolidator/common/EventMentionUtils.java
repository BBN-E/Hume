package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.nlp.WordAndPOS;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.Mention;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.SynNode;
import com.bbn.serif.theories.TokenSequence;
import com.bbn.serif.theories.ValueMention;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;

import java.util.*;

/**
 * Created by ychan on 4/17/19.
 */
public class EventMentionUtils {

    // +1
    public static String eventString(final EventMention em) {
        String ret = anchorString(em);
        for(String s : argumentStrings(em)) {
            ret += "\n" + " - " + s;
        }
        return ret;
    }

    // +1
    public static String anchorString(final EventMention em) {
        return em.type().asString() + ":" + em.score() + ":(" + em.anchorNode().span().startCharOffset() + "-" + em.anchorNode().span().endCharOffset() + ")=[" + em.anchorNode().span().text() + "]";
    }

    // +1
    public static ImmutableList<String> argumentStrings(final EventMention em) {
        final ImmutableList.Builder<String> ret = ImmutableList.builder();
        for(final EventMention.Argument arg : em.arguments()) {
            final Optional<String> entityType = getEntityTypeOfEventArgument(arg);
            ret.add(arg.role().asString() + ":" + arg.score() + ":(" + arg.span().startCharOffset() + "-" + arg.span().endCharOffset() + ")=[" + arg.span().text() + "] " + entityType.or("NONE"));
        }
        return ret.build();
    }

    // +1
    public static boolean isArgumentInList(final EventMention.Argument argument, final ImmutableList<EventMention.Argument> arguments) {
        final OffsetRange<CharOffset> offset = argument.span().charOffsetRange();
        final Symbol role = argument.role();
        for(final EventMention.Argument arg : arguments) {
            if(arg.span().charOffsetRange().equals(offset)) {
                return true;
            }
        }
        return false;
    }

    // +2
    public static Optional<EventMention> getEventWithCoveringArguments(final EventMention e1, final EventMention e2) {
        final List<EventMention.Argument> arguments1 = e1.arguments();
        final List<EventMention.Argument> arguments2 = e2.arguments();

        if(arguments1.size() > arguments2.size()) {         // check whether arguments2 is covered by arguments1
            boolean covers = true;
            for(final EventMention.Argument arg : arguments2) {
                if(!isArgumentInList(arg, ImmutableList.copyOf(arguments1))) {
                    covers = false;
                    break;
                }
            }
            if(covers) {
                return Optional.of(e1);
            } else {
                return Optional.absent();
            }
        } else if(arguments2.size() > arguments1.size()) {  // check whether arguments1 is covered by arguments2
            boolean covers = true;
            for(final EventMention.Argument arg : arguments1) {
                if(!isArgumentInList(arg, ImmutableList.copyOf(arguments2))) {
                    covers = false;
                    break;
                }
            }
            if(covers) {
                return Optional.of(e2);
            } else {
                return Optional.absent();
            }
        } else if(arguments1.size() == arguments2.size()) {
            return Optional.absent();
            /*
            // do their arguments cover the same span?
            boolean covers = true;
            for(final EventMention.Argument arg : arguments1) {
                if(!isArgumentInList(arg, arguments2)) {
                    covers = false;
                    break;
                }
            }
            if(covers) {
                // aggregate their posterior probabilities
                double score1 = e1.score();
                for(final EventMention.Argument arg : e1.arguments()) {
                    score1 += arg.score();
                }
                double score2 = e2.score();
                for(final EventMention.Argument arg : e2.arguments()) {
                    score2 += arg.score();
                }
                if(score1 >= score2) {
                    return Optional.of(e1);
                } else {
                    return Optional.of(e2);
                }
            } else {
                return Optional.absent();
            }
            */
        } else {
            return Optional.absent();
        }
    }

    // +1
    public static EventMention getEventWithMoreArguments(final EventMention em1, final EventMention em2) {
        if(em1.arguments().size() >= em2.arguments().size()) {
            return em1;
        } else {
            return em2;
        }
    }

    // +2
    public static EventMention newEventMentionWithArguments(final EventMention target_em, final List<EventMention.Argument> newArgs) {
        return target_em.modifiedCopyBuilder().setArguments(newArgs).build();
        /*
        if (target_em.pattern().isPresent()) {
            EventMention em = EventMention
                .builder(target_em.type())
                .setAnchorNode(target_em.anchorNode())
                .setAnchorPropFromNode(st)
                .setScore(target_em.score())
                .setPatternID(target_em.pattern().get())
                .setArguments(newArgs)
                .build();
            return em;
        } else {
            EventMention em = EventMention
                .builder(target_em.type())
                .setAnchorNode(target_em.anchorNode())
                .setAnchorPropFromNode(st)
                .setScore(target_em.score())
                .setArguments(newArgs)
                .build();
            return em;
        }
        */
    }

    // +1
    public static boolean hasRole(final ImmutableList<EventMention.Argument> args, final String role) {
        for(final EventMention.Argument arg : args) {
            if(arg.role().asString().compareTo(role)==0) {
                return true;
            }
        }
        return false;
    }

    // +1
    // TODO : note that the ids does not include arg-role
    public static ImmutableList<EventMention.Argument> unionArguments(final ImmutableList<EventMention.Argument> args1, final ImmutableList<EventMention.Argument> args2) {
        Set<String> seenIds = Sets.newHashSet();
        final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();

        for(final EventMention.Argument arg : args1) {
            final String id = arg.span().startCharOffset().asInt() + ":" + arg.span().endCharOffset().asInt();
            seenIds.add(id);
            newArgsBuilder.add(arg);
        }

        for(final EventMention.Argument arg : args2) {
            final String id = arg.span().startCharOffset().asInt() + ":" + arg.span().endCharOffset().asInt();
            if(!seenIds.contains(id)) {
                seenIds.add(id);
                newArgsBuilder.add(arg);
            }
        }

        return newArgsBuilder.build();
    }

    // +2
    public static ImmutableList<EventMention.Argument> aggregateArgumentsFromEventMentions(final ImmutableList<EventMention> eventMentions) {
        Set<String> seenIds = Sets.newHashSet();
        final ImmutableList.Builder<EventMention.Argument> newArgs = ImmutableList.builder();

        final ImmutableList.Builder<EventMention.Argument> currentArgs = ImmutableList.builder();
        for(final EventMention em : eventMentions) {
            currentArgs.addAll(em.arguments());
        }

        for(final EventMention.Argument arg : currentArgs.build()) {
            final String id = arg.role().asString() + ":" + arg.span().startCharOffset().asInt() + ":" + arg.span().endCharOffset().asInt();
            if(!seenIds.contains(id)) {
                seenIds.add(id);
                if(arg instanceof EventMention.ValueMentionArgument) {
                    EventMention.Argument newArg = EventMention.ValueMentionArgument.from(arg.role(), ((EventMention.ValueMentionArgument) arg).valueMention(), arg.score());
                    newArgs.add(newArg);
                } else if(arg instanceof EventMention.MentionArgument) {
                    EventMention.Argument newArg = EventMention.MentionArgument.from(arg.role(), ((EventMention.MentionArgument) arg).mention(), arg.score());
                    newArgs.add(newArg);
                }
            }
        }

        return newArgs.build();
    }

    // +2
    public static EventMention mergeEventMentions(final EventMention target_em, final EventMention em2, final SentenceTheory st) {
        final ImmutableList<EventMention.Argument> newArgs = aggregateArgumentsFromEventMentions(
            ImmutableList.of(target_em, em2));
        return newEventMentionWithArguments(target_em, newArgs);
    }

    // +2
    public static Optional<String> getEntityTypeOfEventArgument(final EventMention.Argument arg) {
        if(arg instanceof EventMention.MentionArgument) {
            final EventMention.MentionArgument m = (EventMention.MentionArgument) arg;
            return Optional.of(m.mention().entityType().toString());
        } else if(arg instanceof EventMention.ValueMentionArgument) {
            final EventMention.ValueMentionArgument m = (EventMention.ValueMentionArgument) arg;
            return Optional.of(m.valueMention().type().asString());
        } else {
            return Optional.absent();
        }
    }

//    public static boolean acceptEventMentionBasedOnArguments(final EventMention em) {
//        final Set<String> interventionTypes = Sets.newHashSet("SexualViolenceManagement", "VectorControl",
//            "CapacityBuildingHumanRights", "ProvideHygieneTool", "ProvideFarmingTool",
//            "ProvideDeliveryKit", "ProvideLivestockFeed", "ProvideVeterinaryService",
//            "ProvideFishingTool", "ProvideStationary");
//        final String et = em.type().asString();
//        if(interventionTypes.contains(et)) {
//            boolean found = false;
//            for(final EventMention.Argument arg : em.arguments()) {
//                if(arg.role().asString().equals("has_artifact")) {
//                    found = true;
//                    break;
//                }
//            }
//            return found;
//        } else {
//            return true;
//        }
//    }

    // +2
    public static boolean entityTypeInSentence(final SentenceTheory st, final String entityType) {
        for(final Mention m : st.mentions()) {
            if(m.entityType().toString().equals(entityType)) {
                return true;
            }
        }
        return false;
    }

    // +2
    public static Optional<String> getInterventionEventTypeBasedOnEntityType(final String entityType) {
        Optional<String> newEventType = Optional.absent();
        if(entityType.equals("FOOD")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_FOOD);
        } else if(entityType.equals("MONEY")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_CASH);
        } else if(entityType.equals("SEED")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_SEED);
        } else if(entityType.equals("HYGIENE_TOOL")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_HYGIENE_TOOL);
        } else if(entityType.equals("LIVESTOCK_FEED")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_LIVESTOCK_FEED);
        } else if(entityType.equals("STATIONARY")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_STATIONARY);
        } else if(entityType.equals("VETERINARY_SERVICE")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_VETERINARY_SERVICE);
        } else if(entityType.equals("DELIVERY_KIT")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_DELIVERY_KIT);
        } else if(entityType.equals("FARMING_TOOL")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_FARMING_TOOL);
        } else if(entityType.equals("FISHING_TOOL")) {
            newEventType = Optional.of(EventTypeConstants.PROVIDE_FISHING_TOOL);
        }
        return newEventType;
    }

    // +2
    public static Optional<EventMention> remapEventMentionBasedOnEntityMentions(final EventMention em, final SentenceTheory st) {

        int anchorIndex = em.anchorNode().head().tokenSpan().endToken().index();

        List<EventMention.Argument> overRidingEventArguments = Lists.newArrayList();
        List<EventMention.EventType> acceptedEventTypes = Lists.newArrayList();

        for(final EventMention.EventType emEt : em.eventTypes()) {
            final String et = emEt.eventType().asString();

            if (et.startsWith(EventTypeConstants.PROVIDE_HUMANITARIAN_RESOURCES)) {
                Set<String> possibleEntityTypes =
                    Sets.newHashSet("FOOD", "MONEY", "SEED", "HYGIENE_TOOL", "LIVESTOCK_FEED",
                        "STATIONARY", "VETERINARY_SERVICE", "DELIVERY_KIT", "FARMING_TOOL",
                        "FISHING_TOOL");

                final ImmutableList<EventMention.Argument> event_arguments = ImmutableList
                    .copyOf(em.argsForRole(Symbol.from(EventRoleConstants.HAS_ARTIFACT)));
                if (event_arguments.size() > 0) {
                    int smallest_distance = 999;
                    Optional<EventMention.Argument> nearestArgument = Optional
                        .absent();    // find the nearest argument of the possibleEntityTypes
                    for (final EventMention.Argument argument : event_arguments) {
                        if (argument instanceof EventMention.MentionArgument) {
                            final String entityType =
                                ((EventMention.MentionArgument) argument).mention().entityType()
                                    .name().asString();
                            if (possibleEntityTypes.contains(entityType)) {
                                int startIndex =
                                    ((EventMention.MentionArgument) argument).mention().head()
                                        .tokenSpan().startToken().index();
                                int endIndex =
                                    ((EventMention.MentionArgument) argument).mention().head()
                                        .tokenSpan().endToken().index();
                                int d = Math.min(Math.abs(anchorIndex - startIndex),
                                    Math.abs(anchorIndex - endIndex));
                                if (d < smallest_distance) {
                                    smallest_distance = d;
                                    nearestArgument = Optional.of(argument);
                                }
                            }

                        }
                    }
                    if (nearestArgument
                        .isPresent()) {   // we will now remap the event-type based on the entity-type of this nearest argument
                        final String entityType =
                            ((EventMention.MentionArgument) nearestArgument.get()).mention()
                                .entityType().name().asString();
                        Optional<String> newEventType =
                            getInterventionEventTypeBasedOnEntityType(entityType);
                        if (newEventType.isPresent()) {
                            acceptedEventTypes.add(EventMention.EventType.from(Symbol.from(newEventType.get()), emEt.score(), Optional.absent(), Optional.absent()));
                        }
                    }
                }

                // If the above does not happen, we now check whether there is an Intervention entity mention within a local window
                int smallest_distance = 999;
                Optional<Mention> nearestMention = Optional.absent();
                for (final Mention mention : st.mentions()) {
                    if (possibleEntityTypes.contains(mention.entityType().name().asString())) {
                        int startIndex = mention.head().tokenSpan().startToken().index();
                        int endIndex = mention.head().tokenSpan().endToken().index();
                        int d = Math.min(Math.abs(anchorIndex - startIndex),
                            Math.abs(anchorIndex - endIndex));
                        if (d <= 5 && d < smallest_distance) {
                            smallest_distance = d;
                            nearestMention = Optional.of(mention);
                        }
                    }
                }
                if (nearestMention
                    .isPresent()) {   // yes, we have an entityMention in the sentence, of the possibleEntityType
                    final String entityType = nearestMention.get().entityType().name().asString();
                    Optional<String> newEventType =
                        getInterventionEventTypeBasedOnEntityType(entityType);
                    if (newEventType.isPresent()) {
                        // we also add this as an argument
                        // TODO : should we add the original arguments also ?
                        EventMention.Argument arg = EventMention.MentionArgument
                            .from(Symbol.from(EventRoleConstants.HAS_ARTIFACT),
                                nearestMention.get(), 1);

                        acceptedEventTypes.add(EventMention.EventType.from(Symbol.from(newEventType.get()), emEt.score(), Optional.absent(), Optional.absent()));
                        overRidingEventArguments.add(arg);
                    }
                }
            } else {
                acceptedEventTypes.add(emEt);
            }
        }

        Optional<EventMention> newEm = EventMentionUtils.reviseEventTypeAsNecessary(em, acceptedEventTypes, em.factorTypes());
        if(newEm.isPresent()) {
            if(overRidingEventArguments.size() > 0) {
                return Optional.of(newEm.get().modifiedCopyBuilder().setArguments(overRidingEventArguments).build());
            } else {
                return newEm;
            }
        } else {
            return Optional.absent();
        }
    }

    // +2
    // ensure that the event mention's event_type attribute is either in the list of <EventMentionType> or <EventMentionFactorType>
    public static Optional<EventMention> reviseEventTypeAsNecessary(final EventMention em, List<EventMention.EventType> eventTypes, List<EventMention.EventType> factorTypes) {
        Optional<String> eventType = Optional.absent();
        double score = 0.0;

        for(final EventMention.EventType et : eventTypes) {
            if(et.eventType().asString().equals(em.type().asString())) {
                eventType = Optional.of(em.type().asString());
                score = em.score();
                break;
            }
        }

        if(!eventType.isPresent()) {
            for(final EventMention.EventType et : factorTypes) {
                if(et.eventType().asString().equals(em.type().asString())) {
                    eventType = Optional.of(em.type().asString());
                    score = em.score();
                    break;
                }
            }
        }

        if(!eventType.isPresent() && eventTypes.size()>0) {
            eventType = Optional.of(eventTypes.get(0).eventType().asString());
            score = eventTypes.get(0).score();
        }

        if(!eventType.isPresent() && factorTypes.size()>0) {
            eventType = Optional.of(factorTypes.get(0).eventType().asString());
            score = factorTypes.get(0).score();
        }

        if(eventType.isPresent()) {
            return Optional.of(em.modifiedCopyBuilder().setType(Symbol.from(eventType.get())).setScore(score).setEventTypes(eventTypes).setFactorTypes(factorTypes).build());
        } else {
            return Optional.absent();
        }
    }

    // +2
    public static Optional<EventMention> acceptEventMentionBasedOnEntityMentions(final EventMention em, final SentenceTheory st) {
        List<EventMention.EventType> acceptedEventTypes = Lists.newArrayList();

        for(final EventMention.EventType et : em.eventTypes()) {
            final String e = et.eventType().asString();

            if (e.equals(EventTypeConstants.ANTI_RETROVIRAL_TREATMENT)) {
                acceptedEventTypes.add(et);
            } else if (e.equals(EventTypeConstants.THERAPEUTIC_FEEDING_OR_TREATING)) {
                acceptedEventTypes.add(et);
            } else if (e.equals(EventTypeConstants.SEXUAL_VIOLENCE_MANAGEMENT)) {
                if (entityTypeInSentence(st, "SEXUAL_VIOLENCE")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.VECTOR_CONTROL)) {
                if (entityTypeInSentence(st, "INSECT_CONTROL")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.CAPACITY_BUILDING_HUMAN_RIGHTS)) {
                if (entityTypeInSentence(st, "HUMAN_RIGHT")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.CHILD_FRIENDLY_LEARNING_SPACES)) {
                if (entityTypeInSentence(st, "PER")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_HYGIENE_TOOL)) {
                if (entityTypeInSentence(st, "HYGIENE_TOOL")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_FARMING_TOOL)) {
                if (entityTypeInSentence(st, "FARMING_TOOL")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_DELIVERY_KIT)) {
                if (entityTypeInSentence(st, "DELIVERY_KIT")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_LIVESTOCK_FEED)) {
                if (entityTypeInSentence(st, "LIVESTOCK_FEED")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_VETERINARY_SERVICE)) {
                if (entityTypeInSentence(st, "VETERINARY_SERVICE")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_FISHING_TOOL)) {
                if (entityTypeInSentence(st, "FISHING_TOOL")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_STATIONARY)) {
                if (entityTypeInSentence(st, "STATIONARY")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_CASH)) {
                if (entityTypeInSentence(st, "MONEY")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_FOOD)) {
                if (entityTypeInSentence(st, "FOOD")) {
                    acceptedEventTypes.add(et);
                }
            } else if (e.equals(EventTypeConstants.PROVIDE_SEED)) {
                if (entityTypeInSentence(st, "SEED")) {
                    acceptedEventTypes.add(et);
                }
            } else {
                acceptedEventTypes.add(et);
            }
        }

        return reviseEventTypeAsNecessary(em, acceptedEventTypes, em.factorTypes());
    }

    // +2
    // Note that the valueMention passed in MUST be has_time suitable
    public static ImmutableList<EventMention> heuristicallyAddTimeArgument(final ValueMention valueMention, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        int startIndex = valueMention.tokenSpan().startToken().index();
        int endIndex = valueMention.tokenSpan().endToken().index();

        for(final EventMention em : ems) {
            if ((em.argsForRole(Symbol.from(EventRoleConstants.HAS_TIME)).size() == 0)
                && (em.argsForRole(Symbol.from(EventRoleConstants.HAS_START_TIME)).size() == 0)
                && (em.argsForRole(Symbol.from(EventRoleConstants.HAS_END_TIME)).size() == 0)) {

                // we check that the distance between event's semantic-phrase and time-mention is <= 5 tokens and there is no quotes nor comma in between
                int anchorStart = 0;
                int anchorEnd = 0;
                if(em.semanticPhraseStart().isPresent() && em.semanticPhraseEnd().isPresent()) {
                    anchorStart = em.semanticPhraseStart().get().intValue();
                    anchorEnd = em.semanticPhraseEnd().get().intValue();
                } else {
                    anchorStart = em.anchorNode().head().tokenSpan().endToken().index();
                    anchorEnd = em.anchorNode().head().tokenSpan().endToken().index();
                }

                String text = "";
                int d = Math.min(Math.abs(anchorStart - endIndex), Math.abs(startIndex - anchorEnd));
                if(anchorStart >= endIndex) {
                    text = st.tokenSequence().span(endIndex, anchorStart).tokenizedText().utf16CodeUnits().toString();

                } else if(startIndex >= anchorEnd) {
                    text = st.tokenSequence().span(anchorEnd, startIndex).tokenizedText().utf16CodeUnits().toString();
                }
                if((d <= 5) && text.indexOf(",")==-1 && text.indexOf("\"")==-1) {
                    final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
                    newArgsBuilder.addAll(em.arguments());
                    EventMention.Argument arg = EventMention.ValueMentionArgument.from(Symbol.from(EventRoleConstants.HAS_TIME), valueMention, EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                    newArgsBuilder.add(arg);
                    ret.add(EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build()));
                } else {
                    ret.add(em);
                }
            } else {
                ret.add(em);
            }
        }
        return ret.build();
    }

    /*
    // +2
    // Note that 'mention' MUST be a has_location like mention
    public static ImmutableList<EventMention> heuristicallyAddPlaceArgument(final Mention mention, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        for(final EventMention em : ems) {
            int anchorIndex = em.anchorNode().head().tokenSpan().endToken().index();
            int startIndex = mention.head().tokenSpan().startToken().index();
            int endIndex = mention.head().tokenSpan().endToken().index();
            int d = Math.min(Math.abs(anchorIndex - startIndex), Math.abs(anchorIndex - endIndex));

            if ((em.argsForRole(Symbol.from(EventRoleConstants.HAS_LOCATION)).size() == 0)
                && (em.argsForRole(Symbol.from(EventRoleConstants.HAS_ORIGIN_LOCATION)).size() == 0)
                && (em.argsForRole(Symbol.from(EventRoleConstants.HAS_DESTINATION_LOCATION)).size() == 0) && (d <= 5)) {
                final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
                newArgsBuilder.addAll(em.arguments());
                EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_LOCATION), mention, EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                newArgsBuilder.add(arg);
                ret.add(EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build()));
            } else {
                ret.add(em);
            }
        }
        return ret.build();
    }
    */

    public static ImmutableList<EventMention> heuristicallyAddPlaceArgument(final ImmutableList<Mention> mentions, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        for(final EventMention em : ems) {
            if (em.argsForRole(Symbol.from(EventRoleConstants.HAS_LOCATION)).size() == 0
                && em.argsForRole(Symbol.from(EventRoleConstants.HAS_ORIGIN_LOCATION)).size() == 0
                && em.argsForRole(Symbol.from(EventRoleConstants.HAS_DESTINATION_LOCATION)).size() == 0) {

                final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
                newArgsBuilder.addAll(em.arguments());

                Optional<Mention> bestMention = Optional.absent();

                if(mentions.size() > 1) {
                    // is there a mention that is near the trigger?
                    int anchorIndex = em.anchorNode().head().tokenSpan().endToken().index();

                    int shortestDistance = 99;
                    for(final Mention m : mentions) {
                        int startIndex = m.head().tokenSpan().startToken().index();
                        int endIndex = m.head().tokenSpan().endToken().index();

                        int d = Math.min(Math.abs(anchorIndex - startIndex), Math.abs(anchorIndex - endIndex));
                        if(d <= 10) {
                            if(d < shortestDistance) {
                                shortestDistance = d;
                                bestMention = Optional.of(m);
                            }
                        }
                    }
                } else if(mentions.size() == 1) {
                    bestMention = Optional.of(mentions.get(0));
                }

                if(bestMention.isPresent()) {
                    EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_LOCATION), bestMention.get(), EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                    newArgsBuilder.add(arg);
                }
                ret.add(EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build()));
            } else {
                ret.add(em);
            }
        }
        return ret.build();
    }

  public static EventMention heuristicallyAddThemeArgument(
      final ImmutableList<Mention> themeCandidates,
      final List<String> factors,
      final EventMention em,
      final SentenceTheory st,
      final HashMap<String, HashSet<String>> selectionConstraints,
      final int neighborDistance) {
    // Assumptions:
    // - themeCandidates is not empty
    // - em is allowed to take a theme
    // - maximum of 1 theme argument is allowed TODO review this assumption

    // include all existing arguments
    final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
    newArgsBuilder.addAll(em.arguments());

    int factorPhraseStartIndex = em.anchorNode().span().startIndex();  // semantic phrase
    int factorPhraseEndIndex = em.anchorNode().span().endIndex();
    if(em.semanticPhraseStart().isPresent() && em.semanticPhraseEnd().isPresent()) {
      factorPhraseStartIndex = em.semanticPhraseStart().get();
      factorPhraseEndIndex = em.semanticPhraseEnd().get();
    }

    Optional<Mention> bestMention = Optional.absent();
    int shortestDistance = 99;
    boolean themeInPhrase = false;
    for (Mention m : themeCandidates) {
      String entityType = m.entityType().toString();
      int mentionStartIndex = m.head().tokenSpan().startToken().index();
      int mentionEndIndex = m.head().tokenSpan().endToken().index();
      int d = Math.min(Math.abs(  // distance to phrase
          factorPhraseEndIndex - mentionStartIndex), Math.abs(factorPhraseEndIndex - mentionEndIndex));

      // Is this Mention disallowed as a theme for any of this factor's types?
      boolean licitThemeType = true;
      for (String factor : factors) {
        if (selectionConstraints.containsKey(factor)) {
          licitThemeType = licitThemeType && selectionConstraints.get(factor).contains(entityType);
        }
      }
      if (!licitThemeType) {
        //System.out.println("invalid factor-theme combo " + factors.toString() + " & " + entityType);
        continue;
      } else {

        // is this mention part of the semantic phrase?
        boolean overlapsPhrase =
            (factorPhraseStartIndex <= mentionEndIndex && mentionEndIndex <= factorPhraseEndIndex) ||
                (mentionStartIndex <= factorPhraseEndIndex && factorPhraseEndIndex <= mentionEndIndex);
        if (overlapsPhrase) {
          shortestDistance = d;  // overwrites a closer distance that is outside of phrase!
          bestMention = Optional.of(m);
          themeInPhrase = true;
          //System.out.println("theme candidate in semantic phrase");
        }

        // is this mention near enough to consider (closer than previous best)?
        boolean inRange = d < shortestDistance;
        // is this mention near the semantic phrase, AND have we yet to encounter a theme inside the phrase?
        if(inRange && d <= neighborDistance && !themeInPhrase) {
          shortestDistance = d;
          bestMention = Optional.of(m);
        }
      }
      //System.out.println("current distance to best theme candidate: " + String.valueOf(shortestDistance));
      //System.out.println("factor/theme: " + factor + " & " + entityType);
    }

    // make a new theme arg from the best Mention
    if(bestMention.isPresent()) {
      EventMention.Argument arg = EventMention.MentionArgument.from(
          Symbol.from(EventRoleConstants.HAS_THEME),
          bestMention.get(),
          EventMentionUtils.INFERRED_ARGUMENT_SCORE);
      newArgsBuilder.add(arg);
    }

    // Make a copy of event mention with our modifications to its arguments
    return EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build());
  }

  public static EventMention heuristicallyAddPropertyArgument(
      final ImmutableList<ValueMention> propertyCandidates,
      final EventMention em,
      final int neighborDistance) {
    // Assumptions:
    // - propertyCandidates is not empty
    // - em is allowed to take a property
    // - maximum of 1 property argument is allowed TODO review this assumption

    // include all existing arguments
    final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
    newArgsBuilder.addAll(em.arguments());

    int factorPhraseStartIndex = em.anchorNode().span().startIndex();  // semantic phrase
    int factorPhraseEndIndex = em.anchorNode().span().endIndex();
    if(em.semanticPhraseStart().isPresent() && em.semanticPhraseEnd().isPresent()) {
      factorPhraseStartIndex = em.semanticPhraseStart().get();
      factorPhraseEndIndex = em.semanticPhraseEnd().get();
    }

    Optional<ValueMention> bestValueMention = Optional.absent();
    int shortestDistance = 99;
    boolean propertyInPhrase = false;
    for (ValueMention vm : propertyCandidates) {
      String valueType = vm.fullType().toString();
      int valueMentionStartIndex = vm.tokenSpan().startToken().index();
      int valueMentionEndIndex = vm.tokenSpan().endToken().index();
      int d = Math.min(Math.abs(  // distance to phrase
          factorPhraseEndIndex - valueMentionStartIndex), Math.abs(factorPhraseEndIndex - valueMentionEndIndex));

      // Is this ValueMention allowed as a property for all of this factor's types?
      boolean licitPropertyType = true;
//      for (String factor : factors) {
//        if (selectionConstraints.containsKey(factor)) {
//          licitPropertyType = licitPropertyType && selectionConstraints.get(factor).contains(valueType);
//        }
//      }
      if (!licitPropertyType) {
        //System.out.println("invalid factor-property combo " + factors.toString() + " & " + valueType);
        continue;
      } else {

        // is this mention part of the semantic phrase?
        boolean overlapsPhrase =
            (factorPhraseStartIndex <= valueMentionEndIndex && valueMentionEndIndex <= factorPhraseEndIndex) ||
                (valueMentionStartIndex <= factorPhraseEndIndex && factorPhraseEndIndex <= valueMentionEndIndex);
        if (overlapsPhrase) {
          shortestDistance = d;  // overwrites a closer distance that is outside of phrase!
          bestValueMention = Optional.of(vm);
          propertyInPhrase = true;
        }

        // is this mention near enough to consider (closer than previous best)?
        boolean inRange = d < shortestDistance;
        // is this mention near the semantic phrase, AND have we yet to encounter a theme inside the phrase?
        if(inRange && d <= neighborDistance && !propertyInPhrase) {
          shortestDistance = d;
          bestValueMention = Optional.of(vm);
        }
      }
      //System.out.println("current distance to best theme candidate: " + String.valueOf(shortestDistance));
      //System.out.println("factor/theme: " + factor + " & " + entityType);
    }

    // make a new theme arg from the best Mention
    if(bestValueMention.isPresent()) {
      EventMention.Argument arg = EventMention.ValueMentionArgument.from(
          Symbol.from(EventRoleConstants.HAS_PROPERTY),
          bestValueMention.get(),
          EventMentionUtils.INFERRED_ARGUMENT_SCORE);
      newArgsBuilder.add(arg);
    }

    // Make a copy of event mention with our modifications to its arguments
    return EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build());
  }

    public static ImmutableList<EventMention> heuristicallyAddActorArgumentViaRules(final ImmutableList<Mention> mentions, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        // .POS.asString() .word().asString()
        final ImmutableList<WordAndPOS> wordPosOfEachToken = EventMentionUtils.getWordPosOfEachToken(st);
        final List<Symbol> npTags = NPChunks.create(st).npChunks();
        final Symbol B = Symbol.from("B");
        final Symbol I = Symbol.from("I");
        final Symbol O = Symbol.from("O");

        /*
        StringBuffer s = new StringBuffer("");
        for(int i=0; i<wordPosOfEachToken.size(); i++) {
            final WordAndPOS wp = wordPosOfEachToken.get(i);
            s.append(wp.word().asString() + "/" + wp.POS().asString() + "/" + npTags.get(i).asString() + " ");
        }
        System.out.println(s.toString());

        s = new StringBuffer("");
        for(final Mention m : mentions) {
            s.append(wordPosOfEachToken.get(m.head().tokenSpan().endToken().index()).word().asString() + " ");
        }
        System.out.println("Mentions: " + s.toString());
        */

        for(final EventMention em : ems) {
            final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
            newArgsBuilder.addAll(em.arguments());

            // We look for these constructions:
            // (1) "noun trigger" : we add the noun-mention as has_actor
            // (2) "mention 's trigger" : we add the mention as has_actor
            // (3) "mention 's [NP containing trigger]" : we add the mention as has_actor
            // (4) "trigger against mention : we add the mention as has_actor
                
            int anchorStartIndex = em.anchorNode().head().tokenSpan().startToken().index();
            int anchorEndIndex = em.anchorNode().head().tokenSpan().endToken().index();

            Set<Integer> addedTokenIndices = new HashSet<Integer>();

            // Construction (1)
            if((anchorStartIndex > 0) && wordPosOfEachToken.get(anchorStartIndex).POS().asString().startsWith("NN") && wordPosOfEachToken.get(anchorStartIndex-1).POS().asString().startsWith("NN")) {
                for(final Mention m : mentions) {
                    if(m.head().tokenSpan().endToken().index() == (anchorStartIndex - 1)) {
                        EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_ACTOR), m, EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                        newArgsBuilder.add(arg);
                        addedTokenIndices.add(new Integer(anchorStartIndex - 1));
                        break;
                    }
                }
            }

            // Construction (2) and (3)
            // if I am in an NP, expand left
            int startTokenIndex = anchorStartIndex;
            if (npTags.get(startTokenIndex).equalTo(I) || npTags.get(startTokenIndex).equalTo(B)) {
                while ((startTokenIndex - 1) >= 0 && !npTags.get(startTokenIndex - 1).equalTo(O)) {
                    startTokenIndex -= 1;
                }
            }

            // is there a mention at the first word of the noun phrase?
            for(int i=startTokenIndex; i<anchorStartIndex; i++) {
                if(!addedTokenIndices.contains(i)) {
                    for(final Mention m : mentions) {
                        if(m.head().tokenSpan().endToken().index() == i) {
                            EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_ACTOR), m, EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                            newArgsBuilder.add(arg);
                            addedTokenIndices.add(new Integer(i));
                            break;
                        }
                    }
                }
            }

            if( ((startTokenIndex - 2) >= 0) && !addedTokenIndices.contains(startTokenIndex-2) ) {
                if(wordPosOfEachToken.get(startTokenIndex-1).word().asString().equals("'s")) {
                    for(final Mention m : mentions) {
                        if(m.head().tokenSpan().endToken().index() == (startTokenIndex - 2)) {
                            EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_ACTOR), m, EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                            newArgsBuilder.add(arg);
                            addedTokenIndices.add(new Integer(startTokenIndex - 2));
                            break;
                        }
                    }
                }
            }

            // Construction (4)
            if((anchorEndIndex + 2) < wordPosOfEachToken.size()) {
                if(wordPosOfEachToken.get(anchorEndIndex+1).word().asString().toLowerCase().equals("against")) {
                    for(final Mention m : mentions) {
                        if(m.head().tokenSpan().startToken().index() == (anchorEndIndex + 2)) {
                            EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_ACTOR), m, EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                            newArgsBuilder.add(arg);
                            addedTokenIndices.add(new Integer(anchorEndIndex + 2));
                            break;
                        }
                    }
                }
            }

            ret.add(EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build()));
        }

        return ret.build();
    }

    // +2
    // We will add an Actor argument to event mentions without Active nor Affected argument, provided distance (num# tokens) between Actor and trigger is small.
    // Note that 'mentions' MUST be has_actor like mentions
    public static ImmutableList<EventMention> heuristicallyAddActorArgumentViaSurrounding(final ImmutableList<Mention> mentions, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        for(final EventMention em : ems) {
            final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
            newArgsBuilder.addAll(em.arguments());

            if (em.argsForRole(Symbol.from(EventRoleConstants.HAS_ACTIVE_ACTOR)).size() == 0
                && em.argsForRole(Symbol.from(EventRoleConstants.HAS_AFFECTED_ACTOR)).size() == 0
                && em.argsForRole(Symbol.from(EventRoleConstants.HAS_ACTOR)).size() == 0) {

                // is there a mention that is near the trigger?
                int anchorIndex = em.anchorNode().head().tokenSpan().endToken().index();

                int shortestDistance = 99;
                Optional<Mention> bestMention = Optional.absent();
                for(final Mention m : mentions) {
                    int startIndex = m.head().tokenSpan().startToken().index();
                    int endIndex = m.head().tokenSpan().endToken().index();

                    int d = Math.min(Math.abs(anchorIndex - startIndex), Math.abs(anchorIndex - endIndex));
                    if(d <= 5) {
                        if(d < shortestDistance) {
                            shortestDistance = d;
                            bestMention = Optional.of(m);
                        }
                    }
                }

                if(bestMention.isPresent()) {
                    EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_ACTOR), bestMention.get(), EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                    newArgsBuilder.add(arg);
                }
                ret.add(EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build()));
            } else {
                ret.add(em);
            }
        }
        return ret.build();
    }

    public static ImmutableList<EventMention> heuristicallyAddActorArgument(final ImmutableList<Mention> mentions, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList<EventMention> emsViaRules = EventMentionUtils.heuristicallyAddActorArgumentViaRules(mentions, ems, st);
        //return EventMentionUtils.heuristicallyAddActorArgumentViaSurrounding(mentions, emsViaRules, st);
        return emsViaRules;
    }

    // +2
    // Note that the 'mentions' passed in MUST be Artifact like
    public static ImmutableList<EventMention> heuristicallyAddArtifactArgument(final ImmutableList<Mention> mentions, final ImmutableList<EventMention> ems, final SentenceTheory st) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        for(final EventMention em : ems) {
            final ImmutableList.Builder<EventMention.Argument> newArgsBuilder = ImmutableList.builder();
            newArgsBuilder.addAll(em.arguments());

            // is there a mention that is near the trigger?
            int anchorIndex = em.anchorNode().head().tokenSpan().endToken().index();

            int shortestDistance = 99;
            Optional<Mention> bestMention = Optional.absent();
            for (final Mention m : mentions) {
                int startIndex = m.head().tokenSpan().startToken().index();
                int endIndex = m.head().tokenSpan().endToken().index();

                int d = Math.min(Math.abs(anchorIndex - startIndex), Math.abs(anchorIndex - endIndex));
                if (d <= 5) {
                    if (d < shortestDistance) {
                        shortestDistance = d;
                        bestMention = Optional.of(m);
                    }
                }
            }

            if (bestMention.isPresent()) {
                boolean alreadyExists = false;
                for(final EventMention.Argument arg : em.arguments()) {
                    if(arg instanceof EventMention.MentionArgument) {
                        final EventMention.MentionArgument mentionArg = (EventMention.MentionArgument) arg;
                        if(mentionArg.mention().equals(bestMention.get())) {
                            alreadyExists = true;
                            break;
                        }
                    }
                }
                if(!alreadyExists) {
                    EventMention.Argument arg = EventMention.MentionArgument.from(Symbol.from(EventRoleConstants.HAS_ARTIFACT), bestMention.get(), EventMentionUtils.INFERRED_ARGUMENT_SCORE);
                    newArgsBuilder.add(arg);
                    ret.add(EventMentionUtils.newEventMentionWithArguments(em, newArgsBuilder.build()));
                    continue;
                }
            }

            ret.add(em);
        }
        return ret.build();
    }

    // +1
    public static Optional<String> getMentionType(final EventMention.Argument arg) {
        Optional<String> mentionType = Optional.absent();

        if(arg instanceof EventMention.MentionArgument) {
            final EventMention.MentionArgument a = (EventMention.MentionArgument) arg;
            mentionType = Optional.of(a.mention().mentionType().name().toString());
        }

        return mentionType;
    }

    // +1
    public static ImmutableList<EventMention.MentionArgument> getMentionArguments(final ImmutableList<EventMention.Argument> arguments) {
        final ImmutableList.Builder<EventMention.MentionArgument> ret = ImmutableList.builder();
        for(final EventMention.Argument arg : arguments) {
            if(arg instanceof EventMention.MentionArgument) {
                ret.add((EventMention.MentionArgument)arg);
            }
        }
        return ret.build();
    }

    // +1
    public static ImmutableList<EventMention.Argument> getNonMentionArguments(final ImmutableList<EventMention.Argument> arguments) {
        final ImmutableList.Builder<EventMention.Argument> ret = ImmutableList.builder();
        for(final EventMention.Argument arg : arguments) {
            if(!(arg instanceof EventMention.MentionArgument)) {
                ret.add(arg);
            }
        }
        return ret.build();
    }

    // if arg1 is a NAME, then we will just use arg1 head to check if it covers arg2
    public static boolean spanCoversUsingNameHead(final EventMention.Argument arg1, final EventMention.Argument arg2) {
        final Optional<String> arg1MentionType = EventMentionUtils.getMentionType(arg1);

        int start1 = 0;
        int end1 = 0;
        if((arg1 instanceof EventMention.MentionArgument) && arg1MentionType.isPresent() && arg1MentionType.get().equals("NAME")) {
            final EventMention.MentionArgument arg = (EventMention.MentionArgument)arg1;
            start1 = arg.mention().head().span().startCharOffset().asInt();
            end1 = arg.mention().head().span().endCharOffset().asInt();
        } else {
            start1 = arg1.span().startCharOffset().asInt();
            end1 = arg1.span().endCharOffset().asInt();
        }

        final int start2 = arg2.span().startCharOffset().asInt();
        final int end2 = arg2.span().endCharOffset().asInt();
        if((start1 <= start2) && (end2 <= end1)) {
            return true;
        } else {
            return false;
        }
    }

    // +1
    public static boolean spanCovers(final EventMention.Argument arg1, final EventMention.Argument arg2) {
        final int start1 = arg1.span().startCharOffset().asInt();
        final int end1 = arg1.span().endCharOffset().asInt();
        final int start2 = arg2.span().startCharOffset().asInt();
        final int end2 = arg2.span().endCharOffset().asInt();
        if((start1 <= start2) && (end2 <= end1)) {
            return true;
        } else {
            return false;
        }
    }

    // +1
    public static ImmutableList<EventMention.Argument> filterForRoles(final ImmutableList<EventMention.Argument> arguments, final ImmutableSet<String> roles) {
        final ImmutableList.Builder<EventMention.Argument> ret = ImmutableList.builder();

        for(final EventMention.Argument arg : arguments) {
            if(roles.contains(arg.role().asString())) {
                ret.add(arg);
            }
        }

        return ret.build();
    }

    // +1
    public static boolean anchorIsEntityMention(final EventMention em, final SentenceTheory st) {
        final int start = em.anchorNode().head().span().startCharOffset().asInt();
        final int end = em.anchorNode().head().span().endCharOffset().asInt();

        for(final Mention m : st.mentions()) {
            final String entityType = m.entityType().toString();
            if(entityType.equals("PER") || entityType.equals("ORG") || entityType.equals("GPE") || entityType.equals("LOC")) {
                // || entityType.equals("FAC") || entityType.equals("WEA") || entityType.equals("VEH")) {
                final int mStart = m.head().span().startCharOffset().asInt();
                final int mEnd = m.head().span().endCharOffset().asInt();
                if (start == mStart && end == mEnd) {
                    return true;
                }
            }
        }
        for(final ValueMention m : st.valueMentions()) {
            final int mStart = m.span().startCharOffset().asInt();
            final int mEnd = m.span().endCharOffset().asInt();
            if(start == mStart && end == mEnd) {
                return true;
            }
        }

        return false;
    }

    // +2
    public static ImmutableSetMultimap<String, EventMention> groupByAnchor(final ImmutableList<EventMention> mentions) {
        final ImmutableSetMultimap.Builder<String, EventMention> ret = ImmutableSetMultimap.builder();
        for(final EventMention mention : mentions) {
            final String start = new Integer(mention.anchorNode().span().startCharOffset().asInt()).toString();
            final String end = new Integer(mention.anchorNode().span().endCharOffset().asInt()).toString();
            ret.put(start + "," + end, mention);
        }
        return ret.build();
    }

    // +1
    public static ImmutableList<WordAndPOS> getWordPosOfEachToken(final SentenceTheory st) {
        final ImmutableList.Builder<WordAndPOS> sentenceWordAndPosBuilder = ImmutableList.builder();
        if (!st.parse().isAbsent() && st.parse().root().isPresent()) {
            final SynNode root = st.parse().root().get();
            for (int j = 0; j < root.numTerminals(); j++) {
                final SynNode node = root.nthTerminal(j);
                sentenceWordAndPosBuilder.add(WordAndPOS.fromWordThenPOS(Symbol.from(node.headWord().asString().toLowerCase()), node.headPOS()));
            }
        }
        return sentenceWordAndPosBuilder.build();
    }

    // +1
    public static ImmutableList<String> getWordOfEachToken(final SentenceTheory st) {
        final ImmutableList.Builder<String> ret = ImmutableList.builder();
        if (!st.parse().isAbsent() && st.parse().root().isPresent()) {
            final SynNode root = st.parse().root().get();
            for (int j = 0; j < root.numTerminals(); j++) {
                final SynNode node = root.nthTerminal(j);
                ret.add(node.headWord().asString());
            }
        }
        return ret.build();
    }

    // +1
    public static ImmutableList<SynNode> getSynNodeOfEachToken(final SentenceTheory st) {
        final ImmutableList.Builder<SynNode> ret = ImmutableList.builder();
        if (!st.parse().isAbsent() && st.parse().root().isPresent()) {
            final SynNode root = st.parse().root().get();
            for (int j = 0; j < root.numTerminals(); j++) {
                final SynNode node = root.nthTerminal(j);
                ret.add(node);
            }
        }
        return ret.build();
    }

    // +2
    public static ImmutableList<EventMention> findEventMentionUsingSynNode(final ImmutableList<EventMention> ems, final SynNode node) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();

        final int start = node.head().span().startCharOffset().asInt();
        final int end = node.head().span().endCharOffset().asInt();

        for(final EventMention em : ems) {
            final int mStart = em.anchorNode().head().span().startCharOffset().asInt();
            final int mEnd = em.anchorNode().head().span().endCharOffset().asInt();

            if(start==mStart && end==mEnd) {
                ret.add(em);
            }
        }

        return ret.build();
    }

    // +2
    public static ImmutableList<EventMention> findTypedEventMentionUsingSynNode(final ImmutableList<EventMention> ems, final SynNode node) {
        final ImmutableList.Builder<EventMention> ret = ImmutableList.builder();
        for(final EventMention em : findEventMentionUsingSynNode(ems, node)) {
            if(!em.type().asString().equals(EventTypeConstants.EVENT)) {
                ret.add(em);
            }
        }
        return ret.build();
    }

    // +1
    public static Optional<SynNode> findCoveringSynNode(final SentenceTheory st, final TokenSequence.Span spanToCover) {
        Optional<SynNode> ret = Optional.absent();
        if (!st.parse().isAbsent() && st.parse().root().isPresent()) {
            final SynNode root = st.parse().root().get();
            ret = root.coveringNonterminalFromTokenSpan(spanToCover);
        }
        return ret;
    }

    public static String printContextOfAnchor(final EventMention em, final SentenceTheory st) {
        int semanticPhraseStart = em.anchorNode().span().startIndex();
        int semanticPhraseEnd = em.anchorNode().span().endIndex();

        if(em.semanticPhraseStart().isPresent() && em.semanticPhraseEnd().isPresent()) {
            semanticPhraseStart = em.semanticPhraseStart().get();
            semanticPhraseEnd = em.semanticPhraseEnd().get();
        }

        final String contextString = st.tokenSequence().span(semanticPhraseStart, semanticPhraseEnd).tokenizedText().utf16CodeUnits().toString();

        return em.type().asString() + "\t" + em.anchorNode().span().tokenizedText().utf16CodeUnits().toLowerCase() + "\t" + contextString;
    }

    public static String eventMentionTokenIndicesToString(final EventMention em) {
        if(em.semanticPhraseStart().isPresent() && em.semanticPhraseEnd().isPresent()) {
            return(em.semanticPhraseStart().get().toString() + "_" + em.semanticPhraseEnd().get().toString());
        } else {
            return(Integer.toString(em.anchorNode().span().startToken().index()) + "_" + Integer.toString(em.anchorNode().span().endToken().index()));
        }
    }

    public static boolean eventMentionHasJustGenericEvent(final EventMention em) {
      Set<String> types = new HashSet<String>();
      for(final EventMention.EventType et : em.eventTypes()) {
        types.add(et.eventType().asString());
      }

      List<String> typeList = new ArrayList<String>();
      for(final String s : types) {
        typeList.add(s);
      }

      return (typeList.size()==1) && (typeList.get(0).contains("/Event#Event") || typeList.get(0).equals("Event"));
    }

    public static boolean eventMentionHasJustGenericFactor(final EventMention em) {
      Set<String> types = new HashSet<String>();
      for(final EventMention.EventType et : em.factorTypes()) {
        types.add(et.eventType().asString());
      }

      List<String> typeList = new ArrayList<String>();
      for(final String s : types) {
        typeList.add(s);
      }

      return (typeList.size()==1) && (typeList.get(0).contains("/ICM#Factor") || typeList.get(0).equals("Factor"));
    }

    public static float INFERRED_ARGUMENT_SCORE = 0.5f;
}

