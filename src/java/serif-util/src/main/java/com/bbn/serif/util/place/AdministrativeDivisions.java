package com.bbn.serif.util.place;

import com.bbn.bue.common.TextGroupImmutable;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.google.common.base.Optional;
import com.google.common.base.Preconditions;

import org.immutables.func.Functional;
import org.immutables.value.Value;

/**
 * Admin divisions increase in specificity in the following order admin1,admin2,admin3,admin4 If a
 * particular abmin division is absent, all the following more specific ones will be absent too
 */
@Value.Immutable(prehash = true)
@Functional
@TextGroupImmutable
@JsonSerialize
@JsonDeserialize
public abstract class AdministrativeDivisions {

  @Value.Parameter
  public abstract Long geoID();

  @Value.Parameter
  public abstract String countryCode();

  @Value.Parameter
  public abstract Optional<String> admin1();

  @Value.Parameter
  public abstract Optional<String> admin2();

  @Value.Parameter
  public abstract Optional<String> admin3();

  @Value.Parameter
  public abstract Optional<String> admin4();

  @Value.Check
  protected void check() {
    Preconditions.checkState(
        (!admin1().isPresent() && !admin2().isPresent() && !admin3().isPresent() && !admin4()
            .isPresent()) ||
            (admin1().isPresent() && !admin2().isPresent() && !admin3().isPresent() && !admin4()
                .isPresent()) ||
            (admin1().isPresent() && admin2().isPresent() && !admin3().isPresent() && !admin4()
                .isPresent()) ||
            (admin1().isPresent() && admin2().isPresent() && admin3().isPresent() && !admin4()
                .isPresent()) ||
            (admin1().isPresent() && admin2().isPresent() && admin3().isPresent() && admin4()
                .isPresent()));
  }

  public static final class Builder extends ImmutableAdministrativeDivisions.Builder {

  }
}
