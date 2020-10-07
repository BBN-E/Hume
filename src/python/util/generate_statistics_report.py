import json
from peewee import fn,SQL
from model_for_summary_statics import EntityT1,EventT1,database

def query_entity_string_cnt():
    print("#### Entity string counts:")
    for i in EntityT1.select(EntityT1.canonical_name,fn.COUNT(EntityT1.canonical_name).alias("count")).group_by(EntityT1.canonical_name).order_by(SQL("count").desc()).limit(10):
        print("{}\t{}".format(i.canonical_name,i.count))
    print("#### End Entity string counts:")

def query_entity_string_cnt_limited_by_entity_type(entity_type):
    print("#### Entity count by entity type: {}".format(entity_type))
    for i in EntityT1.select(EntityT1.canonical_name,fn.COUNT(EntityT1.canonical_name).alias("count")).where(EntityT1.entity_type == entity_type ).group_by(EntityT1.canonical_name).order_by(SQL("count").desc()).limit(10):
        print("{}\t{}".format(i.canonical_name,i.count))
    print("#### End Entity count by entity type: {}".format(entity_type))

def query_anchor_string_cnt():
    print("#### Event anchor string count")
    for i in EventT1.select(EventT1.event_mention_str,fn.COUNT(EventT1.event_mention_str).alias("count")).where((EventT1.actor_str == "") & (EventT1.location_str == "")).group_by(EventT1.event_mention_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.event_mention_str,i.count))
    print("#### End Event anchor and string count")

def query_actor_cnt_in_event():
    print("#### Actor cnt in event")
    for i in EventT1.select(EventT1.actor_str,fn.COUNT(EventT1.actor_str).alias("count")).where(EventT1.actor_str != "").group_by(EventT1.actor_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.actor_str,i.count))
    print("#### End Actor cnt in event")

def query_location_cnt_in_event():
    print("#### Location cnt in event")
    for i in EventT1.select(EventT1.location_str,fn.COUNT(EventT1.location_str).alias("count")).where(EventT1.location_str != "").group_by(EventT1.location_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.location_str,i.count))
    print("#### End Location cnt in event")

def given_a_set_of_actors_output_event_count(actors,db):
    print("#### Event count for actors: {}".format(actors))
    entities_join = " or ".join("actor_str like \"%{}%\"".format(i) for i in actors)
    for i in db.execute_sql("SELECT event_mention_str,count(event_mention_str) as count,actor_str from eventt1 where ({} and location_str=\"\") GROUP by event_mention_str order by count desc limit 100;".format(entities_join)):
        print("{}\t{}\t{}".format(i[0],i[1],i[2]))
    print("#### End Event count for actors: {}".format(actors))

def given_a_set_of_locations_output_event_count(locations,db):
    print("#### Event count for locations: {}".format(locations))
    entities_join = " or ".join("location_str like \"%{}%\"".format(i) for i in locations)
    for i in db.execute_sql("SELECT event_mention_str,count(event_mention_str) as count,location_str from eventt1 where ({} and actor_str=\"\") GROUP by event_mention_str order by count desc limit 20;".format(entities_join)):
        print("{}\t{}\t{}".format(i[0],i[1],i[2]))
    print("#### End Event count for locations: {}".format(locations))

def given_event_mention_str_output_counts_of_actors(event_str):
    print("#### Actor counts given event string: {}".format(event_str))
    for i in EventT1.select(EventT1.actor_str,fn.COUNT(EventT1.actor_str).alias("count")).where((EventT1.event_mention_str.contains(event_str)) & (EventT1.location_str == "") & (EventT1.actor_str != "")).group_by(EventT1.actor_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.actor_str,i.count))
    print("#### End Actor counts given event string: {}".format(event_str))

def given_event_mention_str_output_counts_of_locations(event_str):
    print("#### Location counts given event string: {}".format(event_str))
    for i in EventT1.select(EventT1.location_str,fn.COUNT(EventT1.location_str).alias("count")).where((EventT1.event_mention_str.contains(event_str)) & (EventT1.location_str != "") & (EventT1.actor_str == "")).group_by(EventT1.location_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.location_str,i.count))
    print("#### End Location counts given event string: {}".format(event_str))

def given_event_str_and_actor_output_count_of_locations(event_str,actor):
    print("#### Location counts given event string: {} and actor: {}".format(event_str,actor))
    for i in EventT1.select(EventT1.location_str,fn.COUNT(EventT1.location_str).alias("count")).where((EventT1.event_mention_str.contains(event_str)) & (EventT1.location_str != "") & (EventT1.actor_str.contains(actor))).group_by(EventT1.location_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.location_str,i.count))
    print("#### End Location counts given event string: {}".format(event_str))

def given_event_str_and_location_output_count_of_actors(event_str,location):
    print("#### Actor counts given event string: {} and location: {}".format(event_str,location))
    for i in EventT1.select(EventT1.actor_str,fn.COUNT(EventT1.actor_str).alias("count")).where((EventT1.event_mention_str.contains(event_str)) & (EventT1.location_str.contains(location)) & (EventT1.actor_str != "")).group_by(EventT1.actor_str).order_by(SQL("count").desc()).limit(20):
        print("{}\t{}".format(i.actor_str,i.count))
    print("#### End Actor counts given event string: {} and location: {}".format(event_str,location))

if __name__ == "__main__":

    database.init("/nfs/raid88/u10/users/hqiu/tmp/event_statics.db", pragmas={
        'journal_mode': 'wal',  # WAL-mode.
        'cache_size': -64 * 1000,  # 64MB cache.
        'synchronous': 0})
    database.connect()

    query_entity_string_cnt()
    query_entity_string_cnt_limited_by_entity_type("GPE")
    query_anchor_string_cnt()
    query_actor_cnt_in_event()
    query_location_cnt_in_event()
    # given_a_set_of_actors_output_event_count({"Russia","North Atlantic Treaty Organization"},database)
    # given_a_set_of_locations_output_event_count({"Russia","Denmark"},database)
    # given_event_mention_str_output_counts_of_actors("war")
    # given_event_mention_str_output_counts_of_locations("war")
    # given_event_str_and_actor_output_count_of_locations("war","Russia")
    # given_event_str_and_location_output_count_of_actors("war","Russia")

    # with open("/home/hqiu/Public/structure_query_dryrun_110619.json") as fp:
    #     queries = json.load(fp)
    # print(queries[0])
    # given_a_set_of_actors_output_event_count({"Kingdom of Denmark"},database)
    # given_event_mention_str_output_counts_of_actors("military spending")

    database.commit()
    database.close()