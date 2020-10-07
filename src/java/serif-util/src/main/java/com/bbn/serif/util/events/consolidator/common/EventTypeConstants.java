package com.bbn.serif.util.events.consolidator.common;

import com.google.common.collect.Sets;

import java.util.Set;

/**
 * Created by ychan on 8/29/19.
 */
public final class EventTypeConstants {
  public static String EVENT = new String("Event");
  public static String FACTOR_PLACEHOLDER = new String("_factor_");
  public static String QUOTATION = new String("Quotation");

  public static String ANTI_RETROVIRAL_TREATMENT = new String("AntiRetroviralTreatment");
  public static String THERAPEUTIC_FEEDING_OR_TREATING = new String("TherapeuticFeedingOrTreating");
  public static String SEXUAL_VIOLENCE_MANAGEMENT = new String("SexualViolenceManagement");
  public static String VECTOR_CONTROL = new String("VectorControl");
  public static String CAPACITY_BUILDING_HUMAN_RIGHTS = new String("CapacityBuildingHumanRights");
  public static String CHILD_FRIENDLY_LEARNING_SPACES = new String("ChildFriendlyLearningSpaces");
  public static String PROVIDE_HUMANITARIAN_RESOURCES = new String("provide_humanitarian_resources");
  public static String PROVIDE_HYGIENE_TOOL = new String("ProvideHygieneTool");
  public static String PROVIDE_FARMING_TOOL = new String("ProvideFarmingTool");
  public static String PROVIDE_DELIVERY_KIT = new String("ProvideDeliveryKit");
  public static String PROVIDE_LIVESTOCK_FEED = new String("ProvideLivestockFeed");
  public static String PROVIDE_VETERINARY_SERVICE = new String("ProvideVeterinaryService");
  public static String PROVIDE_FISHING_TOOL = new String("ProvideFishingTool");
  public static String PROVIDE_STATIONARY = new String("ProvideStationary");
  public static String PROVIDE_CASH = new String("ProvideCash");
  public static String PROVIDE_FOOD = new String("ProvideFood");
  public static String PROVIDE_SEED = new String("ProvideSeed");
  public static String HUMAN_DISPLACEMENT = new String("HumanDisplacement");
  public static String MOVEMENT = new String("Movement");

  Set<String> wmEventTypes =
      Sets.newHashSet(ANTI_RETROVIRAL_TREATMENT, THERAPEUTIC_FEEDING_OR_TREATING,
          SEXUAL_VIOLENCE_MANAGEMENT, VECTOR_CONTROL, CAPACITY_BUILDING_HUMAN_RIGHTS, CHILD_FRIENDLY_LEARNING_SPACES,
          PROVIDE_HUMANITARIAN_RESOURCES, PROVIDE_HYGIENE_TOOL, PROVIDE_FARMING_TOOL, PROVIDE_DELIVERY_KIT,
          PROVIDE_LIVESTOCK_FEED, PROVIDE_VETERINARY_SERVICE, PROVIDE_FISHING_TOOL, PROVIDE_STATIONARY,
          PROVIDE_CASH, PROVIDE_FOOD, PROVIDE_SEED, HUMAN_DISPLACEMENT, MOVEMENT);
}
