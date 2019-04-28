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
        pk = instance.__dict__.get('pk', None)
        table_name = instance._table_name
        col_names = tuple(instance._updated_fields.keys())  # (id, name, ...)
        col_values = tuple(instance._updated_fields.values())  # (3, Jone)
        if pk is None:
            # insert

            placeholders = ",".join("?"*len(col_values)) #  получаем строку вида (?, ?, ...)

            sql_query = f'INSERT INTO {table_name} {col_names} VALUES ({placeholders})'
            print(sql_query)

            self.cursor.execute(sql_query, col_values)
            self._connection.commit()
            pk = self.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
            setattr(instance, 'pk', pk)
            instance._updated_fields = {}
        else:
            self.update_record(instance)



    def delete_record(self, instance):
        attrs = vars(instance)
        pk = attrs.get('pk', None)
        table_name = instance._table_name
        sql_query = f"DELETE FROM {table_name} WHERE pk = '{pk}'"

        self.cursor.execute(sql_query)
        self._connection.commit()

    def update_record(self, instance):
        table_name = instance._table_name
        col_names = tuple(instance._updated_fields.keys())  # (id, name, ...)
        col_values = tuple(instance._updated_fields.values())  # (3, Jone)

        placeholders = ','.join(map(lambda key: f"{key}=?", col_names))  # col1=?, col2=?
        sql_query = f"UPDATE {table_name} " \
                    f"SET {placeholders}" \
                    f"WHERE pk=?"
        print(sql_query)
        self.cursor.execute(sql_query, (*col_values, instance.pk))
        # После создания|обновления записи в бд, в updated_field кладем пустое значение
        instance._updated_fields = {}


    def get_record(self, instance, attrs: dict):

        table_name = instance.model_cls._table_name
        placeholders = ','.join(map(lambda key: f"{key}=?", attrs))

        sql_query = f"SELECT * FROM {table_name} WHERE {placeholders}"
        print("get_record", sql_query)

        return self.cursor.execute(sql_query, tuple(attrs.values())).fetchall()