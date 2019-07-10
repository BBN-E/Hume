package com.bbn.necd.event.bin;

import com.bbn.bue.common.StringUtils;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.io.CompressedFileUtils;

import com.google.common.base.Charsets;
import com.google.common.base.Joiner;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMultiset;
import com.google.common.collect.Multiset;
import com.google.common.collect.Multisets;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.io.Writer;

/**
 * Outputs counts of predicate paths.
 */
public final class PredicatePathCounter {

  public static void main(final String[] args) throws IOException {
    if (args.length != 2) {
      System.out.println("Usage: predicatePathCounter features output");
      System.exit(1);
    }

    final File featureFile = new File(args[0]);
    final File outFile = new File(args[1]);

    // Load features
    final ImmutableList<EventFeatures> allFeatures =
        CompressedFileUtils.readAsJsonList(featureFile, EventFeatures.class);

    // Compute counts
    final Multiset<ImmutableList<Symbol>> predicatePathCounts = countPaths(allFeatures);
    final Joiner spaceJoiner = StringUtils.spaceJoiner();
    try (final Writer writer = Files.asCharSink(outFile, Charsets.UTF_8).openBufferedStream()) {
      for (final Multiset.Entry<ImmutableList<Symbol>> entry : predicatePathCounts.entrySet()) {
        writer.write(spaceJoiner.join(entry.getElement()) + "\t" + entry.getCount() + "\n");
      }
    }
  }

  private static ImmutableMultiset<ImmutableList<Symbol>> countPaths(
      final Iterable<EventFeatures> features) {
    final Multiset<ImmutableList<Symbol>> ret = HashMultiset.create();
    for (final EventFeatures eventFeatures : features) {
      ret.add(eventFeatures.stems());
    }
    return Multisets.copyHighestCountFirst(ret);
  }
}
