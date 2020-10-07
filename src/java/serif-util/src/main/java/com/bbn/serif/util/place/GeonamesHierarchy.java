package com.bbn.serif.util.place;

import com.bbn.bue.common.TextGroupImmutable;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.google.common.base.Optional;

import org.immutables.func.Functional;
import org.immutables.value.Value;

/**
 * There are 4 levels in the geoNames DB: (name, admin2, admin1, country). admin2 is a sub-division
 * of admin-1. The parents are admin2, admin1, country
 */
@Value.Immutable(prehash = true)
@Functional
@TextGroupImmutable
@JsonSerialize(as = ImmutableGeonamesHierarchy.class)
@JsonDeserialize(as = ImmutableGeonamesHierarchy.class)
public abstract class GeonamesHierarchy {

  /**
   * This is what you use to query the Geonames DB. Querying always goes up. For instance, if you
   * query using 'boston' (which is ambiguous), you get all records: name=BOSTON ,
   * admin2=LINCOLNSHIRE , admin1=ENGLAND , country=UNITED KINGDOM name=BOSTON , admin2=SUFFOLK
   * COUNTY , admin1=MASSACHUSETTS , country=UNITED STATES ... and so on ...
   *
   * Buf if you query using 'massachusetts', which is unambiguous, you get: name=MASSACHUSETTS ,
   * admin2=NULL , admin1=MASSACHUSETTS , country=UNITED STATES
   *
   * So, one should not consider 'name' to be in the hierarchy.
   */
  @Value.Parameter
  public abstract String name();

  /**
   * geoNameAdmin1 might not always be present when geoNameAdmin2 is present, e.g.: name=LOS
   * ANGELES, admin1=NULL, admin2=BUTUAN CITY, country=PHILIPPINES
   */
  @Value.Parameter
  public abstract Optional<String> geoNameAdmin2();

  @Value.Parameter
  public abstract Optional<String> geoNameAdmin1();

  /**
   * We enforce the constraint that we must always have a country. In some rare cases, records
   * within the DB do violate this, e.g. name=KOSOVO, admin1=KOSOVO POLJE, admin2=NULL, country=NULL
   * We will simply ignore such records
   */
  @Value.Parameter
  public abstract String geoNameCountry();

  public static final class Builder extends ImmutableGeonamesHierarchy.Builder {

  }
}
