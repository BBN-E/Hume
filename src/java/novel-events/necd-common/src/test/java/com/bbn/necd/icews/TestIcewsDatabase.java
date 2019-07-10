package com.bbn.necd.icews;

import com.bbn.bue.common.parameters.Parameters;
import com.google.common.base.Optional;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Ignore;
import org.junit.Test;

import java.io.File;
import java.io.IOException;
import java.sql.SQLException;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * Tests the IcewsDatabase class.
 */
@Ignore // We have to do this because these tests fail 95% of the time on CI machines due to NFS issues.
public final class TestIcewsDatabase {

  private static final String BARACK_OBAMA_NAME = "Barack Obama";
  private static final long BARACK_OBAMA_ACTORID = 14631;
  private static final String CHRIS_SMITH_NAME = "Chris Smith";
  private static final long BANK_AGENT_ID = 25;

  private static ICEWSDatabase db;

  @BeforeClass
  public static void setUp() throws IOException, SQLException {
    final File paramsFile = new File(ICEWSDatabase.class.getResource("/icewsdb.params").getPath());
    db = ICEWSDatabase.fromParameters(Parameters.loadSerifStyle(paramsFile));
  }

  @AfterClass
  public static void cleanUp() throws SQLException {
    db.close();
  }

  /**
   * Tests getting an actor name from an actor id.
   */
  @Test
  public void testGetActorNameFromId() throws SQLException {
    final Optional<String> name = db.getActorNameFromId(BARACK_OBAMA_ACTORID);
    assertTrue(name.isPresent());
    assertEquals(BARACK_OBAMA_NAME, name.get());
  }

  /**
   * Tests getting actor ids for a name.
   */
  @Test
  public void testGetActorIdsForName() throws SQLException {
    // Test a single actor id
    final ImmutableList<Long> names1 = db.getActorIdsForName(BARACK_OBAMA_NAME);
    assertEquals(ImmutableList.of(BARACK_OBAMA_ACTORID), names1);

    // Test multiple actor ids
    final ImmutableList<Long> names2 = db.getActorIdsForName(CHRIS_SMITH_NAME);
    assertTrue(names2.size() > 1);
  }

  /**
   * Tests getting sectors for an actor ID.
   */
  @Test
  public void testGetSectorsForActorId() throws SQLException {
    final ImmutableSet<String> sectors = db.getSectorsForActorId(BARACK_OBAMA_ACTORID);
    assertFalse(sectors.isEmpty());
    assertEquals(ImmutableSet.of("Government", "Executive", "Executive Office", "Ideological", "Center Left", "Parties",
        "(National) Major Party", "Legislative / Parliamentary", "Upper House", "Local", "Provincial"), sectors);
  }

  /**
   * Tests getting sectors for an agent ID.
   */
  @Test
  public void testGetSectorsForAgentId() throws SQLException {
    final ImmutableSet<String> sectors = db.getSectorsForAgentId(BANK_AGENT_ID);
    assertFalse(sectors.isEmpty());
    assertEquals(ImmutableSet.of("Business"), sectors);
  }
}
