from enum import Enum as StdEnum


class ExtendedEnum(StdEnum):
    def __contains__(self, item):
        return item in self.values()

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))
