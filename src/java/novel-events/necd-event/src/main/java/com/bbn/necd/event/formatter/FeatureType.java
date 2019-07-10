package com.bbn.necd.event.formatter;

import com.google.common.base.Function;
import com.google.common.base.Objects;
import com.google.common.collect.ImmutableSet;

/**
 * Created by ychan on 2/4/16.
 */
public final class FeatureType {
  private final String type;      // feature type, e.g. Lex:StemIdentity0
  private final ImmutableSet<String> values;

  private FeatureType(final String type, final ImmutableSet<String> values) {
    this.type = type;
    this.values = values;
  }

  public String getType() {
    return type;
  }

  public ImmutableSet<String> getValues() {
    return values;
  }

  public static Builder builder(final String type) {
    return new Builder(type);
  }

  public static final class Builder {
    private final String type;
    private final ImmutableSet.Builder<String> values;

    private Builder(final String type) {
      this.type = type;
      this.values = ImmutableSet.builder();
    }

    public Builder withValue(final String value) {
      values.add(value);
      return this;
    }

    public FeatureType build() {
      return new FeatureType(type, values.build());
    }
  }

  public String toString() {
    final StringBuilder sb = new StringBuilder(type + ": [");

    int valueIndex = 0;
    for (final String v : values) {
      if (valueIndex > 0) {
        sb.append(",");
      }
      sb.append(v);
      valueIndex += 1;
    }
    sb.append("]");

    return sb.toString();
  }

  @Override
  public int hashCode() {
    return Objects.hashCode(type, values);
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
    final FeatureType other = (FeatureType) obj;
    return Objects.equal(type, other.type) &&
        Objects.equal(values, other.values);
  }

  public static final Function<FeatureType, ImmutableSet<String>> VALUES =
      new Function<FeatureType, ImmutableSet<String>>() {
        @Override
        public ImmutableSet<String> apply(final FeatureType featureType) {
          return featureType.getValues();
        }
      };

}
