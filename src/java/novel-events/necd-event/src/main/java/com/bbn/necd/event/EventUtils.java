package com.bbn.necd.event;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.PropositionTreeEvent;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.annotations.Beta;
import com.google.common.base.Functions;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSortedMap;
import com.google.common.collect.Ordering;

import org.slf4j.Logger;

import java.io.File;
import java.io.IOException;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Shared utility methods.
 */
@Beta
public final class EventUtils {

  public static <K, V extends Comparable> ImmutableSortedMap<K, V> orderMapByReversedValues(
      final Map<K, V> map, final Comparator<? super K> tieBreakerOrdering) {
    final Ordering<K> naturalReverseValueOrdering =
        Ordering.natural().reverse().nullsLast().onResultOf(Functions.forMap(map, null)).compound(tieBreakerOrdering);
    return ImmutableSortedMap.copyOf(map, naturalReverseValueOrdering);
  }

  public static ImmutableMap<Symbol, PropositionTreeEvent> loadProcessedEvents(
      final Set<Symbol> ids,
      final List<File> fileList, File baseDir, final Logger log)
      throws IOException {
    final ImmutableMap.Builder<Symbol, PropositionTreeEvent> ret = ImmutableMap.builder();
    for (final File eventFeaturesFile : fileList) {
      final File fullFile = new File(baseDir, eventFeaturesFile.getPath()).getAbsoluteFile();
      log.info("Loading events from {}", fullFile);
      ret.putAll(loadProcessedEvents(ids, fullFile, false));
    }
    return ret.build();
  }

  public static ImmutableMap<Symbol, PropositionTreeEvent> loadProcessedEvents(final Set<Symbol> ids,
      final File file, boolean keepAllCoded) throws IOException {
    final ImmutableMap.Builder<Symbol, PropositionTreeEvent> ret = ImmutableMap.builder();
    final ImmutableList<PropositionTreeEvent> features =
        CompressedFileUtils.readAsJsonList(file, PropositionTreeEvent.class);
    for (final PropositionTreeEvent feature : features) {
      final Symbol id = feature.getId();
      // Only keep the event features that we actually need
      if (ids.contains(id) || (keepAllCoded && feature.getEventCode().isPresent())) {
        ret.put(id, feature);
      }
    }
    return ret.build();
  }
}
