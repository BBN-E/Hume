package com.bbn.serif.util;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.*;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Created by bmin on 10/22/18.
 */
public class GenericEventDetector {
    static ImmutableSet<String> role_active_actor = ImmutableSet.of("sub", "by");
    static ImmutableSet<String> et_active_actor = ImmutableSet.of("GPE", "PER", "ORG");

    static ImmutableSet<String> role_affected_actor = ImmutableSet.of("obj", "including");
    static ImmutableSet<String> et_affected_actor = ImmutableSet.of("GPE", "PER", "ORG");

    static ImmutableSet<String> role_location = ImmutableSet.of("in", "at", "over", "<loc>", "to", "into");
    static ImmutableSet<String> et_location = ImmutableSet.of("GPE", "LOC");

    static ImmutableSet<String> role_time = ImmutableSet.of("in", "at", "over", "during", "<temp>");

    static ImmutableSet<String> role_artifact = ImmutableSet.of("by", "of", "with", "poss", "via");
    static ImmutableSet<String> et_artifact = ImmutableSet.of("VEH", "WEA");

    /*
     * This is based on the TimeML annotation guideline
     *     https://catalog.ldc.upenn.edu/docs/LDC2006T08/timeml_annguide_1.2.1.pdf
     * Examples are in: /nfs/raid88/u10/users/bmin/temp/timeml_event_examples.txt
     */
    static ImmutableMap<String, String> class2triggerList =  new ImmutableMap.Builder<String, String>()
            .put("i_action/intention/pos",
                    "expect, attempt, try, scramble, ask, order, persuade, request, beg, command, urge, authorize, promise, offer, assure, propose, agree, decide, " +
                            "promise, offer, assure, propose, agree, decide, swear, vow, declare, proclaim, claim, allege, suggest")
            .put("i_action/intention/neg", "delay, postpone, defer, hinder, set back, avoid, prevent, cancel")
            .put("i_state/intention/pos", "feel, be conceivable, be sure, hope, prepare, believe, think, suspect, imagine, want, love, like, " +
                    "desire, crave, lust, hope, expect, aspire, plan, need, require, demand, be ready, be eager, be prepared, be able")
            .put("i_state/intention/neg", "fear, hate, dread, worry, doubt, be afraid, be unable")
            .put("state", "shortage, prepare, ready, on board")
            .put("reporting", "say, report, tell, explain, state, said, report, cite")
            .put("perception", "see, watch, glimpse, behold, view, hear, listen, overhear, saw, hear")
            .put("aspectual/initiation", "begin, start, commence, set out, set about, lead off, originate, initiate")
            .put("aspectual/reinitiation", "restart, reinitiate, reignite")
            .put("aspectual/termination", "stop, cancel, end, halt, terminate, cease, discontinue, interrupt, quit, give up, abandon, block, break off, lay off, call off, wind up")
            .put("aspectual/culmination", "finish, complete")
            .put("aspectual/continuation", "continue, keep, go on, proceed, go along, carry on, uphold, bear on, persist, persevere")
            .put("light predicate", "take place") // mostly light verbs
            .build();

    public static List<EventMention> getEventMentions(SynNode anchorNode, SentenceTheory sentenceTheory, DocTheory docTheory) {
        List<EventMention> eventMentions = new ArrayList<EventMention>();
        for (Proposition topProp : sentenceTheory.propositions()) {
            if(topProp.predHead().isPresent()) {
                SynNode predHead = topProp.predHead().get();
                if(predHead.head().span().equals(anchorNode.head().span())) {

                    List<EventMention.Argument> arguments = new ArrayList<EventMention.Argument>();
                    for(Proposition.Argument a : topProp.args()) {
                        final Symbol role = a.role().isPresent()? a.role().get() : Symbol.from("UNKNOWN");
                        Optional<String> text = Optional.absent();

                        Optional<String> arg_role = Optional.absent();
                        if(role_active_actor.contains(role.asString()))
                            arg_role = Optional.of("has_active_actor");
                        else if(role_affected_actor.contains(role.asString()))
                            arg_role = Optional.of("has_affected_actor");
                        else if(role_location.contains(role.asString()))
                            arg_role = Optional.of("has_location");
                        else if(role_time.contains(role.asString()))
                            arg_role = Optional.of("has_time");
                        else if(role_artifact.contains(role.asString()))
                            arg_role = Optional.of("has_artifact");

                        if(arg_role.isPresent()) {
                            if (a instanceof Proposition.MentionArgument) {
                                Proposition.MentionArgument ma = (Proposition.MentionArgument)a;
                                SynNode mention = ma.mention().node();
                                while (mention != null) {
                                    mention = mention.head().equals(mention) ? null : mention.head();
                                }

                                String entityType = ma.mention().entityType().name().asString();
                                if((et_active_actor.contains(entityType) && arg_role.get().equals("has_active_actor")) ||
                                        (et_affected_actor.contains(entityType) && arg_role.get().equals("has_affected_actor")) ||
                                        (et_location.contains(entityType) && arg_role.get().equals("has_location")) ||
                                        (et_artifact.contains(entityType) && arg_role.get().equals("has_artifact")) ) {
                                    EventMention.MentionArgument arg = EventMention.MentionArgument.from(Symbol.from(arg_role.get()), ma.mention(), 0.7f);
                                    arguments.add(arg);
                                }
                            }
                            else if (a instanceof Proposition.TextArgument) {
                                Proposition.TextArgument ta = (Proposition.TextArgument)a;
                                Optional<ValueMention> vmOptional = sentenceTheory.valueMentions().lookupByTokenSpan(ta.span().tokenSequence().span());
                                if(vmOptional.isPresent()) {
                                    EventMention.ValueMentionArgument arg = EventMention.ValueMentionArgument.from(Symbol.from(arg_role.get()), vmOptional.get(), 0.7f);
                                    arguments.add(arg);
                                }
                            }
                        }
                    }

                    Optional<String> extendedEventMention = getExtendedEventMention(anchorNode, sentenceTheory, docTheory);
                    Symbol eventPatternID = Symbol.from(extendedEventMention.isPresent()?extendedEventMention.get():"NA");

                    // // get NP
                    // Optional<SynNode> anchorNP = findNPforEventTriggers(anchorNode, sentenceTheory);
                    // if(anchorNP.isPresent())
                    //    anchorNode = anchorNP.get();

                    EventMention em = EventMention
                            .builder(Symbol.from("Event"))
                            .setAnchorNode(anchorNode)
                            .setAnchorPropFromNode(sentenceTheory)
                            .setScore(0.3)
                            .setPatternID(eventPatternID)
                            .setArguments(arguments)
                            .build();
                    eventMentions.add(em);
                }
            }
        }
        return eventMentions;
    }

    public static Optional<SynNode> findNPforEventTriggers(SynNode anchorNode, SentenceTheory sentenceTheory) {
        Optional<Mention> mentionOptional = Optional.absent();

        int MAX_SPAN_COVERING_RATIO = 5;

        float minSpanCoveringRatio = 20;
        if(anchorNode.headPOS().asString().toLowerCase().startsWith("nn")) {
            for (Mention mention : sentenceTheory.mentions()) {
                if (!mention.isName() && !mention.isPronoun()) {
                    if (mention.span().startCharOffset().asInt() <= anchorNode.span().startCharOffset().asInt() &&
                            mention.span().endCharOffset().asInt() >= anchorNode.span().endCharOffset().asInt()) {
                        float spanCoveringRatio = (mention.span().endCharOffset().asInt() - mention.span().startCharOffset().asInt() + 1) * 1.0f / (anchorNode.span().endCharOffset().asInt() - anchorNode.span().startCharOffset().asInt() + 1);
                        if (spanCoveringRatio < minSpanCoveringRatio) {
                            minSpanCoveringRatio = spanCoveringRatio;
                            mentionOptional = Optional.of(mention);
                        }
                    }
                }
            }
        }

        if(minSpanCoveringRatio<5)
            return Optional.of(mentionOptional.get().node());
        else
            return Optional.absent();
    }

    public static Optional<String> getExtendedEventMention(SynNode anchorNode, SentenceTheory sentenceTheory, DocTheory docTheory) {
        for (Proposition topProp : sentenceTheory.propositions()) {
            if(topProp.predHead().isPresent()) {
                SynNode predHead = topProp.predHead().get();
                if(predHead.head().span().equals(anchorNode.head().span())) {
                    Optional<String> sub = Optional.absent();
                    Optional<String> obj = Optional.absent();
                    Optional<String> iobj = Optional.absent();
                    Optional<String> poss = Optional.absent();
                    Optional<String> of = Optional.absent();
                    Optional<String> by = Optional.absent();
                    Optional<String> strFor = Optional.absent();
                    Optional<String> in = Optional.absent();
                    Optional<String> on = Optional.absent();
                    Optional<String> at = Optional.absent();
                    Optional<String> over = Optional.absent();
                    Optional<String> under = Optional.absent();
                    Optional<String> with = Optional.absent();
                    Optional<String> without = Optional.absent();
                    Optional<String> to = Optional.absent();
                    Optional<String> into = Optional.absent();
                    Optional<String> about = Optional.absent();
                    Optional<String> against = Optional.absent();
                    Optional<String> from = Optional.absent();
                    Optional<String> between = Optional.absent();
                    Optional<String> among = Optional.absent();
                    Optional<String> involving = Optional.absent();

                    for(Proposition.Argument a : topProp.args()) {
                        final Symbol role = a.role().isPresent()? a.role().get() : Symbol.from("UNKNOWN");
                        Optional<String> text = Optional.absent();

                        if(role.asString().equals("<ref>") ||
                                role.asString().equals("<unknown>") ||
                                role.asString().equals("that") ||
                                role.asString().equals("when") ||
                                role.asString().equals("before") ||
                                role.asString().equals("during") ||
                                role.asString().equals("after") ||
                                role.asString().equals("since") ||
                                role.asString().equals("where") ||
                                role.asString().equals("while") ||
                                role.asString().equals("<temp>") ||
                                role.asString().equals("via") ||
                                role.asString().equals("including") ||
                                role.asString().equals("if") ||
                                role.asString().equals("as") ||
                                role.asString().equals("following") ||
                                role.asString().equals("out_of") ||
                                role.asString().equals("below") ||
                                role.asString().equals("<loc>") ||
                                role.asString().equals("like") )
                            continue;

                        if (a instanceof Proposition.MentionArgument) {
                            Proposition.MentionArgument ma = (Proposition.MentionArgument)a;
                            SynNode mention = ma.mention().node();
                            while (mention != null) {
                                mention = mention.head().equals(mention) ? null : mention.head();
                            }
                            if(ma.mention().entityType().name().asString().equals("OTH") ||
                                    ma.mention().entityType().name().asString().equals("UNDET"))
                                text = Optional.of(ma.mention().head().head().tokenSpan().tokenizedText(docTheory).utf16CodeUnits());
                            else
                                text = Optional.of(ma.mention().entityType().name().asString());
                        }
                        else if (a instanceof Proposition.TextArgument) {
                            Proposition.TextArgument ta = (Proposition.TextArgument)a;
                            text = Optional.of(ta.node().tokenSpan().tokenizedText(docTheory).utf16CodeUnits());
                        }else if(a instanceof Proposition.PropositionArgument){
                            Proposition.PropositionArgument pa = (Proposition.PropositionArgument)a;
                            //if s0 and s1 are anchorNodes of EventMentions, we may just want to match the predicate of the Proposition with them
                            Optional<SynNode> paPredHead = pa.proposition().predHead();
                            if(pa.proposition().predHead().isPresent())
                                text = Optional.of(pa.proposition().predHead().get().tokenSpan().tokenizedText(docTheory).utf16CodeUnits());
                        }

                        if(role.asString().equals("<sub>"))
                            sub = text;
                        else if(role.asString().equals("<obj>"))
                            obj = text;
                        else if(role.asString().equals("<iobj>"))
                            iobj = text;
                        else if(role.asString().equals("<poss>"))
                            poss = text;
                        else if(role.asString().equals("of"))
                            of = text;
                        else if(role.asString().equals("with"))
                            with = text;
                        else if(role.asString().equals("without"))
                            without = text;
                        else if(role.asString().equals("by"))
                            by = text;
                        else if(role.asString().equals("in"))
                            in = text;
                        else if(role.asString().equals("into"))
                            into = text;
                        else if(role.asString().equals("involving"))
                            involving = text;
                        else if(role.asString().equals("on"))
                            on = text;
                        else if(role.asString().equals("at"))
                            at = text;
                        else if(role.asString().equals("over"))
                            over = text;
                        else if(role.asString().equals("under"))
                            under = text;
                        else if(role.asString().equals("to"))
                            to = text;
                        else if(role.asString().equals("for"))
                            strFor = text;
                        else if(role.asString().equals("about"))
                            about = text;
                        else if(role.asString().equals("against"))
                            against = text;
                        else if(role.asString().equals("from"))
                            from = text;
                        else if(role.asString().equals("between"))
                            between = text;
                        else if(role.asString().equals("among"))
                            among = text;
                    }

                    String head = "[" + anchorNode.tokenSpan().tokenizedText(docTheory).utf16CodeUnits() + "]";
                    if (sub.isPresent())
                        head = sub.get() + " " + head;
                    if (poss.isPresent())
                        head += poss.get() + " 's ";
                    if (obj.isPresent())
                        head += " " + obj.get();
                    if (of.isPresent())
                        head += " of " + of.get();
                    if (from.isPresent())
                        head += " from " + from.get();
                    if (by.isPresent())
                        head += " by " + by.get();
                    if (with.isPresent())
                        head += " with " + with.get();
                    if (without.isPresent())
                        head += " without " + without.get();
                    if (strFor.isPresent())
                        head += " for " + strFor.get();
                    if (in.isPresent())
                        head += " in " + in.get();
                    if (into.isPresent())
                        head += " into " + into.get();
                    if (on.isPresent())
                        head += " on " + on.get();
                    if (at.isPresent())
                        head += " at " + at.get();
                    if (over.isPresent())
                        head += " over " + over.get();
                    if (under.isPresent())
                        head += " under " + under.get();
                    if (to.isPresent())
                        head += " to " + to.get();
                    if (iobj.isPresent())
                        head += " " + iobj.get();
                    if (about.isPresent())
                        head += " about " + about.get();
                    if (involving.isPresent())
                        head += " involving " + involving.get();
                    if (against.isPresent())
                        head += " against " + against.get();
                    if (between.isPresent())
                        head += " between " + between.get();
                    if (among.isPresent())
                        head += " among " + among.get();

                    return Optional.of(head);
                }
            }
        }

        return Optional.absent();
    }
}
