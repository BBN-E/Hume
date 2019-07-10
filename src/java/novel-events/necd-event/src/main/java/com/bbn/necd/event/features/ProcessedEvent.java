package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionPredicateType;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;

/**
 * Represents a minimal set of event features to be shared across implementations.
 */
public interface ProcessedEvent {
  Symbol getId();
  Optional<Symbol> getEventCode();
  PropositionPredicateType getPredType();
  ImmutableList<Symbol> getPredicates();
  ImmutableList<Symbol> getStems();
  EventFilter getEventFilter();
}
