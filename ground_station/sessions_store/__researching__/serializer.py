from __future__ import annotations
import json
import datetime

class PrettyPrint:
    def __str__(self) -> str:
        lines: list[str] = [self.__class__.__name__ + ':']
        for key, val in vars(self).items():
            lines += f'{key}: {val}'.split('\n')
        return '\n    '.join(lines)

class ClassA(PrettyPrint):
    def __init__(self, **kwargs) -> None:
        self.a: int = kwargs.get('a', 1)
        self.dt: datetime.datetime = kwargs.get('dt', datetime.datetime.now().astimezone())

class ClassB(PrettyPrint):
    def __init__(self, **kwargs) -> None:
        self.b: int = kwargs.get('b', 2)
        self.c: ClassA = ClassA(**kwargs)
        self.d: ClassA = ClassA(**kwargs)

def encoder(obj) -> str | dict:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj.__dict__

print(ClassB())
print(json.dumps(ClassB(), default=encoder, indent=4))
ff=json.loads('{"b":2,"c":{"a":1,"dt":"2022-11-29T21:23:56.589922+07:00"},"d":{"a":1,"dt":"2022-11-29T21:23:56.589922+07:00"}}')
a = ClassB(**ff)
print(a)

print(json.loads("{'a': 1, 'b': {'c': 2}}"))
