"""Test class-interference Extension"""
# pylint: disable=no-member,missing-function-docstring

from class_interference import Extension, inject, apply_extensions


class PatchBase:
    """Base patched class"""

    def get_instance_string(self) -> str:
        return "Instance"

    @classmethod
    def get_class_string(cls) -> str:
        return "Class"

    @staticmethod
    def get_static_string() -> str:
        return "Static"


class PatchBaseExtension(PatchBase, Extension):
    """Extended version of base class"""

    @inject
    def get_instance_string(self) -> str:
        return self.reverse_string_instance(self.super_ext.get_instance_string())

    @classmethod
    @inject
    def get_class_string(cls) -> str:
        return cls.reverse_string_class(cls.super_ext.get_class_string())

    @staticmethod
    @inject
    def get_static_string() -> str:
        return PatchBaseExtension.reverse_string_static(PatchBase.super_ext.get_static_string())  # type: ignore

    def reverse_string_instance(self, string: str) -> str:  # noqa
        return string[::-1]

    @classmethod
    def reverse_string_class(cls, string: str) -> str:
        return string[::-1]

    @staticmethod
    def reverse_string_static(string: str) -> str:
        return string[::-1]


apply_extensions(PatchBaseExtension)


def test_instance_method_injection():
    assert PatchBase().get_instance_string() == "ecnatsnI"


def test_class_method_injection():
    assert PatchBase.get_class_string() == "ssalC"


def test_static_method_injection():
    assert PatchBase.get_static_string() == "citatS"
