package com.bbn.necd.event.features;

import com.bbn.bue.common.symbols.Symbol;
import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.common.base.MoreObjects;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableList;
import com.google.common.primitives.Booleans;
import com.google.common.primitives.Doubles;

import java.util.Arrays;
import java.util.List;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Represent features computed over a pair of events.
 */
@JsonAutoDetect(fieldVisibility = Visibility.ANY, getterVisibility = Visibility.NONE, setterVisibility = Visibility.NONE)
public final class EventPairFeatures {

  private final Symbol id;

  private final double[] wuPalmerConSim;
  private final double[] wuPalmerConSimCombinations;
  private final boolean[] shareSynset;
  private final boolean[] shareSynsetCombinations;
  private final boolean[] sameWord;
  private final boolean[] sameWordCombinations;
  private final boolean[] sameStem;
  private final boolean[] sameStemCombinations;

  private final double sourceSectorOverlap;
  private final double targetSectorOverlap;

  private EventPairFeatures(
      @JsonProperty("id") Symbol id,
      @JsonProperty("shareSynset") boolean[] shareSynset,
      @JsonProperty("shareSynsetCombinations") boolean[] shareSynsetCombinations,
      @JsonProperty("sameWord") boolean[] sameWord,
      @JsonProperty("sameWordCombinations") boolean[] sameWordCombinations,
      @JsonProperty("sameStem") boolean[] sameStem,
      @JsonProperty("sameStemCombinations") boolean[] sameStemCombinations,
      @JsonProperty("wuPalmerConSim") double[] wuPalmerConSim,
      @JsonProperty("wuPalmerConSimCombinations") double[] wuPalmerConSimCombinations,
      @JsonProperty("sourceSectorOverlap") double sourceSectorOverlap,
      @JsonProperty("targetSectorOverlap") double targetSectorOverlap) {
    // Check that lengths match
    final int n = shareSynset.length;
    checkArgument(sameWord.length == n && sameStem.length == n && wuPalmerConSim.length == n);
    final int m = shareSynsetCombinations.length;
    checkArgument(sameWordCombinations.length == m && sameStemCombinations.length == m && wuPalmerConSimCombinations.length == m);

    this.id = checkNotNull(id);
    this.shareSynset = shareSynset;
    this.shareSynsetCombinations = shareSynsetCombinations;
    this.sameWord = sameWord;
    this.sameWordCombinations = sameWordCombinations;
    this.sameStem = sameStem;
    this.sameStemCombinations = sameStemCombinations;
    this.wuPalmerConSim = wuPalmerConSim;
    this.wuPalmerConSimCombinations = wuPalmerConSimCombinations;
    this.sourceSectorOverlap = sourceSectorOverlap;
    this.targetSectorOverlap = targetSectorOverlap;
  }

  public static EventPairFeatures create(Symbol id,  List<Boolean> shareSynset,
      List<Boolean> shareSynsetCombinations, List<Boolean> sameWord,  List<Boolean> sameWordCombinations,
      List<Boolean> sameStem,  List<Boolean> sameStemCombinations,
       List<Double> wuPalmerConSim,  List<Double> wuPalmerConSimCombinations, double sourceSectorOverlap,
      double targetSectorOverlap) {
    return new EventPairFeatures(id, Booleans.toArray(shareSynset), Booleans.toArray(shareSynsetCombinations),
        Booleans.toArray(sameWord), Booleans.toArray(sameWordCombinations), Booleans.toArray(sameStem),
        Booleans.toArray(sameStemCombinations), Doubles.toArray(wuPalmerConSim),
        Doubles.toArray(wuPalmerConSimCombinations), sourceSectorOverlap, targetSectorOverlap);
  }

  public Symbol id() {
    return id;
  }

  public double sourceSectorOverlap() {
    return sourceSectorOverlap;
  }

  public double targetSectorOverlap() {
    return targetSectorOverlap;
  }

  public ImmutableList<Double> wuPalmerConSim() {
    return ImmutableList.copyOf(Doubles.asList(wuPalmerConSim));
  }

  public ImmutableList<Double> wuPalmerConSimCombinations() {
    return ImmutableList.copyOf(Doubles.asList(wuPalmerConSimCombinations));
  }

  public ImmutableList<Boolean> shareSynset() {
    return ImmutableList.copyOf(Booleans.asList(shareSynset));
  }

  public ImmutableList<Boolean> shareSynsetCombinations() {
    return ImmutableList.copyOf(Booleans.asList(shareSynsetCombinations));
  }

  public ImmutableList<Boolean> sameWord() {
    return ImmutableList.copyOf(Booleans.asList(sameWord));
  }

  public ImmutableList<Boolean> sameWordCombinations() {
    return ImmutableList.copyOf(Booleans.asList(sameWordCombinations));
  }

  public ImmutableList<Boolean> sameStem() {
    return ImmutableList.copyOf(Booleans.asList(sameStem));
  }

  public ImmutableList<Boolean> sameStemCombinations() {
    return ImmutableList.copyOf(Booleans.asList(sameStemCombinations));
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(id, wuPalmerConSim, wuPalmerConSimCombinations, shareSynset, shareSynsetCombinations,
        sameWord, sameWordCombinations, sameStem, sameStemCombinations, sourceSectorOverlap, targetSectorOverlap);
  }

  @Override
  public boolean equals(Object obj) {
    if (this == obj) {
      return true;
    }
    if (obj == null || getClass() != obj.getClass()) {
      return false;
    }
    final EventPairFeatures other = (EventPairFeatures) obj;
    return Objects.equal(this.id, other.id)
        && Arrays.equals(this.wuPalmerConSim, other.wuPalmerConSim)
        && Arrays.equals(this.wuPalmerConSimCombinations, other.wuPalmerConSimCombinations)
        && Arrays.equals(this.shareSynset, other.shareSynset)
        && Arrays.equals(this.shareSynsetCombinations, other.shareSynsetCombinations)
        && Arrays.equals(this.sameWord, other.sameWord)
        && Arrays.equals(this.sameWordCombinations, other.sameWordCombinations)
        && Arrays.equals(this.sameStem, other.sameStem)
        && Arrays.equals(this.sameStemCombinations, other.sameStemCombinations)
        && Objects.equal(this.sourceSectorOverlap, other.sourceSectorOverlap)
        && Objects.equal(this.targetSectorOverlap, other.targetSectorOverlap);
  }

  @Override
  public String toString() {
    return MoreObjects.toStringHelper(this)
        .add("id", id)
        .add("wuPalmerConSim", wuPalmerConSim)
        .add("wuPalmerConSimCombinations", wuPalmerConSimCombinations)
        .add("shareSynset", shareSynset)
        .add("shareSynsetCombinations", shareSynsetCombinations)
        .add("sameWord", sameWord)
        .add("sameWordCombinations", sameWordCombinations)
        .add("sameStem", sameStem)
        .add("sameStemCombinations", sameStemCombinations)
        .add("sourceSectorOverlap", sourceSectorOverlap)
        .add("targetSectorOverlap", targetSectorOverlap)
        .toString();
  }
}
