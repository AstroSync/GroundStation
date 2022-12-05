from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel


# class Foo:
#     def __init__(self, **kwargs) -> None:
#         self.a: int = kwargs.get('a', 0)
#         self.b: int = kwargs.get('b', 1)
#         self.c: int = 3
#         print(self.__class__)

#     def check(self) -> None:
#         print('boo')

#     def to_model(self):
#         return MyModel(**self.__dict__)

# bar = Foo(a=1, b=2)
# c = dict({k: v for k, v in bar.__dict__.items() if k != 'a'})
# print(Foo)

# print(bar.to_model())

class MyModel(BaseModel):
    a: int
    b: int
    d: datetime
class MyClass:
    a: int = 1
    b: int = 2
    def __init__(self, **kwargs) -> None:
        self.c = 0

a = [1, 14, 15, 1125]
print([f'0x{x:04X}' for x in a])

print([int.to_bytes(x, 2, byteorder='little') for x in a])
l = b''.join([int.to_bytes(x, 2, byteorder='little') for x in a])
start = 1
stop = len(l)
print(list(b''.join([int.to_bytes(x, 2, byteorder='little') for x in a])[start:stop]))


date1 = datetime.now().astimezone(ZoneInfo('UTC'))
date2 = datetime.now().astimezone()
print(date1.tzinfo)
print(date2.tzinfo)

sample_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
chunk_size=10
result=[sample_list[i:i + chunk_size] for i in range(0, len(sample_list), chunk_size)]
print(result)
print(MyClass(**{'h':1}).__dict__)
print(MyModel.parse_obj({'a':1, 'b':2, 'd':'2022-12-05T10:21:50.739874Z'}))
