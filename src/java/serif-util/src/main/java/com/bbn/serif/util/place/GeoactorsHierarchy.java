package com.bbn.serif.util.place;

import com.bbn.bue.common.TextGroupImmutable;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.google.common.base.Optional;

import org.immutables.func.Functional;
import org.immutables.value.Value;

/**
 * If we can find a GeoResolvedActor from a given ActorEntity, we will instantiate this. A
 * GeoResolvedActor will have a geoCountry, but might not have a geoID. If it has a geoID, then we
 * can use it to find AdministrativeDivisions I believe if the AdministrativeDivisions.countryCode
 * is present, it will be the same as geoCountry.
 */
@Value.Immutable(prehash = true)
@Functional
@TextGroupImmutable
@JsonSerialize(as = ImmutableGeoactorsHierarchy.class)
@JsonDeserialize(as = ImmutableGeoactorsHierarchy.class)
public abstract class GeoactorsHierarchy {

  @Value.Parameter
  public abstract String geoCountry();

  @Value.Parameter
  public abstract Optional<AdministrativeDivisions> administrativeDivisions();

  public static final class Builder extends ImmutableGeoactorsHierarchy.Builder {

  }
}
