import sqlite3

class AwakeDB:

    def __init__(self):
        pass

    conn = None
    source_cache = dict()
    geonameid_cache = dict()

    @classmethod
    def initialize_awake_db(cls, awake_sqlite_db):
        cls.conn = sqlite3.connect(awake_sqlite_db)

    @classmethod 
    def get_source_string(cls, actorid):
        if actorid in cls.source_cache:
            return cls.source_cache[actorid]

        cur = cls.conn.cursor()
        cur.execute("select originalsourceelement from actor a, actorsource s where a.actorid=s.actorid and a.actorid=?", (actorid,))
        results = cur.fetchone()
        if results: 
            cls.source_cache[actorid] = results[0]
            return results[0]
        cls.source_cache[actorid] = None
        return None

    @classmethod
    def get_geonameid_from_actorid(cls, actorid):
        if actorid in cls.geonameid_cache:
            return cls.geonameid_cache[actorid]
        
        cur = cls.conn.cursor()
        cur.execute("select geonameid from actor a where a.actorid=?", (actorid,))
        results = cur.fetchone()
        if results: 
            cls.geonameid_cache[actorid] = results[0]
            return results[0]
        cls.geonameid_cache[actorid] = None
        return None
