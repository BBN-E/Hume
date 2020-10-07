package com.bbn.serif.util.place;

import com.bbn.bue.common.StringUtils;
import com.bbn.bue.geonames.GeoNames;
import com.bbn.bue.geonames.GeonamesException;
import com.bbn.bue.geonames.LocationRecord;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableMultimap;
import com.google.common.collect.ImmutableSet;

import java.util.Locale;


public final class PlaceContainmentUtils {

  private PlaceContainmentUtils() {
    throw new UnsupportedOperationException();
  }

  // find all GeoNames location records (at least population of 1) for a particular string
  public static ImmutableSet<LocationRecord> findPopulatedLocationRecords(final GeoNames geoNames,
      final String name) throws GeonamesException {
    final ImmutableSet.Builder<LocationRecord> ret = ImmutableSet.builder();

    final ImmutableSet<LocationRecord> locationRecords =
        geoNames.locationRecordsForNameString(name);
    for (final LocationRecord record : locationRecords) {
      if (record.population() > 0) {
        ret.add(record);
      }
    }

    return ret.build();
  }

  public static GeonamesHierarchy extractGeonamesHierarchy(final LocationRecord record) {
    final String name = record.name().toLowerCase(Locale.ENGLISH);
    final Optional<String> admin2 = record.admin2().transform(StringUtils.toLowerCaseFunction(Locale.ENGLISH));
    final Optional<String> admin1 = record.admin1().transform(StringUtils.toLowerCaseFunction(Locale.ENGLISH));
    final Optional<String> country = record.country().transform(StringUtils.toLowerCaseFunction(Locale.ENGLISH));

    return new GeonamesHierarchy.Builder().name(name).geoNameAdmin2(admin2).geoNameAdmin1(admin1)
        .geoNameCountry(country.get()).build();

  }

  // Each place can be associated with multiple geonames records. We extract all of them, and form them into GeonamesHierachy
  public static ImmutableSet<GeonamesHierarchy> extractGeonamesHierarchies(final String place,
      final GeoNames geoNames) throws GeonamesException {
    final ImmutableSet.Builder<GeonamesHierarchy> ret = ImmutableSet.builder();

    final ImmutableSet<LocationRecord> locationRecords = findPopulatedLocationRecords(geoNames, place);

    for(final LocationRecord locationRecord : locationRecords) {
      if(locationRecord.country().isPresent()) {
        ret.add(extractGeonamesHierarchy(locationRecord));
      }
    }

    return ret.build();
  }

  // for each Location-record: [name, admin1, admin2, country] , we obtain the following containment relations
  // name -in- admin1
  // name -in- admin2
  // name -in- country
  // admin2 -in- admin1
  // admin2 -in- country
  // admin1 -in- country
  public static ImmutableMultimap<String, String> constructPlaceContainmentMap(final LocationRecord record) {
    final ImmutableMultimap.Builder<String, String> ret = ImmutableMultimap.builder();

    final String name = record.name().toLowerCase(Locale.ENGLISH);
    final Optional<String> admin2 = record.admin2().transform(StringUtils.toLowerCaseFunction(Locale.ENGLISH));
    final Optional<String> admin1 = record.admin1().transform(StringUtils.toLowerCaseFunction(Locale.ENGLISH));
    final Optional<String> country = record.country().transform(StringUtils.toLowerCaseFunction(Locale.ENGLISH));

    if(admin1.isPresent()) {
      if(!name.equals(admin1.get())) {
        ret.put(name, admin1.get());
      }
      if(country.isPresent() && !country.get().equals(admin1.get())) {
        ret.put(admin1.get(), country.get());
      }
    }
    if(admin2.isPresent()) {
      if(!name.equals(admin2.get())) {
        ret.put(name, admin2.get());
      }
      if(admin1.isPresent() && !admin1.get().equals(admin2.get())) {
        ret.put(admin2.get(), admin1.get());
      }
      if(country.isPresent() && !country.get().equals(admin2.get())) {
        ret.put(admin2.get(), country.get());
      }
    }
    if(country.isPresent()) {
      if(!name.equals(country.get())) {
        ret.put(name, country.get());
      }
    }

    return ret.build();
  }

}
