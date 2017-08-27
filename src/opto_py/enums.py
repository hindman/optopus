from collections import OrderedDict

class Enum(object):

    def __init__(self, enum_name, *members):
        self._enum_name = enum_name
        self._members = OrderedDict(
            (name, EnumMember(enum_name, name, value))
            for value, name in enumerate(members)
        )
        self._rmembers = OrderedDict(
            (em.value, em)
            for em in self._members.values()
        )

    def __iter__(self):
        return iter(self._members.values())

    def __getattr__(self, name):
        if name in self._members:
            return self._members[name]
        else:
            raise AttributeError(name)

    def __call__(self, value):
        if value in self._rmembers:
            return self._rmembers[value]
        else:
            raise ValueError(value)

class EnumMember(object):

    def __init__(self, enum_name, name, value):
        self.enum_name = enum_name
        self.name = name
        self.value = value

    def __str__(self):
        fmt = '{}({}, {!r})'
        msg = fmt.format(self.enum_name, self.name, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return not self == other

OptType = Enum('OptType', 'LONG', 'SHORT', 'POS', 'WILD')
PhraseType = Enum('PhraseType', 'OPT', 'POS', 'PHRASE', 'WILD', 'ZONE')
PhraseLogicType = Enum('PhraseLogicType', 'AND', 'OR')

