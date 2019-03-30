from core import Model, IntField, StringField

class User(Model):
   id = IntField()
   name = StringField()

   class Meta:
       table_name = 'User'
#
#
# class Man(User):
#     sex = StringField()
#
#
user = User(id=1, name="name")
print("User instance", user.__dict__)

user.id = 2
user.name = "abc"
print("User instance", user.__dict__)

user.save()
# User.objects.all().filter(name="abc")

# user_obj = User.objects.create(id=3, name='Jone')

# print("create", user_obj, "\n", user_obj.__dict__)


print(user.__dict__)
# user.save()

# print(str([1, 2, 3]))
# print(user.__dict__)
# print(user.id)
# user.save()
# user.save() # сохранение в бд


class Manage:
   def __get__(self, instance, owner):
       print("instance: ", instance, "\n", "owner: ", owner)
       print(owner.__bases__[-1])
       print(instance.__class__)


class A:
   a_attr = "val"
   obj = Manage()


class B(A):
   b_attr = "b_attr"

a = A()
b = B()

print(b.obj)



# User.objects.update(id=1)
# User.objects.delete(id=1)
#
# User.objects.filter(id=2).filter(name='petya')
#
# user.name = '2'
# user.save()
# user.delete()
