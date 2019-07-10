package com.bbn.necd.event.formatter;

import com.google.common.base.Objects;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableCollection;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;

import java.util.Map;

/**
 * Created by ychan on 2/4/16.
 */
public final class InstanceFeatures {
  private final ImmutableMap<String, FeatureType> features; // featureType -> FeatureType

  private InstanceFeatures(final ImmutableMap<String, FeatureType> features) {
    this.features = features;
  }

  public Optional<FeatureType> getFeatureType(final String featureType) {
    return Optional.fromNullable(features.get(featureType));
  }

  public ImmutableCollection<FeatureType> getFeatureTypes() {
    return features.values();
  }

  public ImmutableSet<FeatureType> getFeatureTypesStartingWithPrefix(final String prefix) {
    final ImmutableSet.Builder<FeatureType> ret = ImmutableSet.builder();

    for(final FeatureType feature : features.values()) {
      if(feature.getType().startsWith(prefix)) {
        ret.add(feature);
      }
    }

    return ret.build();
  }

  public static ImmutableSet<StringPair> crossAllFeatureValues(final FeatureType feature1, final FeatureType feature2) {
    final ImmutableSet.Builder<StringPair> ret = ImmutableSet.builder();

    for(final String v1 : feature1.getValues()) {
      for(final String v2 : feature2.getValues()) {
        ret.add(StringPair.from(v1, v2));
      }
    }

    return ret.build();
  }

  public static Builder builder() {
    return new Builder();
  }

  public static final class Builder {
    private Map<String, FeatureType.Builder> features;

    private Builder() {
      this.features = Maps.newHashMap();
    }

    public Builder addFeatureValue(final String featureType, final String featureValue) {
      if (features.containsKey(featureType)) {
        features.get(featureType).withValue(featureValue);
      } else {
        features.put(featureType, FeatureType.builder(featureType).withValue(featureValue));
      }
      return this;
    }

    public InstanceFeatures build() {
      final ImmutableMap.Builder<String, FeatureType> feas = ImmutableMap.builder();
      for (final String featureType : Ordering.natural().immutableSortedCopy(features.keySet())) {
        feas.put(featureType, features.get(featureType).build());
      }
      return new InstanceFeatures(feas.build());
    }
  }

  public String toString() {
    final StringBuilder sb = new StringBuilder();

    for (final FeatureType f : features.values()) {
      sb.append(f.toString());
      sb.append("\n");
    }

    return sb.toString();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(features);
  }

  @Override
  public boolean equals(final Object obj) {
    if(this == obj) {
      return true;
    }
    if(obj == null) {
      return false;
    }
    if(getClass() != obj.getClass()) {
      return false;
    }
    final InstanceFeatures other = (InstanceFeatures) obj;
    return Objects.equal(features, other.features);
  }
}
