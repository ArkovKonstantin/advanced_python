import abc
import config
from SQLighter import SQLighter


class Field(abc.ABC):
    def __init__(self, f_type, required=True, default=None):
        self.f_type = f_type
        self.required = required
        self.default = default

    # def __set__(self, instance, value):
    #     value = self.validate(value)
    #     setattr(instance, self.storage_name, value)
    #
    # def __get__(self, instance, owner):
    #     if instance:
    #         return getattr(instance, self.storage_name)
    #     else:
    #         return type(self).__name__

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

    def __init__(cls, name, bases, namespace):
        # cls уже готовый обьект
        super().__init__(name, bases, namespace)  # зачем вызывать super.__init__
        if name != 'Model':
            fields = {}
            for sub_cls in cls.mro()[:-1]:
                for k, v in vars(sub_cls).items():
                    if isinstance(v, Field):
                        fields[k] = v

            # namespace['_fields'] = fields <- почему так не работает
            cls._fields = fields
            # создание таблицы в бд
            with SQLighter(config.db_name) as db_worker:
                table_name = cls._table_name
                db_worker.create_table(fields, table_name)

    def __new__(mcs, name, bases, namespace):
        if name == 'Model':
            return super().__new__(mcs, name, bases, namespace)

        meta = namespace.get('Meta')
        if meta is None:
            raise ValueError('meta is none')
        if not hasattr(meta, 'table_name'):
            raise ValueError('table_name is empty')

        namespace['_table_name'] = meta.table_name
        return super().__new__(mcs, name, bases, namespace)

    def __call(cls):
        """"""


# todo subscriptable
class QuerySet:

    def __init__(self, model_cls, attrs: dict = None):
        self.model_cls = model_cls
        if attrs is None:
            self.attrs = {}
        else:
            self.attrs = attrs

    def filter(self, **kwargs):

        self.attrs.update(kwargs)
        return QuerySet(self.model_cls, self.attrs)

    def __iter__(self):
        table_name = self.model_cls._table_name
        with SQLighter(config.db_name) as db_worker:
            param = 'AND '.join(map(lambda item: f"{item[0]}='{item[1]}'",
                                    self.attrs.items()))
            sql_query = f"SELECT * FROM {table_name}"
            if param:
                sql_query = f"SELECT * FROM {table_name} WHERE {param}"

            print(sql_query)
            table_data = db_worker.cursor.execute(sql_query).fetchall()

        attrs = list(attr for attr in vars(self.model_cls)
                     if not attr.startswith('_') and attr != 'Meta')

        for row in table_data:
            pk = row[0]
            instance = self.model_cls(**dict(zip(attrs, row[1:])))
            setattr(instance, 'pk', pk)

            yield instance

    # todo
    def __len__(self):
        """кол во записей в таблице"""


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
        """Вернуть все записи"""
        return QuerySet(self.model_cls)

    def filter(self, **kwargs) -> QuerySet:
        return QuerySet(self.model_cls, kwargs)

    def get(self, **kwargs):
        """Должен вернуть один уникальный экземляр"""
        with SQLighter(config.db_name) as db_worker:
            result = db_worker.get_record(self, kwargs)
            if result:
                if len(result) == 1:

                    attrs = self.model_cls._fields.keys()
                    pk = result[0][0]
                    instance = self.model_cls(**dict(zip(attrs, result[0][1:])))
                    setattr(instance, 'pk', pk)
                    instance._updated_fields = {}
                    return instance
                raise ValueError("много записей")

            return None


class Model(metaclass=ModelMeta):
    class Meta:
        table_name = ''

    objects = Manage()

    # todo DoesNotExist


    def __init__(self, *_, **kwargs):
        # col names; col values;
        self._updated_fields = {} # dict атрибутов, которые были обновлены

        for field_name, field in self._fields.items():
            value = kwargs.get(field_name)
            setattr(self, field_name, value)

    def __setattr__(self, key, value):

        try:
            field = self._fields[key]
            val = field.validate(value)
            self.__dict__[key] = val
            # todo col names, values
            self._updated_fields[key] = val
        except KeyError:
            self.__dict__[key] = value


    def save(self):
        with SQLighter(config.db_name) as db_worker:
            db_worker.create_record(self)

    def update(self, **kwargs):
        self._updated_fields.update(kwargs)

        """обновить обьект и запись в таблице"""
        with SQLighter(config.db_name) as db_worker:
            db_worker.update_record(self)

    def delete(self):
        """удаление записи из таблицы"""
        with SQLighter(config.db_name) as db_worker:
            db_worker.delete_record(self)

    def __str__(self):
        return str(vars(self))

