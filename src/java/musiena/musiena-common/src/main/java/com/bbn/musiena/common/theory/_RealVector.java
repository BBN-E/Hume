package com.bbn.musiena.common.theory;

import com.bbn.bue.common.TextGroupPublicImmutable;

import org.immutables.func.Functional;
import org.immutables.value.Value;

@Value.Immutable(prehash = true)
@Functional
@TextGroupPublicImmutable
public abstract class _RealVector {
  @Value.Parameter
  public abstract String id();

  @Value.Parameter
  public abstract double[] vector();

}
