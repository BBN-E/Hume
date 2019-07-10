package com.bbn.necd.event.io;

import com.bbn.bue.common.io.GZIPByteSink;
import com.bbn.bue.common.io.GZIPByteSource;
import com.bbn.bue.common.serialization.jackson.JacksonSerializer;
import com.google.common.base.Charsets;
import com.google.common.collect.ImmutableList;
import com.google.common.io.ByteSink;
import com.google.common.io.ByteSource;
import com.google.common.io.Files;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.Writer;

/**
 * Provides utilities for reading from and writing to compressed files.
 */
public final class CompressedFileUtils {

  /**
   * Writes an object to a file as gzipped Smile-format JSON.
   *
   * @param object the object to write
   * @param file the file to write to
   * @throws IOException if the file could not be written to
   */
  public static void writeAsJson(final Object object, final File file) throws IOException {
    final ByteSink outputSink = GZIPByteSink.gzipCompress(Files.asByteSink(file));
    final JacksonSerializer serializer = JacksonSerializer.forSmile();
    serializer.serializeTo(object, outputSink);
  }

  /**
   * Reads a list from a gzipped smile-format JSON file, casting it appropriately. It is up the caller to ensure that the
   * file being read from represents a list written using {@link #writeAsJson(Object, File)} and that the
   * specified class is the correct class for its contents.
   *
   * @param file the file to read from
   * @param clazz the class of the list contents
   * @return a deserialized list from the file
   * @throws IOException if the file cannot be read
   */
  @SuppressWarnings("unchecked") // It's up to to the user to provide the correct class for the cast.
  public static <T> ImmutableList<T> readAsJsonList(final File file, final Class<T> clazz) throws IOException {
    final ByteSource eventsSource = GZIPByteSource.fromCompressed(file);
    final JacksonSerializer deserializer = JacksonSerializer.forSmile();
    return (ImmutableList<T>) deserializer.deserializeFrom(eventsSource);
  }

  /**
   * Opens a gzip-compressed buffered writer for the specified file.
   *
   * @param file the file to write to
   * @return a gzip-compressed buffered writer
   * @throws IOException if the file cannot be opened
   */
  public static Writer openBufferedCompressedWriter(final File file) throws IOException {
    return GZIPByteSink.gzipCompress(Files.asByteSink(file)).asCharSink(Charsets.UTF_8).openBufferedStream();
  }

  /**
   * Opens a gzip-compressed buffered reader for the specified file.
   *
   * @param file the file to read from
   * @return a gzip-decompressed buffered reader
   * @throws IOException if the file cannot be opened
   */
  public static BufferedReader openBufferedCompressedReader(final File file) throws IOException {
    return GZIPByteSource.fromCompressed(Files.asByteSource(file)).asCharSource(Charsets.UTF_8).openBufferedStream();
  }
}
