package com.bbn.necd.event.io;

import java.io.IOException;
import java.io.Writer;

import static com.bbn.bue.common.StringUtils.CommaJoiner;

// TODO: Remove this class

/**
 * Methods for writing crude delimited lines. Use {@link org.apache.commons.csv.CSVParser} and
 * {@link org.apache.commons.csv.CSVPrinter} instead.
 */
@Deprecated
public final class DelimUtils {

  public static void writeDelimRow(final Writer writer, final Object... objects) throws IOException {
    // This doesn't direct to the other implementation because the other one is not treated as more specific, resulting
    // in infinite recursion.
    writer.write(CommaJoiner.join(objects));
    writer.write("\n");
  }

  public static void writeDelimRow(final Writer writer, final Iterable<?> objects) throws IOException {
    writer.write(CommaJoiner.join(objects));
    writer.write("\n");
  }
}
