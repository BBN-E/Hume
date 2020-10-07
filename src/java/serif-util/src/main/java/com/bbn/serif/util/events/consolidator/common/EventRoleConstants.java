package com.bbn.serif.util.events.consolidator.common;


import com.google.common.collect.Sets;

import java.util.Set;

public final class EventRoleConstants {
  public static String HAS_ACTOR = new String("has_actor");
  public static String HAS_ACTIVE_ACTOR = new String("has_active_actor");
  public static String HAS_AFFECTED_ACTOR = new String("has_affected_actor");
  public static String HAS_LOCATION = new String("has_location");
  public static String HAS_ORIGIN_LOCATION = new String("has_origin_location");
  public static String HAS_DESTINATION_LOCATION = new String("has_destination_location");
  public static String HAS_INTERMEDIATE_LOCATION = new String("has_intermediate_location");
  public static String HAS_ARTIFACT = new String("has_artifact");
  public static String HAS_THEME = new String("has_theme");
  public static String HAS_PROPERTY = new String("has_property");
  public static String HAS_TIME = new String("has_time");
  public static String HAS_START_TIME = new String("has_start_time");
  public static String HAS_END_TIME = new String("has_end_time");
  public static String HAS_DURATION = new String("has_duration");

  Set<String> eventRoles =
      Sets.newHashSet(HAS_ACTOR, HAS_ACTIVE_ACTOR, HAS_AFFECTED_ACTOR, HAS_LOCATION,
          HAS_ORIGIN_LOCATION, HAS_DESTINATION_LOCATION, HAS_INTERMEDIATE_LOCATION, HAS_ARTIFACT,
          HAS_PROPERTY, HAS_THEME, HAS_TIME, HAS_START_TIME, HAS_END_TIME, HAS_DURATION);
}
