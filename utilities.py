from enum import Enum, EnumMeta, _EnumDict


#custom enum metaclass so that calling MyEnum.MY_VALUE returns b'MY_VALUE'
#str method should return just the name of the enum value
class MyEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, oldclassdict):
        newclassdict = _EnumDict()
        newclassdict._cls_name = cls
        for key, value in oldclassdict.items():
            if value == ():
                value = key.encode('utf-8')
            newclassdict[key] = value
        return super().__new__(metacls, cls, bases, newclassdict)
class MyEnum(bytes, Enum, metaclass=MyEnumMeta):
    """base class for enum where values are bytes of the enum name"""
    def __str__(self):
        return self.name