package com.bbn.necd.event.io;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVPrinter;

import java.io.Closeable;
import java.io.File;
import java.io.IOException;

import static com.bbn.necd.event.io.CompressedFileUtils.openBufferedCompressedReader;
import static com.bbn.necd.event.io.CompressedFileUtils.openBufferedCompressedWriter;

/**
 * Writes out events with a single label alongside the event. Could be make much more generic than it is.
 */
public final class LabeledIdWriter implements Closeable {

  public static final String HEADER_ID = "Id";
  public static final String HEADER_LABEL = "Label";

  private static final CSVFormat FORMAT = CSVFormat.TDF;
  private static final String[] HEADER = new String[]{HEADER_ID, HEADER_LABEL};

  private final CSVPrinter writer;

  private LabeledIdWriter(final CSVPrinter writer) {
    this.writer = writer;
  }

  /**
   * Creates a new writer.
   *
   * @param output the file to write out labels to
   * @return the writer
   * @throws IOException if the file cannot be opened
   */
  public static LabeledIdWriter create(final File output) throws IOException {
    final CSVPrinter writer =
        new CSVPrinter(openBufferedCompressedWriter(output), FORMAT.withHeader(HEADER));
    return new LabeledIdWriter(writer);
  }

  /**
   * Returns a parser for this format.
   * @param file the file to parse
   * @return the parser
   * @throws IOException if the file could not be opened
   */
  public static CSVParser getParser(final File file) throws IOException {
    return new CSVParser(openBufferedCompressedReader(file), FORMAT.withHeader());
  }

  /**
   * Writes out the label for the specified id.
   * @param id the event
   * @param label the label
   * @throws IOException if the label could not be written
   */
  public void writeLabel(final String id, final String label) throws IOException {
    writer.printRecord(id, label);
  }

  /**
   * Closes the writer, flushing all data.
   * @throws IOException if the label file could not be closed
   */
  @Override
  public void close() throws IOException {
    writer.close();
  }
}
