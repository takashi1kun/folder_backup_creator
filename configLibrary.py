from config_file import ConfigFile, ParsingError
from collections import OrderedDict
from typing import Callable

import os






class Field:
    def __init__(self, key: str = None,*, help: str = "", default: str = ""):
        self.key = key
        self.help = help
        self.default = default

    def __get__(self, instance, owner):
        if instance:
            return instance.get_var(self.key)
        return self

    def __set__(self, instance, value):
        if instance:
            instance.set_var(self.key, value)

class StringField(Field):
    pass
class DeclarativeValuesMetaclass(type):
    """
    Collect Value objects declared on the base classes
    """

    def __new__(self, class_name, bases, attrs):
        # Collect values from current class and all bases.
        values = OrderedDict()

        # Walk through the MRO and add values from base class.
        for base in reversed(bases):
            if hasattr(base, "_declared_values"):
                values.update(base._declared_values)

        for key, value in attrs.items():
            if isinstance(value, Field):
                if value.key and key != value.key:
                    raise AttributeError(
                        "Don't explicitly set keys when declaring values"
                    )
                value.key = key
                #value.section_name = values.get('section_name', default='')
                #value.configuration_file = values.get('configuration_file', default='')
                values.update({key: value})

        attrs["_declared_values"] = values

        return super(DeclarativeValuesMetaclass, self).__new__(
            self, class_name, bases, attrs
        )

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        # Remember the order that values are defined.
        return OrderedDict()

class SettingsSection(metaclass=DeclarativeValuesMetaclass):
    def __init__(self, section_name: str = None,*,configuration_file=""):
        self.section_name = section_name
        self.configuration_file = configuration_file
        self.config: ConfigFile = None

    def get_var(self, key):
        value = self.config.get("%s.%s" % (self.section_name, key), default=False)
        if not value and self._declared_values[key].default:
            self.set_var(key, self._declared_values[key].default)
            value = self.config.get("%s.%s" % (self.section_name, key), default=False)
        return value

    def set_var(self, key, value):
        self.config.set("%s.%s" % (self.section_name, key), value)
        self.config.save()


class DeclarativeValuesMetaclassSections(type):
    """
    Collect Value objects declared on the base classes
    """

    def __new__(self, class_name, bases, attrs):
        # Collect values from current class and all bases.
        values = OrderedDict()

        # Walk through the MRO and add values from base class.
        for base in reversed(bases):
            if hasattr(base, "_declared_values"):
                values.update(base._declared_values)

        for key, value in attrs.items():
            if isinstance(value, SettingsSection):
                if value.section_name and key != value.section_name:
                    raise AttributeError(
                        "Don't explicitly set keys when declaring values"
                    )
                value.section_name = key
                #value.configuration_file = values.get('configuration_file', default='')
                #value.config = values.get('config', default='')
                values.update({key: value})

        attrs["_declared_values"] = values

        return super(DeclarativeValuesMetaclassSections, self).__new__(
            self, class_name, bases, attrs
        )

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        # Remember the order that values are defined.
        return OrderedDict()

class SettingsController(metaclass=DeclarativeValuesMetaclassSections):
    def __init__(self,configuration_file):
        self.configuration_file = configuration_file
        if not os.path.isfile(configuration_file):
            newfile = open(configuration_file, 'a+')
            newfile.write("")
            newfile.close()
        self.config = ConfigFile(configuration_file)
        for key in self._declared_values.keys():
            value = self._declared_values[key]
            value.config = self.config
            value.configuration_file = configuration_file
            for key2 in value._declared_values.keys():
                value2 = value._declared_values[key2]
                value2.config = self.config
                value2.configuration_file = self.configuration_file
                if not value2 and value2.default:
                    value.set_var(key2, value2.default)

