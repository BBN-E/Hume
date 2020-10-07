from peewee import Model,PrimaryKeyField,TextField
from playhouse.sqlite_ext import SqliteExtDatabase


database = SqliteExtDatabase(None)


class BaseModel(Model):
    class Meta:
        database = database


class EntityT1(BaseModel):
    entity_type = TextField()
    canonical_name = TextField()

class EventT1(BaseModel):
    event_type = TextField()
    event_mention_str = TextField()
    actor_str = TextField(null=True)
    location_str = TextField(null=True)



if __name__ == "__main__":
    database.init("/nfs/raid88/u10/users/hqiu/tmp/event_statics.db", pragmas={
        'journal_mode': 'wal',  # WAL-mode.
        'cache_size': -64 * 1000,  # 64MB cache.
        'synchronous': 0})
    database.connect()
    database.create_tables([EntityT1,EventT1])
    database.commit()
    database.close()