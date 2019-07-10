package com.bbn.necd.event.propositions;

import com.bbn.bue.common.Finishable;
import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.features.WordNetWrapper;
import com.bbn.necd.event.wrappers.ExtractedPropositionTreeEventInfo;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Sets;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;

/**
 * Extract features from a {@link ExtractedPropositionTreeEventInfo}.
 */
public final class PropositionTreeEventProcessor implements Finishable {

  private static final Logger log = LoggerFactory.getLogger(PropositionTreeEventProcessor.class);

  private static final boolean DEBUG_LOGGING = false;

  // Counts for logging
  private int totalEventsProcessed;
  private int eventFilterAllEventsProcessed;

  private final ImmutableList.Builder<PropositionTreeEvent> eventFeatures;
  private final Set<Symbol> eventIds;

  private PropositionTreeEventProcessor() {
    eventFeatures = ImmutableList.builder();
    // We use a mutable set as we need to check for membership as it is built and do not care about the final set.
    eventIds = Sets.newHashSet();
  }

  public static PropositionTreeEventProcessor from(Parameters params) {
    return new PropositionTreeEventProcessor();
  }

  public void process(final ExtractedPropositionTreeEventInfo event, final WordNetWrapper wn) {
    totalEventsProcessed++;
    if (EventFilter.ALL.equals(event.getEventFilter())) {
      eventFilterAllEventsProcessed++;
    }

    if (DEBUG_LOGGING) {
      System.out.println("********************");
      System.out.println(event.getSentenceText());
      System.out.println("Source: " + event.getSource().prettyPrint() +
          " Target: " + event.getTarget().prettyPrint());
    }
    final Optional<PropositionTreeEvent> optFeatures =
        PropositionTreeEvent.fromEventInstance(event, wn);
    if (optFeatures.isPresent()) {
      final PropositionTreeEvent features = optFeatures.get();
      final Symbol id = features.getId();
      // As there can be multiple events with the same ID, only take the first one.
      if (!eventIds.contains(id)) {
        if (DEBUG_LOGGING) {
          System.out.println(features.getPredicates());
          System.out.println();
        }
        eventFeatures.add(features);
        eventIds.add(id);
      } else {
        log.warn("Duplicate event for id {}, code {}", id, features.getEventCode().or(Symbol.from("unknown")));
      }
    }
  }

  public ImmutableList<PropositionTreeEvent> getSerializableEvents() {
    return eventFeatures.build();
  }

  public void finish() {
    log.info("Total events processed: {}", totalEventsProcessed);
    log.info("EventFilter.ALL events processed: {}", eventFilterAllEventsProcessed);
  }
}
