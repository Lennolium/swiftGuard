#!/usr/bin/env python3

"""
models.py: TODO: Headline...

TODO: Description...
"""
from __future__ import annotations

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2025-01-27"
__status__ = "Prototype/Development/Production"

# Imports.
import logging
import weakref

import shiboken6.Shiboken

# Child logger.
LOGGER = logging.getLogger(__name__)


class Singleton(type):
    """
    Singleton metaclass for creating singleton classes.
    It ensures that only one instance of a class exists. Also by using
    the `instance` property, you can get the instance without creating
    a new one. If the instance does not exist, `None` will be returned.
    We use weakref so the instance can be garbage can be garbage
    collected if there are no references to it.

    **Usage:**

    - import Singleton
    - class MyClass(metaclass=Singleton): ...

    *Create an instance:*

    - a = MyClass()
    - b = MyClass()
    - print(a is b)  # True

    *Get the same instance in another module:*

    - from module import MyClass
    - c = MyClass.instance


    :cvar __instances: Dictionary for storing the instances of the
        classes. The key is the class and the value is the instance.
    :type __instances: weakref.WeakValueDictionary

    """

    __instances = weakref.WeakValueDictionary()

    def __call__(cls, *args, **kwargs) -> Singleton:
        """
        Call the constructor of the class. If the instance does not
        exist, we will create a new one. Otherwise, we will return the
        existing instance.

        :param args: Arguments for the constructor.
        :type args: tuple | list | None
        :param kwargs: Keyword arguments for the constructor.
        :type kwargs: dict | None
        :return: The singleton instance of the class.
        :rtype: Singleton
        """

        if cls not in cls.__instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls.__instances[cls] = instance

        else:
            LOGGER.debug(f"Only one instance of the {cls.__name__} instance"
                         "can be created. Returning the existing instance."
                         )

        return cls.__instances[cls]

    @property
    def instance(cls) -> Singleton:
        """
        Get the instance of the class. If the instance does not exist,
        we will NOT create a new one. Call the constructor directly.

        :return: The singleton instance of the class.
        :rtype: Singleton | None
        """

        return cls.__instances.get(key=cls, default=None)

    @classmethod
    def all_instances(cls) -> dict[str, Singleton]:
        """
        Get all instances of the class. The key is the class name and
        the value is the instance.

        :return: All instances that are created.
        :rtype: dict[str, Singleton]
        """

        res = {}

        for key, value in cls.__instances.items():
            res[key.__name__] = value

        return res


class SingletonQt(Singleton, type(shiboken6.Shiboken.Object)):
    """
    Singleton metaclass for creating singleton classes with Qt objects.
    This is metaclass has to be used for classes that inherit from Qt
    objects, e.g. QThread, QApplication, etc.
    """
    ...
