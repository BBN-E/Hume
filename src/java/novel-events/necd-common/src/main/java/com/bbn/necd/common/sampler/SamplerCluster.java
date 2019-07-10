package com.bbn.necd.common.sampler;

import com.bbn.bue.common.symbols.Symbol;

import com.google.common.base.Function;
import com.google.common.collect.ImmutableSet;

/**
 * Created by ychan on 1/12/16.
 */
public final class SamplerCluster {
  private final Symbol label;             // e.g. event code. We could have kept this also in some external multimap, but there's no harm in being self sufficient
  private final ImmutableSet<Symbol> ids; // e.g. all instance ids of that event code

  private SamplerCluster(final Symbol label, final ImmutableSet<Symbol> ids) {
    this.label = label;
    this.ids = ids;
  }

  public Symbol getLabel() {
    return label;
  }

  public ImmutableSet<Symbol> getIds() {
    return ids;
  }

  public static Builder builder(final Symbol label) {
    return new Builder(label);
  }

  public static class Builder {
    private final Symbol label;
    private final ImmutableSet.Builder<Symbol> idsBuilder;

    private Builder(final Symbol label) {
      this.label = label;
      this.idsBuilder = ImmutableSet.builder();
    }

    public Builder withId(final Symbol id) {
      idsBuilder.add(id);
      return this;
    }

    public Builder withIds(final ImmutableSet<Symbol> ids) {
      idsBuilder.addAll(ids);
      return this;
    }

    public SamplerCluster build() {
      return new SamplerCluster(label, idsBuilder.build());
    }
  }

  public static final Function<SamplerCluster, Integer> SIZE =
      new Function<SamplerCluster, Integer>() {
        @Override
        public Integer apply(final SamplerCluster cluster) {
          return cluster.getIds().size();
        }
      };
}
