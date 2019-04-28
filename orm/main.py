from core import Model, IntField, StringField
from SQLighter import SQLighter


class User(Model):
    id = IntField()
    name = StringField()

    class Meta:
        table_name = 'User'


#
#
class Man(User):
    sex = StringField()

    class Meta:
        table_name = "Man"


print('-------Создание обьектов--------')

man = Man(sex="m", id=5)
man.save()

user1 = User.objects.create(id=1, name='Mishgan')
user_obj = User.objects.get(id=1)
print(user_obj)
# user3 = User.objects.create(id=1, name='Lexa')
# user4 = User.objects.create(id=1, name='Jone')

# user2 = User(id=2, name="Irjan")
# user2.save()


# print('man: ', man)
# print('user1: ', user1)
# print('user2: ', user2)


print('-------Изменение обьектов--------')
user1.name = "Miha"
user1.save()
user1 = User.objects.get(name="Miha")
# print('user1: ', user1)

# user2.update(name="Nurmagomed")
# print('user2: ', user2.name)  # object
# user2 = User.objects.get(id=2)  # get from db
# print('user2: ', user2.name)

print('-------Удаление обьектов--------')

# user2.delete()
# user2 = User.objects.get(id=2)
# print('user2: ', user2)

print('-------all(); filter()--------')

# qs = User.objects.filter(id=1).filter(name='Jone')
# gen = iter(qs)
# print(vars(next(gen)))
#
# for item in User.objects.all():
#     print(item)