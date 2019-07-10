package com.bbn.necd.event.bin;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Created by ychan on 8/8/16.
 */
public final class GeoNames {
  private static final Logger log = LoggerFactory.getLogger(GeoNames.class);

  private final Connection connection;

  private GeoNames(Connection connection) throws GeonamesException {
    try {
      checkArgument(!connection.isClosed());
    } catch (SQLException e) {
      throw new GeonamesException("Error during initialization", e);
    }
    this.connection = checkNotNull(connection);
  }

  public static GeoNames connectToGeonamesDB(File dbFile) throws GeonamesException {
    log.info("Connecting to GeoNames database stored in {}", dbFile);
    try {
      log.info("Loading JDBC driver");
      Class.forName("org.sqlite.JDBC");
    } catch (ClassNotFoundException e) {
      throw new GeonamesException("Could not load JDBC driver", e);
    }

    Connection connection = null;
    try {
      connection = DriverManager.getConnection("jdbc:sqlite:" + dbFile.getAbsolutePath());
      return new GeoNames(connection);
    } catch (SQLException e) {
      throw new GeonamesException("Error establishing connection", e);
    }
  }

  public void locationRecordsForNameString(String name)
      throws GeonamesException {
    log.info("Looking up location records for {} in GeoNames", name);
    name = name.toUpperCase();



    try {
      final PreparedStatement statement =
          connection.prepareStatement("select admin1,admin2,country,population from locations "
              + "inner join names on locations.gid=names.gid where names.name=?");
      statement.setString(1, name);
      final ResultSet resultSet = statement.executeQuery();


/*
      final ImmutableSet.Builder<LocationRecord> ret = ImmutableSet.builder();
      while (resultSet.next()) {
        ret.add(LocationRecord.from(name, deduplicate(resultSet.getString("admin1")),
            deduplicate(resultSet.getString("admin2")), resultSet.getString("country"),
            resultSet.getInt("population")));
      }
      return ret.build();
      */
    } catch (SQLException e) {
      throw new GeonamesException("Lookup of location records for " + name + " failed", e);
    }
  }

  // TODO: all the admin1 and admin2 values I've seen have been of the form
  // x,x . I'm sure some must be different, but I'm coding this up the
  // night before an eval freeze, so I'm just going to strip everything
  // after the first comma for now. If this code gets used elsewhere, this
  // should be fixed
  private static String deduplicate(String s) {
    final int commaIdx = s.indexOf(",");
    if (commaIdx >= 0) {
      return s.substring(0, commaIdx);
    } else {
      return s;
    }
  }

  public void disconnect() {
    try {
      connection.close();
    } catch (SQLException e) {
      log.error("Exception on disconnection: {}", e);
    }
  }
}
