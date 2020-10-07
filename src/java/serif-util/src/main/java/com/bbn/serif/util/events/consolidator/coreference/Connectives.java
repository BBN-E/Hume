package com.bbn.serif.util.events.consolidator.coreference;

import com.bbn.bue.common.parameters.Parameters;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.bue.common.symbols.SymbolUtils;

import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;

import java.io.File;
import java.io.IOException;
import java.util.Set;


public final class Connectives {

  private final ImmutableSet<Symbol> comparisonContrastConnectives;
  private final ImmutableSet<Symbol> temporalSynchronousConnectives;
  private final ImmutableSet<Symbol> causeConnectives;
  private final ImmutableSet<Symbol> preventionConnectives;

  private Connectives(final Set<Symbol> comparisonContrastConnectives,
      final Set<Symbol> temporalSynchronousConnectives, final Set<Symbol> causeConnectives,
      final Set<Symbol> preventionConnectives) {
    this.comparisonContrastConnectives = ImmutableSet.copyOf(comparisonContrastConnectives);
    this.temporalSynchronousConnectives = ImmutableSet.copyOf(temporalSynchronousConnectives);
    this.causeConnectives = ImmutableSet.copyOf(causeConnectives);
    this.preventionConnectives = ImmutableSet.copyOf(preventionConnectives);
  }

  public static Connectives from(final Parameters params) throws IOException {
    return new Connectives(readComparisonWords(params), readTemporalWords(params),
        readCauseWords(params), readPreventionWords(params));
  }

  private static ImmutableSet<Symbol> readComparisonWords(Parameters params) throws IOException {
    final File file = params.getExistingFile("connective.comparisonContrast");
    return SymbolUtils.setFrom(Files.asCharSource(file, Charsets.UTF_8).readLines());
  }

  private static ImmutableSet<Symbol> readTemporalWords(Parameters params) throws IOException {
    final File file = params.getExistingFile("connective.temporalSynchronous");
    return SymbolUtils.setFrom(Files.asCharSource(file, Charsets.UTF_8).readLines());
  }

  private static ImmutableSet<Symbol> readCauseWords(Parameters params) throws IOException {
    final File file = params.getExistingFile("connective.cause");
    return SymbolUtils.setFrom(Files.asCharSource(file, Charsets.UTF_8).readLines());
  }

  private static ImmutableSet<Symbol> readPreventionWords(Parameters params) throws IOException {
    final File file = params.getExistingFile("connective.prevention");
    return SymbolUtils.setFrom(Files.asCharSource(file, Charsets.UTF_8).readLines());
  }

  public ImmutableSet<Symbol> getComparisonContrastConnectives() {
    return comparisonContrastConnectives;
  }

  public ImmutableSet<Symbol> getTemporalSynchronousConnectives() {
    return temporalSynchronousConnectives;
  }

  public ImmutableSet<Symbol> getCauseConnectives() {
    return causeConnectives;
  }

  public ImmutableSet<Symbol> getPreventionConnectives() {
    return preventionConnectives;
  }
}


