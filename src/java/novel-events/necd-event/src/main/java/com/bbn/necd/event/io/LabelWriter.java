package com.bbn.necd.event.io;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.necd.event.features.ProcessedEvent;
import com.google.common.base.Optional;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVPrinter;

import java.io.Closeable;
import java.io.File;
import java.io.IOException;

import static com.bbn.necd.event.io.CompressedFileUtils.openBufferedCompressedReader;
import static com.bbn.necd.event.io.CompressedFileUtils.openBufferedCompressedWriter;

/**
 * Writes labels for event pairs to a compressed CSV file.
 */
public final class LabelWriter implements Closeable {

  private static final CSVFormat FORMAT = CSVFormat.TDF;
  private static final String[] HEADER = new String[]{"Id1", "Id2", "Code1", "Code2", "SameCode"};

  private final CSVPrinter labelWriter;

  private LabelWriter(final CSVPrinter labelWriter) {
    this.labelWriter = labelWriter;
  }

  /**
   * Creates a new writer.
   * @param labelFile the file to write out labels to
   * @return the writer
   * @throws IOException if the file cannot be opened
   */
  public static LabelWriter create(final File labelFile) throws IOException {
    final CSVPrinter writer =
        new CSVPrinter(openBufferedCompressedWriter(labelFile), FORMAT.withHeader(HEADER));
    return new LabelWriter(writer);
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
   * Writes out the label for the specified events.
   * @param event1 the first event
   * @param event2 the second event
   * @throws IOException if the label could not be written
   */
  public void writeEventPair(final ProcessedEvent event1, final ProcessedEvent event2)
      throws IOException {
    // Write out label if it exists
    final Optional<Symbol> optEventCode1 = event1.getEventCode();
    final Optional<Symbol> optEventCode2 = event2.getEventCode();
    if (optEventCode1.isPresent() && optEventCode2.isPresent()) {
      final boolean sameCode = optEventCode1.get().equalTo(optEventCode2.get());
      labelWriter.printRecord(event1.getId().asString(), event2.getId().asString(),
          optEventCode1.get().asString(), optEventCode2.get().asString(), Boolean.toString(sameCode));
    }
  }

  public void writeIdPair(final Symbol id1, final Symbol id2, final Symbol code1,
      final Symbol code2) throws IOException {
    final boolean sameCode = code1.equalTo(code2);
    labelWriter.printRecord(id1.asString(), id2.asString(), code1.asString(), code2.asString(),
        Boolean.toString(sameCode));
  }

  /**
   * Closes the writer, flushing all data.
   * @throws IOException if the label file could not be closed
   */
  @Override
  public void close() throws IOException {
    labelWriter.close();
  }
}
