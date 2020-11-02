from peewee import (
    fn, Model, IntegerField, CharField, DateTimeField
)
from playhouse.migrate import (
    migrate as peewee_migrate,
    SqliteMigrator,
    MySQLMigrator,
    PostgresqlMigrator
)
from playhouse.db_url import connect
import config
import logging
import datetime

database = connect(config.DATABASE_URI)
if 'mysql' in config.DATABASE_URI:
    fn_Random = fn.Rand
else:
    fn_Random = fn.Random


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    uid = IntegerField(primary_key=True)
    name = CharField(max_length=250)
    path = IntegerField()
    step = IntegerField(default=1)
    updated = DateTimeField(default=datetime.datetime.now)


# ------------------------------ MIGRATION ------------------------------


LAST_VERSION = 1


class Version(BaseModel):
    version = IntegerField()


@database.atomic()
def migrate():
    database.create_tables([Version], safe=True)
    try:
        v = Version.select().get()
    except Version.DoesNotExist:
        database.create_tables([User])
        v = Version(version=LAST_VERSION)
        v.save()

    if v.version >= LAST_VERSION:
        return

    if 'mysql' in config.DATABASE_URI:
        migrator = MySQLMigrator(database)
    elif 'sqlite' in config.DATABASE_URI:
        migrator = SqliteMigrator(database)
    else:
        migrator = PostgresqlMigrator(database)

    # No migrations yet

    logging.info('Migrated the database to version %s', v.version)
    if v.version != LAST_VERSION:
        raise ValueError('LAST_VERSION in db.py should be {}'.format(v.version))
