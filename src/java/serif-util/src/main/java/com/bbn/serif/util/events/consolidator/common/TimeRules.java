package com.bbn.serif.util.events.consolidator.common;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.EventMention;
import com.bbn.serif.util.events.consolidator.coreference.SieveConstants;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;

import java.util.Set;

public final class TimeRules {

  private TimeRules() {
    throw new UnsupportedOperationException();
  }


  public static boolean hasContainmentRelation(final ImmutableSet<EventMention.Argument> args1,
      final ImmutableSet<EventMention.Argument> args2) {
    // timexVal.isPresent() && isValidNormalizedDate: e.g. 2018, today, tomorrow, yesterday
    final ImmutableSet<EventMention.Argument> validArgs1 = getValidTimeArguments(args1);
    final ImmutableSet<EventMention.Argument> validArgs2 = getValidTimeArguments(args2);
    final ImmutableSet<NormalizedDate> dates1 = toNormalizedDates(validArgs1);
    final ImmutableSet<NormalizedDate> dates2 = toNormalizedDates(validArgs2);
    final boolean equalOnValidArgs = hasContainmentRelationOnDates(dates1, dates2);

    // // timexVal.isPresent() && !isValidNormalizedDate: e.g. current, future, modern, the past 75 years
    // these are argument such as: FUTURE_REF, PAST, etc.
    final ImmutableSet<EventMention.Argument> invalidArgs1 = getInvalidTimeArguments(args1);
    final ImmutableSet<EventMention.Argument> invalidArgs2 = getInvalidTimeArguments(args2);
    final boolean equalOnInvalidArgs = isEqualOnInvalidDates(invalidArgs1, invalidArgs2);

    final ImmutableSet<EventMention.Argument> nonTimexArgs1 = getNonTimexArguments(args1);
    final ImmutableSet<EventMention.Argument> nonTimexArgs2 = getNonTimexArguments(args2);
    final boolean equalOnNonTimex = isEqualOnText(nonTimexArgs1, nonTimexArgs2);

    final int a1 = validArgs1.size();
    final int a2 = invalidArgs1.size();
    final int a3 = nonTimexArgs1.size();

    final int b1 = validArgs2.size();
    final int b2 = invalidArgs2.size();
    final int b3 = nonTimexArgs2.size();

    if( (a1>0 && a2==0 && a3==0 && b1==0 && b2>0 && b3==0) ||   // 100 vs 010
        (a1>0 && a2==0 && a3==0 && b1==0 && b2==0 && b3>0) ||   // 100 vs 001
        (a1==0 && a2>0 && a3==0 && b1>0 && b2==0 && b3==0) ||   // 010 vs 100
        (a1==0 && a2>0 && a3==0 && b1==0 && b2==0 && b3>0) ||   // 010 vs 001
        (a1==0 && a2==0 && a3>0 && b1>0 && b2==0 && b3==0) ||   // 001 vs 100
        (a1==0 && a2==0 && a3>0 && b1==0 && b2>0 && b3==0) ||   // 001 vs 010
        (a1>0 && a2>0 && a3==0 && b1==0 && b2==0 && b3>0) ||    // 110 vs 001
        (a1==0 && a2>0 && a3>0 && b1>0 && b2==0 && b3==0) ||    // 011 vs 100
        (a1>0 && a2==0 && a3>0 && b1==0 && b2>0 && b3==0) ||    // 101 vs 010
        (a1==0 && a2==0 && a3>0 && b1>0 && b2>0 && b3==0) ||    // 001 vs 110
        (a1>0 && a2==0 && a3==0 && b1==0 && b2>0 && b3>0) ||    // 100 vs 011
        (a1==0 && a2>0 && a3==0 && b1>0 && b2==0 && b3>0) ) {   // 010 vs 101
      return false;
    } else {
      return equalOnValidArgs && equalOnInvalidArgs && equalOnNonTimex;
    }
  }

  private static boolean hasContainmentRelationOnDates(
      final ImmutableSet<NormalizedDate> dates1, final ImmutableSet<NormalizedDate> dates2) {
    for (final NormalizedDate date1 : dates1) {
      for (final NormalizedDate date2 : dates2) {
        if (!date1.contains(date2) && !date2.contains(date1)) {
          return false;
        }
      }
    }
    return true;
  }

  private static boolean isEqualOnText(final ImmutableSet<EventMention.Argument> args1, final ImmutableSet<EventMention.Argument> args2) {
    Set<String> time1 = Sets.newHashSet();
    Set<String> time2 = Sets.newHashSet();

    for(final EventMention.Argument arg : args1) {
      time1.add(arg.span().text().utf16CodeUnits().toString().toLowerCase());

    }
    for(final EventMention.Argument arg : args2) {
      time2.add(arg.span().text().utf16CodeUnits().toString().toLowerCase());
    }
    if(time1.size() > 0 && time2.size() > 0) {
      return time1.equals(time2);
    } else {
      return true;
    }
  }

  private static boolean isEqualOnInvalidDates(final ImmutableSet<EventMention.Argument> args1, final ImmutableSet<EventMention.Argument> args2) {
    Set<String> time1 = Sets.newHashSet();
    Set<String> time2 = Sets.newHashSet();

    for(final EventMention.Argument arg : args1) {
      time1.add(SieveUtils.getTimexVal(arg).get().asString().toLowerCase());
    }
    for(final EventMention.Argument arg : args2) {
      time2.add(SieveUtils.getTimexVal(arg).get().asString().toLowerCase());
    }
    if(time1.size() > 0 && time2.size() > 0) {
      return time1.equals(time2);
    } else {
      return true;
    }
  }

  // timexVal is present && isValidNormalizedDate
  private static ImmutableSet<EventMention.Argument> getValidTimeArguments(final ImmutableSet<EventMention.Argument> args) {
    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();

    for (final EventMention.Argument arg : args) {
      final Optional<Symbol> timexVal = SieveUtils.getTimexVal(arg);
      if(timexVal.isPresent() && isValidNormalizedDate(timexVal.get().asString())) {
        ret.add(arg);
      }
    }

    return ret.build();
  }

  // timexVal is present && !isValidNormalizedDate
  private static ImmutableSet<EventMention.Argument> getInvalidTimeArguments(final ImmutableSet<EventMention.Argument> args) {
    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();

    for (final EventMention.Argument arg : args) {
      final Optional<Symbol> timexVal = SieveUtils.getTimexVal(arg);
      if(timexVal.isPresent() && !isValidNormalizedDate(timexVal.get().asString())) {
        //System.out.println("getInvalidTimeArguments " + arg.span().text().utf16CodeUnits().toString() + " " + SieveUtils.getTimexVal(arg).get().asString().toLowerCase());
        ret.add(arg);
      }
    }

    return ret.build();
  }

  private static ImmutableSet<EventMention.Argument> getNonTimexArguments(final ImmutableSet<EventMention.Argument> args) {
    final ImmutableSet.Builder<EventMention.Argument> ret = ImmutableSet.builder();

    for (final EventMention.Argument arg : args) {
      final Optional<Symbol> timexVal = SieveUtils.getTimexVal(arg);
      if(!timexVal.isPresent()) {
        ret.add(arg);
      }
    }

    return ret.build();
  }


  /**
   * Returns all maximal subsets of the data arguments of the given event frame where
   * all elements in a subset, considered pairwise, have some containment relationship.
   */
  /*
  static ImmutableSet<ImmutableSet<SherlockEventArgument>> getMaximalConsistentSubsets(
      final SherlockDocumentEvent ef, int maxArgSetSize) {

    final ImmutableMultimap.Builder<NormalizedDate, SherlockEventArgument> dateToArgMapBuilder =
        ImmutableMultimap.builder();
    for (final SherlockEventArgument arg : getValidTimeArguments(ef)) {
      final NormalizedDate normDate = NormalizedDate.from(SherlockAccessor.getCAS(arg).string());
      dateToArgMapBuilder.put(normDate, arg);
    }
    final ImmutableMultimap<NormalizedDate, SherlockEventArgument> dateToArgMap =
        dateToArgMapBuilder.build();

    final Set<Set<NormalizedDate>> subsets =
        SieveUtils.nonEmptySubsetsSafely(dateToArgMap.asMap().keySet(),
            maxArgSetSize); // generate all subsets

    final ImmutableSet.Builder<ImmutableSet<NormalizedDate>> fullyContainedSubsetsBuilder =
        ImmutableSet.builder();
    for (final Set<NormalizedDate> set : subsets) {
      if (allTimesInPairwiseContainmentRelationships(set)) {
        fullyContainedSubsetsBuilder.add(ImmutableSet.copyOf(set));
      }
    }
    final ImmutableSet<ImmutableSet<NormalizedDate>> fullyContainedSubsets =
        SieveUtils.discardProperSubsets(fullyContainedSubsetsBuilder.build());

    final ImmutableSet.Builder<ImmutableSet<SherlockEventArgument>> ret = ImmutableSet.builder();
    for (final ImmutableSet<NormalizedDate> normDates : fullyContainedSubsets) {
      final ImmutableSet.Builder<SherlockEventArgument> argSetBuilder = ImmutableSet.builder();
      for (final NormalizedDate normDate : normDates) {
        argSetBuilder.addAll(dateToArgMap.get(normDate));
      }
      ret.add(argSetBuilder.build());
    }
    return ret.build();
  }

  private static boolean allTimesInPairwiseContainmentRelationships(
      final Set<NormalizedDate> set) {
    if (set.size() < 2) {    // singletons are always full contained
      return true;
    } else {
      final ImmutableList<NormalizedDate> elements = ImmutableList.copyOf(set);
      for (int i = 0; i < (elements.size() - 1); i++) {
        for (int j = (i + 1); j < elements.size(); j++) {
          if (!elements.get(i).contains(elements.get(j)) &&
              !elements.get(j).contains(elements.get(i))) {
            return false;
          }
        }
      }
      return true;
    }
  }
  */

  private static ImmutableSet<EventMention.Argument> getValidTimeArguments(final EventMention ef) {
    return getValidTimeArguments(ImmutableSet.copyOf(ef.argsForRole(SieveConstants.TIME)));
  }

  // pre-condition: args should contain only valid normalized dates
  /*
  private static ImmutableSet<NormalizedDate> toNormalizedDates(
      final ImmutableSet<SherlockEventArgument> args) {
    final ImmutableSet.Builder<NormalizedDate> ret = ImmutableSet.builder();

    for (final SherlockEventArgument arg : args) {
      ret.add(NormalizedDate.from(SherlockAccessor.getCAS(arg).string()));
    }

    return ret.build();
  }
  */

  // pre-condition: args should contain only valid normalized dates ; i.e. filtered by function getValidTimeArguments
  private static ImmutableSet<NormalizedDate> toNormalizedDates(final ImmutableSet<EventMention.Argument> args) {
    final ImmutableSet.Builder<NormalizedDate> ret = ImmutableSet.builder();
    for(final EventMention.Argument arg : args) {
      ret.add(NormalizedDate.from(SieveUtils.getTimexVal(arg).get().asString()));
    }
    return ret.build();
  }

  // check whether an input string is a valid normalized date , i.e. XXXX-XX-XX
  private static boolean isValidNormalizedDate(final String s) {
    final String[] tokens = s.split("-");

    if (tokens.length > 3) {
      return false;
    }

    final String yearString = tokens[0];
    final String monthString = tokens.length >= 2? tokens[1] : "XX";
    final String dayString = tokens.length >= 3? tokens[2] : "XX";

    return isValidYear(yearString) && isValidMonth(monthString) && isValidDay(dayString);
  }

  private static boolean isValidYear(final String s) {
    return s.equals("XXXX") || s.matches("^\\d+$");
  }

  private static boolean isValidMonth(final String s) {
    if (s.equals("XX")) {
      return true;
    } else {
      if (s.matches("^\\d+$")) {
        final int month = Integer.parseInt(s);
        return (1 <= month && month <= 12);
      } else {
        return false;
      }
    }
  }

  private static boolean isValidDay(final String s) {
    if (s.equals("XX")) {
      return true;
    } else {
      if (s.matches("^\\d+$")) {
        final int day = Integer.parseInt(s);
        return (1 <= day && day <= 31);
      } else {
        return false;
      }
    }
  }

  // TODO: this could be replaced by Timex2Time
  private static final class NormalizedDate {

    private final Optional<Integer> year;
    private final Optional<Integer> month;
    private final Optional<Integer> day;

    private NormalizedDate(final Integer year, final Integer month, final Integer day) {
      this.year = Optional.fromNullable(year);
      this.month = Optional.fromNullable(month);
      this.day = Optional.fromNullable(day);
    }

    // has to be in the form of XX-XX-XX , where each XX is an integer
    private static NormalizedDate from(final String dateString) {
      final String[] tokens = dateString.split("-");

      final Integer year = tokens[0].compareTo("XXXX") == 0 ? null : Integer.valueOf(tokens[0]);
      final Integer month = (tokens.length < 2 || tokens[1].compareTo("XX") == 0) ? null : Integer.valueOf(tokens[1]);
      final Integer day = (tokens.length < 3 || tokens[2].compareTo("XX") == 0) ? null : Integer.valueOf(tokens[2]);

      return new NormalizedDate(year, month, day);
    }

    private Optional<Integer> getYear() {
      return year;
    }

    private Optional<Integer> getMonth() {
      return month;
    }

    private Optional<Integer> getDay() {
      return day;
    }

    private boolean contains(final NormalizedDate other) {
      return elementContains(year, other.getYear())
          && elementContains(month, other.getMonth())
          && elementContains(day, other.getDay());
    }

    private boolean elementContains(final Optional<Integer> e1, final Optional<Integer> e2) {
      return (!e1.isPresent() && !e2.isPresent()) ||
          (!e1.isPresent() && e2.isPresent()) ||
          (e1.isPresent() && e2.isPresent() && e1.get().intValue() == e2.get().intValue());
    }

    public String toString() {
      String year = this.year.isPresent()? this.year.get().toString() : "XXXX";
      String month = this.month.isPresent()? this.month.get().toString() : "XX";
      String day = this.day.isPresent()? this.day.get().toString() : "XX";
      return month + "/" + day + "/" + year;
    }
  }
}
