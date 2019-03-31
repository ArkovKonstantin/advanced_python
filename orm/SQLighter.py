import sqlite3


class SQLighter:
    def __init__(self, db_name):
        self._connection = sqlite3.connect(db_name)
        self._db_field = {"IntField": "INTEGER", "StringField": "TEXT"}
        self.cursor = self._connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.close()

    def create_table(self, fields: dict, table_name):
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        fields = ','.join(map(lambda item: f"{item[0]} {self._db_field[type(item[1]).__name__]}",
                              fields.items()))

        sql_query = f'CREATE TABLE {table_name}' \
                    f'(pk INTEGER PRIMARY KEY AUTOINCREMENT,' \
                    f'{fields})'

        self.cursor.execute(sql_query)

    def create_record(self, instance):
        attrs = vars(instance)
        pk = attrs.get('pk', None)
        table_name = instance._table_name

        if pk is None:
            # insert
            keys = ','.join((k.split('#')[1] for k in attrs))
            values = ','.join(f"'{str(v)}'" for v in attrs.values())
            sql_query = f'INSERT INTO {table_name}({keys})' \
                        f'VALUES({values})'

            self.cursor.execute(sql_query)
            self._connection.commit()
            pk = self.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
            setattr(instance, 'pk', pk)
        else:
            # update
            param = ','.join(map(lambda item: f"{item[0].split('#')[-1]}='{item[1]}'",
                                 attrs.items()))
            sql_query = f"UPDATE {table_name} " \
                        f"SET {param}" \
                        f"WHERE pk='{instance.pk}'"

            self.cursor.execute(sql_query)
            self._connection.commit()

    def delete_record(self, instance):
        attrs = vars(instance)
        pk = attrs.get('pk', None)
        table_name = instance._table_name
        sql_query = f"DELETE FROM {table_name} WHERE pk = '{pk}'"
        self.cursor.execute(sql_query)
        self._connection.commit()

    def update_record(self, instance, **kwargs):
        pk = instance.pk
        table_name = instance._table_name

        param = ','.join(map(lambda item: f"{item[0]}='{item[1]}'",
                             kwargs.items()))
        sql_query = f"UPDATE {table_name} " \
                    f"SET {param}" \
                    f"WHERE pk='{pk}'"

        for k, v in kwargs.items():
            k = f"{getattr(type(instance), k)}#{k}"
            vars(instance)[k] = v

        self.cursor.execute(sql_query)
        self._connection.commit()

    def get_record(self, instance, attrs: dict):
        table_name = instance.model_cls._table_name
        param = ','.join(map(lambda item: f"{item[0]}='{item[1]}'",
                             attrs.items()))

        sql_query = f"SELECT * FROM {table_name} WHERE {param}"
        return self.cursor.execute(sql_query).fetchall()
