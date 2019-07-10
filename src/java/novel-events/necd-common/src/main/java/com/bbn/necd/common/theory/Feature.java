package com.bbn.necd.common.theory;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.collect.BiMap;
import com.google.common.collect.HashMultiset;
import com.google.common.collect.ImmutableTable;
import com.google.common.collect.Multiset;
import com.google.common.collect.Table;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Created by ychan on 4/18/16.
 */
public class Feature {
  private final String featureName;
  private final BiMap<String, Integer> featureIndices;
  private final int startIndex;
  private final int endIndex;

  protected Feature(final String featureName,
      final BiMap<String, Integer> featureIndices, final int startIndex, final int endIndex) {
    this.featureName = checkNotNull(featureName);
    this.featureIndices = featureIndices;
    this.startIndex = startIndex;
    this.endIndex = endIndex;
  }

  public String getFeatureName() {
    return featureName;
  }

  public int getStartIndex() {
    return startIndex;
  }

  public int getEndIndex() {
    return endIndex;
  }

  public BiMap<String, Integer> getFeatureStringToIndex() {
    return featureIndices;
  }

  public BiMap<Integer, String> getFeatureIndexToString() {
    return featureIndices.inverse();
  }

  public boolean hasFeatureValue() {
    return (featureIndices.size() > 0)? true: false;
  }

  public static Multiset<String> getFeatureCount(final ImmutableTable<Symbol, String, Double> featuresCache) {
    final Multiset<String> ret = HashMultiset.create();

    for(final Table.Cell<Symbol, String, Double> cell : featuresCache.cellSet()) {
      ret.add(cell.getColumnKey());
    }

    return ret;
  }

  public final static String DELIMITER = ":";
}
