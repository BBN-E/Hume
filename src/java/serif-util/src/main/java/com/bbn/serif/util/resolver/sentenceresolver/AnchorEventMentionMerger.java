
package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.theories.Proposition;
import com.bbn.serif.types.Trend;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;

import java.util.*;


// Merges when two events have matching anchor. Arguments and types will be merged.
// Used in IARPA COVID task
public final class AnchorEventMentionMerger implements SentenceResolver, Resolver {

    public AnchorEventMentionMerger() { }

    private final boolean alreadyHasType(final EventMention eventMention, final EventMention.EventType eventTypeObj) {
        for (EventMention.EventType et : eventMention.eventTypes())
            if (et.eventType() == eventTypeObj.eventType())
                return true;
        return false;
    }

    private final boolean alreadyHasAnchor(final EventMention eventMention, final EventMention.Anchor anchorObj) {
        for (EventMention.Anchor a : eventMention.anchors())
            if (a.anchorNode() == anchorObj.anchorNode())
                return true;
        return false;
    }

    private final EventMention getMasterEventMention(List<EventMention> ems) {
        for (EventMention em: ems) {
            if (em.type() != Symbol.from("Event")){
                return em;
            }
        }
        return ems.get(0);
    }

    public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

        // Builder for final set of EventMentions that will appear in the returned sentence theory
        EventMentions.Builder emsBuilder = new EventMentions.Builder();

        // Organize event mentions by offset range
        HashMap<OffsetRange<CharOffset>, List<EventMention>> offsetRangeToEventMentions = new HashMap<>();
        for (EventMention em : sentenceTheory.eventMentions()) {
            OffsetRange<CharOffset> offsets = em.anchorNode().head().span().charOffsetRange();
            if (!offsetRangeToEventMentions.containsKey(offsets))
                offsetRangeToEventMentions.put(offsets, new ArrayList<>());
            offsetRangeToEventMentions.get(offsets).add(em);
        }

        // Merge each group into new event mention
        for (List<EventMention> ems : offsetRangeToEventMentions.values()) {
            EventMention masterEventMention = getMasterEventMention(ems); // EventMention we'll merge others into

            List<EventMention> others = new ArrayList<>();
            for (EventMention em : ems) {
                if (em == masterEventMention)
                    continue;
                others.add(em);
            }

            for (EventMention em : others) {
                //System.out.println("Merging");
                // Arguments
                masterEventMention = EventMentionUtils.mergeEventMentions(masterEventMention, em, sentenceTheory);
                // Pattern
                if (em.pattern().isPresent() && !masterEventMention.pattern().isPresent())
                    masterEventMention =
                            masterEventMention.modifiedCopyBuilder().setPatternID(em.pattern().get()).build();
                // Types
                for (EventMention.EventType et : em.eventTypes()) {
                    if (alreadyHasType(masterEventMention, et))
                        continue;
                    com.google.common.base.Optional<Double> e = com.google.common.base.Optional.absent();
                    com.google.common.base.Optional<Trend> t = com.google.common.base.Optional.absent();
                    masterEventMention.eventTypes().add(EventMention.EventType.from(et.eventType(), 0.0, e, t));
                }
                // Anchors
                for (EventMention.Anchor a : em.anchors()) {
                    if (alreadyHasAnchor(masterEventMention, a))
                        continue;
                    Proposition p = null;
                    if (a.anchorProposition().isPresent())
                        p = a.anchorProposition().get();
                    masterEventMention.anchors().add(EventMention.Anchor.from(a.anchorNode(), p));
                }
            }
            emsBuilder.addEventMentions(masterEventMention);
        }

        final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
        return stBuilder.eventMentions(emsBuilder.build()).build();
    }
}
