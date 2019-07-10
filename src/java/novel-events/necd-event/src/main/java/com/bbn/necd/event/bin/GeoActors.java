package com.bbn.necd.event.bin;

import com.bbn.bue.common.symbols.Symbol;
import com.bbn.serif.theories.actors.GeoResolvedActor;

import com.google.common.base.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;

import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Created by ychan on 8/8/16.
 */
public final class GeoActors {
  private static final Logger log = LoggerFactory.getLogger(GeoActors.class);

  private final Connection connection;

  final PreparedStatement lookUpWithGeoNameIdStatement;
  final PreparedStatement countryLookupStatement;

  private Map<Long,AdministrativeDivisions> localCache = new HashMap<>();
  private Map<Long,GeoResolvedActor> localGeoResolvedActorCache = new HashMap<>();

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

  public static GeoActors connectToGeonamesDB(File dbFile) throws GeonamesException {
    log.info("Connecting to GeoNames database stored in {}", dbFile);
    try {
      log.info("Loading JDBC driver");
      Class.forName("org.sqlite.JDBC");
    } catch (ClassNotFoundException e) {
      throw new GeonamesException("Could not load JDBC driver", e);
    }

    try {
      // Open read-only
      final SQLiteConfig config = new SQLiteConfig();
      config.setReadOnly(true);

      final Connection connection = DriverManager
          .getConnection("jdbc:sqlite:" + dbFile.getAbsolutePath(), config.toProperties());
      final PreparedStatement ps =
          connection.prepareStatement("select country_code,admin1,admin2,admin3,admin4 from "
              + "geonames where geonameid=?");
      final PreparedStatement ps2 = connection.prepareStatement("select canonicalname from actor where actorid=?");

      if(connection.isClosed()) {
        log.info("connection is closed");
      } else {
        log.info("connection is open");
      }
      if(ps.isClosed()) {
        log.info("ps is closed");
      } else {
        log.info("ps is open");
      }
      if(ps2.isClosed()) {
        log.info("ps2 is closed");
      } else {
        log.info("ps2 is open");
      }

      return new GeoActors(connection,ps,ps2);
    } catch (SQLException e) {
      throw new GeonamesException("Error establishing connection", e);
    }
  }

  public final AdministrativeDivisions administrativeDivisionsForGeoID(Long geoID)
      throws GeonamesException {
    checkNotNull(geoID);

    log.info("Looking up administrative divisions for {} in Local Cache...", geoID);
    if(localCache.containsKey(geoID)){
      log.info("Found key in local cache...");
      return localCache.get(geoID);
    }

    log.info("Looking up administrative divisions for {} in DB...", geoID);
    try {
      this.lookUpWithGeoNameIdStatement.setString(1,Long.toString(geoID));
      final ResultSet resultSet = this.lookUpWithGeoNameIdStatement.executeQuery();
      if (resultSet.next()) {
        AdministrativeDivisions ad = AdministrativeDivisions.from(geoID, Symbol.from(resultSet.getString("country_code")),
            Optional.fromNullable(resultSet.getString("admin1")!=null ? Symbol.from(resultSet.getString("admin1")) : null),
            Optional.fromNullable(resultSet.getString("admin2")!=null?Symbol.from(resultSet.getString("admin2")):null),
            Optional.fromNullable(resultSet.getString("admin3")!=null?Symbol.from(resultSet.getString("admin3")):null),
            Optional.fromNullable(resultSet.getString("admin4")!=null?Symbol.from(resultSet.getString("admin4")):null));
        localCache.put(geoID, ad);
        return ad;
      }else{
        throw new GeonamesException("No entry exists for geoID="+geoID,null);
      }
    } catch (SQLException e) {
      throw new GeonamesException("Lookup of location records for geoID " + geoID + " failed", e);
    }
  }

  public final Optional<GeoResolvedActor> geoResolvedActorForActorID(Long actorID)
      throws GeonamesException {
    checkNotNull(actorID);

    log.info("Looking up geoResolvedActor for {} in Local Cache...", actorID);
    if(localGeoResolvedActorCache.containsKey(actorID)){
      log.info("Found key in local geoResolvedActor cache...");
      return Optional.of(localGeoResolvedActorCache.get(actorID));
    }

    log.info("Looking up country for {} in DB...", actorID);
    try {
      this.countryLookupStatement.setLong(1,actorID);
      final ResultSet resultSet = this.countryLookupStatement.executeQuery();
      if (resultSet.next()) {
        final String countryName = resultSet.getString("canonicalname");
        if (countryName==null){
          return Optional.<GeoResolvedActor>absent();
        }
        final GeoResolvedActor countryActor = GeoResolvedActor.create(null,Symbol.from(countryName),
            Optional.<Long>absent(), Optional.<Double>absent(), Optional.<Double>absent(),
            Optional.<GeoResolvedActor.CountryInfo>absent());
        localGeoResolvedActorCache.put(actorID, countryActor);
        return Optional.of(countryActor);
      }else{
        throw new GeonamesException("No entry exists for actorID="+actorID,null);
      }
    } catch (SQLException e) {
      throw new GeonamesException("Lookup of country-name for actorID " + actorID + " failed", e);
    }
  }

  public void disconnect() {
    try {
      this.lookUpWithGeoNameIdStatement.close();
      this.connection.close();
      this.localCache = new HashMap<>();
    } catch (SQLException e) {
      log.error("Exception on disconnection: {}", e);
    }
  }
}
