package com.bbn.necd.icews;

import com.bbn.bue.common.parameters.Parameters;
import com.google.common.annotations.Beta;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.io.Files;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.File;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * Provides an interface to the ICEWS database.
 */
@Beta
public final class ICEWSDatabase {

  private static final Logger log = LoggerFactory.getLogger(ICEWSDatabase.class);

  private static final String TEMP_PREFIX = "novel_events_icewsdb_";
  private static final String TEMP_SUFFIX = ".db";

  private static final String PARAM_DBPATH = "icewsdbpath";
  private static final String CONNECTION_PREFIX = "jdbc:sqlite:";
  private static final String QUERY_SELECT_STAR_WHERE = "SELECT * FROM %s WHERE %s = ?";

  private static final String TABLE_ACTORS = "dict_actors";
  private static final String TABLE_SECTORS = "dict_sectors";
  private static final String TABLE_ACTOR_SECTORS = "dict_sector_mappings";
  private static final String TABLE_AGENT_SECTORS = "dict_agent_sector_mappings";
  private static final String COLUMN_ACTORID = "actor_id";
  private static final String COLUMN_AGENTID = "agent_id";
  private static final String COLUMN_SECTORID = "sector_id";
  private static final String COLUMN_NAME = "name";

  private final Connection conn;

  private ICEWSDatabase(final Connection conn) throws SQLException {
    this.conn = conn;
  }

  /**
   * Load the database specified by the {@link Parameters} and create a new instance that uses it.
   *
   * @param params the parameters
   * @return a new instance
   * @throws SQLException if the database cannot be loaded
   */
  public static ICEWSDatabase fromParameters(final Parameters params) throws SQLException, IOException {
    final File dbFile = params.getExistingFile(PARAM_DBPATH);
    // Because NFS locks cause problems, we have to copy the database locally
    final File tempDbFile = File.createTempFile(TEMP_PREFIX, TEMP_SUFFIX);
    tempDbFile.deleteOnExit();
    log.info("Making temporary copy of ICEWS database {} at {}", dbFile, tempDbFile);
    Files.copy(dbFile, tempDbFile);

    // Open read-only
    final SQLiteConfig config = new SQLiteConfig();
    config.setReadOnly(true);
    final Connection conn = DriverManager.getConnection(CONNECTION_PREFIX + tempDbFile,
        config.toProperties());
    return new ICEWSDatabase(conn);
  }

  /**
   * Returns the name of the actor with the specified id.
   *
   * @param id the id
   * @return the name of the actor, or {@link Optional#absent()} if no actor has the specified id
   * @throws SQLException if there is a problem with executing the query
   */
  public Optional<String> getActorNameFromId(final long id) throws SQLException {
    final PreparedStatement selectActorById =
        conn.prepareStatement(String.format(QUERY_SELECT_STAR_WHERE, TABLE_ACTORS, COLUMN_ACTORID));
    selectActorById.setLong(1, id);
    final ResultSet rs = selectActorById.executeQuery();
    // Actor id is a primary key so there can never be more than one result
    final Optional<String> result = rs.next()
        ? Optional.of(rs.getString(COLUMN_NAME))
        : Optional.<String>absent();
    rs.close();
    selectActorById.close();
    return result;
  }

  /**
   * Returns all actor ids for actors with the specified name.
   *
   * @param name the name
   * @return the actor ids, which may be empty if no actors have the specified name
   * @throws SQLException if there is a problem executing the query
   */
  public ImmutableList<Long> getActorIdsForName(final String name) throws SQLException {
    final PreparedStatement selectActorById =
        conn.prepareStatement(String.format(QUERY_SELECT_STAR_WHERE, TABLE_ACTORS, COLUMN_NAME));
    selectActorById.setString(1, name);
    final ResultSet rs = selectActorById.executeQuery();
    final ImmutableList.Builder<Long> results = ImmutableList.builder();
    while (rs.next()) {
      results.add(rs.getLong(COLUMN_ACTORID));
    }
    rs.close();
    selectActorById.close();
    return results.build();
  }

  public ImmutableSet<String> getSectorsForActorId(final long actorId) throws SQLException {
    final PreparedStatement selectSectorNamesByActorId =
        conn.prepareStatement(String.format("SELECT * FROM %s DSM, %s DS where DSM.%s = ? and DS.%s = DSM.%s",
            TABLE_ACTOR_SECTORS, TABLE_SECTORS, COLUMN_ACTORID, COLUMN_SECTORID, COLUMN_SECTORID));
    selectSectorNamesByActorId.setLong(1, actorId);
    final ResultSet rs = selectSectorNamesByActorId.executeQuery();
    final ImmutableSet.Builder<String> results = ImmutableSet.builder();
    while (rs.next()) {
      results.add(rs.getString(COLUMN_NAME));
    }
    rs.close();
    selectSectorNamesByActorId.close();
    return results.build();
  }

  public ImmutableSet<String> getSectorsForAgentId(final long agentId) throws SQLException {
    final PreparedStatement selectSectorNamesByAgentId =
        conn.prepareStatement(String.format("SELECT * FROM %s DASM, %s DS where DASM.%s = ? and DS.%s = DASM.%s",
            TABLE_AGENT_SECTORS, TABLE_SECTORS, COLUMN_AGENTID, COLUMN_SECTORID, COLUMN_SECTORID));
    selectSectorNamesByAgentId.setLong(1, agentId);
    final ResultSet rs = selectSectorNamesByAgentId.executeQuery();
    final ImmutableSet.Builder<String> results = ImmutableSet.builder();
    while (rs.next()) {
      results.add(rs.getString(COLUMN_NAME));
    }
    rs.close();
    selectSectorNamesByAgentId.close();
    return results.build();
  }

  public void close() throws SQLException {
    conn.close();
  }
}
