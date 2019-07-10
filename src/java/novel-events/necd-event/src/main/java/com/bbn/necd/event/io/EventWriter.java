package com.bbn.necd.event.io;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.EventFeatures;
import com.bbn.necd.event.features.EventPairFeatures;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.Sets;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;

import java.io.Closeable;
import java.io.File;
import java.io.IOException;
import java.util.Set;

import static com.bbn.necd.event.io.CompressedFileUtils.openBufferedCompressedReader;
import static com.bbn.necd.event.io.CompressedFileUtils.readAsJsonList;

/**
 * Writes events and event pairs features to a compressed CSV file.
 */
public final class EventWriter implements Closeable {

  private static final CSVFormat FORMAT = CSVFormat.TDF;
  private static final String[] EVENT_HEADER = new String[]{"Id", "Feature", "Value"};
  private static final String[] PAIR_HEADER = new String[]{"Id1", "Id2", "Feature", "Value"};

  private final ImmutableList.Builder<EventFeatures> events;
  private final ImmutableList.Builder<EventPairFeatures> eventPairs;
  private final Set<Symbol> writtenEventIds;
  private final File eventFile;
  private final File eventPairFile;

  private EventWriter(File eventFile, File eventPairFile) {
    this.eventFile = eventFile;
    this.eventPairFile = eventPairFile;
    this.writtenEventIds = Sets.newHashSet();
    events = ImmutableList.builder();
    eventPairs = ImmutableList.builder();
  }

  /**
   * Creates a new writer.
   *
   * @param eventFile the file to write event features to
   * @param eventPairFile the file to write event pair features to
   * @return the writer
   */
  public static EventWriter create(final File eventFile, final File eventPairFile) {
    return new EventWriter(eventFile, eventPairFile);
  }

  /**
   * Returns a parser that can read output created by this writer.
   *
   * @param file the file to read from
   * @return the parser
   * @throws IOException if the file cannot be opened
   * @deprecated Use {@link #readEvents(File)} and {@link #readEventPairs(File)}
   */
  @Deprecated
  public static CSVParser getParser(final File file) throws IOException {
    return new CSVParser(openBufferedCompressedReader(file), FORMAT.withHeader());
  }

  /**
   * Read serialized events from a file.
   */
  public static ImmutableList<EventFeatures> readEvents(final File file) throws IOException {
    return readAsJsonList(file, EventFeatures.class);
  }

  /**
   * Read serialized event pairs from a file.
   */
  public static ImmutableList<EventPairFeatures> readEventPairs(final File file) throws IOException {
    return readAsJsonList(file, EventPairFeatures.class);
  }

  /**
   * Stores the features for an individual event for future writing, if it has not already been stored.
   *
   * @param event the event
   */
  public void addIfNeeded(final EventFeatures event) {
    // If we haven't written this out before, write out all the features
    final Symbol id = event.id();
    if (!writtenEventIds.contains(id)) {
      events.add(event);
      // Record that we wrote it out
      writtenEventIds.add(id);
    }
  }

  /**
   * Stores the features for an event pair for future writing.
   *
   * @param features the event pair features
   */
  public void add(final EventPairFeatures features) {
    eventPairs.add(features);
  }

  /**
   * Writes out the events to files
   *
   * @throws IOException if the files cannot be written to or closed
   */
  @Override
  public void close() throws IOException {
    CompressedFileUtils.writeAsJson(events.build(), eventFile);
    CompressedFileUtils.writeAsJson(eventPairs.build(), eventPairFile);
  }
}
