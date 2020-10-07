package com.bbn.serif.util.place;

import com.bbn.bue.geonames.GeonamesException;

import com.google.common.base.Optional;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.Closeable;
import java.io.File;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * This class is meant to query the AWAKE DB actor_db.freebase.sqlite.
 * There is a separate class @see com.bbn.bue.geonames.GeoNames, which is meant for the DB geoNames.db
 */
public final class GeoActors implements Closeable {
  private static final Logger log = LoggerFactory.getLogger(GeoActors.class);

  private final Connection connection;

  final PreparedStatement lookUpWithGeoNameIdStatement;
  final PreparedStatement countryLookupStatement;

  private LoadingCache<Long, AdministrativeDivisions> adCache =
      CacheBuilder.newBuilder().build(new CacheLoader<Long, AdministrativeDivisions>() {
        @Override
        public AdministrativeDivisions load(Long id) throws Exception {
          return getAdministrativeDivisionsByGeoID(id);
        }
      });

  private GeoActors(Connection connection, PreparedStatement lookUpStatement,
      PreparedStatement countryLookupStatement) throws GeonamesException {
    try {
      checkArgument(!connection.isClosed() && !lookUpStatement.isClosed() && !countryLookupStatement.isClosed());
    } catch (SQLException e) {
      throw new GeonamesException("Error during initialization", e);
    }
    this.connection = checkNotNull(connection);
    this.lookUpWithGeoNameIdStatement = checkNotNull(lookUpStatement);
    this.countryLookupStatement = checkNotNull(countryLookupStatement);
  }

  public LoadingCache<Long, AdministrativeDivisions> getLoadingCache() {
    return adCache;
  }

  public static GeoActors connectToGeonamesDB(File dbFile) throws GeonamesException {
    log.debug("Connecting to GeoNames database stored in {}", dbFile);
    log.debug("Loading JDBC driver");
    checkNotNull(org.sqlite.JDBC.class);

    try {
      // Open read-only
      final SQLiteConfig config = new SQLiteConfig();
      config.setReadOnly(true);

      final Connection connection = DriverManager.getConnection("jdbc:sqlite:" + dbFile.getAbsolutePath(), config.toProperties());
      final PreparedStatement ps =
          connection.prepareStatement("select country_code,admin1,admin2,admin3,admin4 from "
              + "geonames where geonameid=?");
      final PreparedStatement ps2 = connection.prepareStatement("select canonicalname from actor where actorid=?");

      return new GeoActors(connection,ps,ps2);
    } catch (SQLException e) {
      throw new GeonamesException("Error establishing connection", e);
    }
  }

  /**
   * If we can find a GeoResolvedActor from a given ActorEntity, we will have a geoID from the GeoResolvedActor.
   */
  public AdministrativeDivisions getAdministrativeDivisionsByGeoID(Long geoID) throws GeonamesException {
    checkNotNull(geoID);

    try {
      this.lookUpWithGeoNameIdStatement.setString(1,Long.toString(geoID));

      final ResultSet resultSet = this.lookUpWithGeoNameIdStatement.executeQuery();
      if (resultSet.next()) {
        final String countryCode = resultSet.getString("country_code");
        final String admin1 = resultSet.getString("admin1");  // nullable
        final String admin2 = resultSet.getString("admin2");  // nullable
        final String admin3 = resultSet.getString("admin3");  // nullable
        final String admin4 = resultSet.getString("admin4");  // nullable

        AdministrativeDivisions ad =
            new AdministrativeDivisions.Builder().geoID(geoID).countryCode(countryCode)
                .admin1(Optional.fromNullable(admin1)).admin2(Optional.fromNullable(admin2))
                .admin3(Optional.fromNullable(admin3)).admin4(Optional.fromNullable(admin4))
                .build();

        return ad;
      }else{
        throw new GeonamesException("No entry exists for geoID="+geoID,null);
      }
    } catch (SQLException e) {
      throw new GeonamesException("Lookup of location records for geoID " + geoID + " failed", e);
    }
  }

  @Override
  public void close() throws IOException {
    try {
      this.lookUpWithGeoNameIdStatement.close();
      this.connection.close();
    } catch (SQLException e) {
      log.error("Exception on disconnection: {}", e);
    }
  }
}
