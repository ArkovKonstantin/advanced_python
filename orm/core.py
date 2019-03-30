import abc
import config
from SQLighter import SQLighter


class Field(abc.ABC):
    def __init__(self, f_type, required=True, default=None):
        self.f_type = f_type
        self.required = required
        self.default = default

    def __set__(self, instance, value):
        value = self.validate(value)
        setattr(instance, self.storage_name, value)

    def __get__(self, instance, owner):
        return getattr(instance, self.storage_name)

    @abc.abstractmethod
    def validate(self, value):
        if value is None and not self.required:
            return None

        try:
            value = self.f_type(value)
        except ValueError:
            raise ValueError(f'Value must me {self.f_type}')

        return value


class IntField(Field):
    def __init__(self, required=True, default=None):
        super().__init__(int, required, default)

    def validate(self, value):
        value = super().validate(value)
        return value


class StringField(Field):
    def __init__(self, required=True, default=None):
        super().__init__(str, required, default)

    def validate(self, value):
        value = super().validate(value).strip()
        if not value:
            msg = f"value of {type(self).__name__} can not be empty"
            raise ValueError(msg)

        return value


class ModelMeta(type):
    def __new__(mcs, name, bases, namespace):
        if name == 'Model':
            return super().__new__(mcs, name, bases, namespace)

        meta = namespace.get('Meta')
        if meta is None:
            raise ValueError('meta is none')
        if not hasattr(meta, 'table_name'):
            raise ValueError('table_name is empty')

        # todo mro
        fields = {}
        for k, v in namespace.items():
            if isinstance(v, Field):
                cls_name = v.__class__.__name__
                v.storage_name = f"{cls_name}#{k}"
                fields[k] = v

        namespace['_fields'] = fields
        namespace['_table_name'] = meta.table_name
        return super().__new__(mcs, name, bases, namespace)

# TODO QuerySet
class Manage:

    def __init__(self):
        self.model_cls = None

    def __get__(self, instance, owner):
        if self.model_cls is None:
            self.model_cls = owner
        return self

    def create(self, **kwargs):
        instance = self.model_cls(**kwargs)
        instance.save()
        return instance

    def all(self) -> QuerySet:
        table_name = self.model_cls._table_name
        sql_query = f'SELECT * FROM {table_name}'
        with SQLighter(config.db_name) as db_worker:
            items = db_worker.cursor.execute(sql_query).fetchall()
        return items

    def get(self, **kwargs):
        """Должен вернуть уникальный экземляр"""
        pass



class Model(metaclass=ModelMeta):
    class Meta:
        table_name = ''

    objects = Manage()

    def __new__(cls, *args, **kwargs):
        pass

    # todo DoesNotExist

    def __init__(self, *_, **kwargs):
        for field_name, field in self._fields.items():
            value = kwargs.get(field_name)
            setattr(self, field_name, value)

    # TODO pk
    # TODO перенести логику создания таблиц в метакласс
    def save(self):
        with SQLighter(config.db_name) as db_worker:
            table_name = type(self)._table_name

            attrs = ','.join(map(lambda lst: f'{lst[1]} {db_worker._db_field[lst[0]]}',
                                 (k.split('#') for k in vars(self))))

            sql_query = f"SELECT count(*) FROM sqlite_master" \
                        f" WHERE type = 'table' AND name = '{table_name}';"
            table_exists = db_worker.cursor.execute(sql_query).fetchone()

            if table_exists:
                sql_query = f"CREATE TABLE IF NOT EXISTS {table_name}({attrs})"
                # print("attr: ", attrs, "\n", "sql_query", sql_query)
            else:
                pk = vars(self)[f'{type(self)}#pk']
                sql_query = f"INSERT {table_name} SET {attrs} WHERE pk = {pk}"  # insert

            db_worker.cursor.execute(sql_query)
            # установить pk в обьект
            pk = db_worker.exexute("COUNT ...")
            setattr(self, "pk", pk)


    def update(self, **kwargs):
        with SQLighter(config.db_name) as db_worker:
            table_name = type(self)._table_name

            attrs = ','.join(map(lambda lst: f'{lst[1]} {db_worker._db_field[lst[0]]}',
                                 (k.split('#') for k in vars(self))))

            pk = vars(self)['pk']
            sql_query = f"UPDATE {table_name} SET {attrs} WHERE pk = {pk}"
            db_worker.cursor.execute(sql_query)

    def delete(self):
        """удаление записи из таблицы"""
