// we merge ACCENT, KBP and NN events that share path prefixes (and in general choose the
// longer path one), but ACCENT events (even if on shorted path) can still override

package com.bbn.serif.util.resolver.sentenceresolver;

import com.bbn.bue.common.strings.offsets.CharOffset;
import com.bbn.bue.common.strings.offsets.OffsetRange;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.theories.EventMentions;
import com.bbn.serif.theories.SentenceTheory;
import com.bbn.serif.util.events.consolidator.EventConsolidator;
import com.bbn.serif.util.events.consolidator.common.EventMentionUtils;
import com.bbn.serif.util.events.consolidator.common.OntologyHierarchy;
import com.bbn.serif.util.resolver.Resolver;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;

import java.util.List;
import java.util.Set;

// +2
public final class AllEventMentionMerger implements SentenceResolver, Resolver {

  final ImmutableMap<String, OntologyHierarchy> ontologyHierarchies;

  public AllEventMentionMerger(final ImmutableMap<String, OntologyHierarchy> oh) {
    this.ontologyHierarchies = oh;
  }

  public final SentenceTheory resolve(final SentenceTheory sentenceTheory) {

    // Builder for final set of EventMentions that will appear in the returned sentence theory
    EventMentions.Builder emsBuilder = new EventMentions.Builder();

    // List of event mentions to possibly merge in Step 1
    ImmutableList.Builder<EventMention> emListBuilder = new ImmutableList.Builder<>();
    // List of just accent event mentions
    ImmutableList.Builder<EventMention> accentEmListBuilder = new ImmutableList.Builder<>();
    // List of just generic event mentions
    ImmutableList.Builder<EventMention> genericEmListBuilder = new ImmutableList.Builder<>();

    for (EventMention em : sentenceTheory.eventMentions()) {
      if (em.model().isPresent() && em.model().get().equalTo(Symbol.from("ACCENT"))) {
        accentEmListBuilder.add(em);
        emListBuilder.add(em);
      } else if (em.model().isPresent() && !em.model().get().equalTo(Symbol.from("Generic")))
        emListBuilder.add(em);
      else
        genericEmListBuilder.add(em);
    }

    final ImmutableList<EventMention> accentEmList = accentEmListBuilder.build();
    List<EventMention> mergedEventMentions = emListBuilder.build();

    // Step 1 -- Merge all non-generic events
    mergedEventMentions = Lists.newArrayList(EventConsolidator
        .mergeSamePathEventMentions(ImmutableList.copyOf(mergedEventMentions), ontologyHierarchies,
            sentenceTheory, accentEmList));


    // Step 2 -- Merge in generic event arguments to non-generic events
    List<EventMention> unmergedGenericEMs = Lists.newArrayList();
    Set<String> unmergedGenericEMsOffset = Sets.newHashSet();
    for(final EventMention genericEM : genericEmListBuilder.build()) {
      OffsetRange<CharOffset> offset = genericEM.anchorNode().head().span().charOffsetRange();
      boolean merged = false;
      for(int j=0; j<mergedEventMentions.size(); j++) {
        if(offset.equals(mergedEventMentions.get(j).anchorNode().head().span().charOffsetRange())) {
          final EventMention newEM = EventMentionUtils
              .mergeEventMentions(mergedEventMentions.get(j), genericEM, sentenceTheory);
          mergedEventMentions.set(j, newEM);
          merged = true;
        }
      }

      final String offsetString = genericEM.anchorNode().span().startCharOffset().toString() + "," + genericEM.anchorNode().span().endCharOffset().toString();
      if(!merged && !unmergedGenericEMsOffset.contains(offsetString)) {
        unmergedGenericEMs.add(genericEM);
        unmergedGenericEMsOffset.add(offsetString);
      }
    }

    // Add in EMs from Step 1
    emsBuilder.addAllEventMentions(mergedEventMentions);
    // Add in unmerged EMs from Step 2
    emsBuilder.addAllEventMentions(unmergedGenericEMs);

    final SentenceTheory.Builder stBuilder = sentenceTheory.modifiedCopyBuilder();
    return stBuilder.eventMentions(emsBuilder.build()).build();
  }
}
