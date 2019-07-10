package com.bbn.necd.event;

import com.bbn.bue.common.serialization.jackson.JacksonSerializer;
import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventPairFeatures;
import com.bbn.necd.event.propositions.EventFilter;
import com.bbn.necd.event.propositions.PropositionPredicateType;
import com.bbn.nlp.banks.wordnet.WordNetPOS;

import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;

import org.junit.Test;

import java.io.IOException;

import static org.junit.Assert.assertEquals;

/**
 * Test serialization of event structures.
 */
public final class SerializationTest {

  @Test
  public void testEventFeatures() throws IOException {
    /*
    final EventFeatures expected = EventFeatures.create(Symbol.from("id"), Optional.of(Symbol.from("10")),
        PropositionPredicateType.NOUN, EventFilter.ALL, ImmutableList.of(Symbol.from("tacos")),
        ImmutableList.of(Symbol.from("taco")), ImmutableList.of(WordNetPOS.NOUN), ImmutableList.of(5), ImmutableList.of(Symbol.from("food")),
        ImmutableList.of(Symbol.from("dinner")), ImmutableList.of(Symbol.from("burrito")),
        ImmutableList.of(Symbol.from("enchilada")), Symbol.from("docId"), 1);
    */

    final EventFeatures.Builder eventFeaturesBuilder = EventFeatures.builder(Symbol.from("id"),
        Optional.of(Symbol.from("10")), PropositionPredicateType.NOUN, EventFilter.ALL,
        Symbol.from("docId"), 1);

    eventFeaturesBuilder.withPredicates(ImmutableList.of(Symbol.from("tacos")));
    eventFeaturesBuilder.withStems(ImmutableList.of(Symbol.from("taco")));
    eventFeaturesBuilder.withPos(ImmutableList.of(WordNetPOS.NOUN));
    eventFeaturesBuilder.withPredicateTokenIndices(ImmutableList.of(5));
    eventFeaturesBuilder.withSourceSectors(ImmutableSet.of(Symbol.from("food")));
    eventFeaturesBuilder.withTargetSectors(ImmutableSet.of(Symbol.from("dinner")));
    eventFeaturesBuilder.withSourceTokens(ImmutableList.of(Symbol.from("burrito")));
    eventFeaturesBuilder.withTargetTokens(ImmutableList.of(Symbol.from("enchilada")));
    //PropositionTreeFeatures.addFeatures(event, eventFeaturesBuilder);

    final EventFeatures expected = eventFeaturesBuilder.build();

    roundTrip(expected, EventFeatures.class);
  }

  @Test
  public void testEventPairFeatures() throws IOException {
    final EventPairFeatures expected = EventPairFeatures.create(Symbol.from("id"),
        ImmutableList.of(false, false), ImmutableList.of(false, false, false, false),
        ImmutableList.of(false, true), ImmutableList.of(false, false, false, true),
        ImmutableList.of(true, false), ImmutableList.of(false, false, true, false),
        ImmutableList.of(0.0, 1.0), ImmutableList.of(0.0, 0.25, 0.5, 1.0),
        0.1, 0.2);
    roundTrip(expected, EventPairFeatures.class);
  }

  private static <T> void roundTrip(T obj, Class<T> clazz) throws IOException {
    final JacksonSerializer serializer = JacksonSerializer.builder().prettyOutput().build();
    final String serialized = serializer.writeValueAsString(obj);
    final T actual = serializer.deserializeFromString(serialized, clazz);
    assertEquals(obj, actual);
  }
}
