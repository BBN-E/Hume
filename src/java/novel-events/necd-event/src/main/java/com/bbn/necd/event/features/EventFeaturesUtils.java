package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.common.sampler.SymbolPair;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableMultimap;

import java.io.File;
import java.io.IOException;

/**
 * Provides utilities for working with {@link ProcessedEvent}.
 */
public final class EventFeaturesUtils {

  /**
   * Return a multimap of codes to their event.
   *
   * @param eventFeatures the events, some of which must have codes
   * @return a multimap of codes to their events
   */
  public static <T extends ProcessedEvent> ImmutableMultimap<Symbol, T> codeFeaturesMap(
      final Iterable<T> eventFeatures) {
    final ImmutableMultimap.Builder<Symbol, T> ret = ImmutableMultimap.builder();
    for (final T ef : eventFeatures) {
      if (ef.getEventCode().isPresent()) {
        ret.put(ef.getEventCode().get(), ef);
      }
    }
    return ret.build();
  }

  public static ImmutableMap<Symbol, EventFeatures> readEventFeatures(final File infile)
      throws IOException {
    final ImmutableMap.Builder<Symbol, EventFeatures> ret = ImmutableMap.builder();

    final ImmutableList<EventFeatures> eventFeatures =
        CompressedFileUtils.readAsJsonList(infile, EventFeatures.class);

    for(final EventFeatures eg : eventFeatures) {
      ret.put(eg.id(), eg);
    }

    return ret.build();
  }

  public static ImmutableMap<SymbolPair, EventPairFeatures> readEventPairFeatures(final File infile) throws IOException {
    final ImmutableMap.Builder<SymbolPair, EventPairFeatures> ret = ImmutableMap.builder();

    final ImmutableList<EventPairFeatures> examples = CompressedFileUtils.readAsJsonList(infile, EventPairFeatures.class);

    for(final EventPairFeatures eg : examples) {
      String pairId = eg.id().asString();
      pairId = pairId.substring(1, pairId.length()-1);
      final int index = pairId.indexOf("]")+1;
      final String id1 = pairId.substring(0, index);
      final String id2 = pairId.substring(index+1);
      ret.put(SymbolPair.from(Symbol.from(id1), Symbol.from(id2)), eg);
    }

    return ret.build();
  }
}
