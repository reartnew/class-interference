from __future__ import annotations

import typing as t

__all__ = [
    "Extension",
]

# (Base; Derived)
_known_derivatives: t.List[t.Tuple[type, t.Type[Extension]]] = []
_extension_attr: str = "__extendable_replacement__"


class BaseSuperExt(object):
    _funcs: t.Dict[str, t.Callable]

    def __getattr__(self, item: str) -> t.Callable:
        """Base unbound function getter"""
        unbound_func: t.Optional[t.Callable] = self._funcs.get(item)
        if unbound_func is None:
            raise AttributeError(f"<super_ext>: {item}")
        return unbound_func

    def __iter__(self) -> t.Iterator[str]:
        return self._funcs.__iter__()


class ClassSuperExt(BaseSuperExt):

    def __init__(self) -> None:
        self._funcs: t.Dict[str, t.Callable] = {}

    def __setitem__(self, key: str, value: t.Callable) -> None:
        assert key not in self._funcs, f"Name collision: {key}"
        self._funcs[key] = value

    def __get__(self, instance, owner) -> BaseSuperExt:
        # Create instance proxy to give access to new instance methods
        return self if instance is None else InstanceSuperExt(instance=instance, funcs=self._funcs)


class InstanceSuperExt(BaseSuperExt):
    # Instance method proxy object
    def __init__(self, instance: t.Any, funcs: t.Dict[str, t.Callable]) -> None:
        self._instance = instance
        self._funcs: t.Dict[str, t.Callable] = funcs

    def __getattr__(self, item: str) -> t.Callable:
        # Make it work like self
        return _bind_unbound_func(
            unbound_func=super().__getattr__(item),
            bind_instance=self._instance,
            source_class=self._instance.__class__,
        )


class Extension(object):
    """Monkey patch utility for library classes.
    Usage:

        class LibraryClass:
            def library_method(self, *args, **kwargs):
                return None

        class LibraryClassExtension(LibraryClass, Extension):
            @Extension.inject
            def library_method(self, *args, **kwargs):
                original_value = self.super_ext.library_method(*args, **kwargs)
                if original_value is None:
                    raise ValueError
                return original_value

        Extension.extend_all()

        if __name__ == "__main__":
            library_class_instance = LibraryClass()
            library_class_instance.library_method()  # raises ValueError

        """
    super_ext: ClassSuperExt

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        assert len(cls.__bases__) == 2
        assert Extension in cls.__bases__
        for base_class in cls.__bases__:  # type: type
            if Extension is not base_class:
                non_extendable_base_class: type = base_class
                break
        else:
            raise TypeError(f"Non-extendable bases: {cls.__bases__}")
        cls.super_ext = ClassSuperExt()
        _known_derivatives.append((non_extendable_base_class, cls))
        for derived_attr_name in dir(cls):
            derived_attr_value = getattr(cls, derived_attr_name)
            # Avoid SuperExt objects to prevent getting stuck into their __getattr__ calls
            if isinstance(derived_attr_value, ClassSuperExt):
                continue
            # Check method injection mark
            if not getattr(derived_attr_value, _extension_attr, False):
                continue
            # Check super implementation presence
            base_attr_value = getattr(non_extendable_base_class, derived_attr_name, None)
            if base_attr_value is not None:
                # Remember, if any
                cls.super_ext[base_attr_value.__name__] = base_attr_value


def __create_super_getattr(old_class, new_class):
    """Derivative closure. Make superclass able to access subclass' unique methods"""
    # Save previous __getattr__ implementation, if any
    _old_base_getattr = getattr(old_class, "__getattr__", None)

    def _new_base_getattr(self, attr_name):
        # __getattr__ has not yet been defined
        if _old_base_getattr is None:
            return _bind_unbound_func(
                unbound_func=getattr(new_class, attr_name),
                bind_instance=self,
                source_class=new_class,
            )
        try:
            # Maybe super __getattr__ works?
            return _old_base_getattr(self, attr_name)
        except AttributeError:
            return _bind_unbound_func(
                unbound_func=getattr(new_class, attr_name),
                bind_instance=self,
                source_class=new_class,
            )

    return _new_base_getattr


def _bind_unbound_func(*, unbound_func: t.Callable, bind_instance: t.Any, source_class: type) -> t.Callable:
    """Simulate method binding"""
    maybe_derived_unbound_special_wrapper = source_class.__dict__.get(unbound_func.__name__)
    if isinstance(maybe_derived_unbound_special_wrapper, (staticmethod, classmethod)):
        bound_func = unbound_func
    else:
        def bound_func(*args, **kwargs):
            return unbound_func(bind_instance, *args, **kwargs)

    return bound_func


def inject(func: t.Callable) -> t.Callable:
    # Just mark using special attribute
    setattr(func, _extension_attr, True)
    return func


def extend_all() -> None:
    """Apply patches for all registered classes"""
    for base_class, derivative_class in _known_derivatives:
        # Give base an accessor to original methods
        setattr(base_class, "super_ext", derivative_class.super_ext)
        # Replace overridden methods
        for k in derivative_class.super_ext:
            setattr(base_class, k, getattr(derivative_class, k))
        # Patch __getattr__ to give access to new methods
        setattr(base_class, "__getattr__", __create_super_getattr(base_class, derivative_class))
