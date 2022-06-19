# class-interference

Monkey patching utilities for classes.

## Installation

```shell
pip install class-interference
```

# Usage example

```python
from class_interference import Extension, inject, extend_all


class LibraryClass:
    def library_method(self, *args, **kwargs):
        return None


class LibraryClassExtension(LibraryClass, Extension):
    @inject
    def library_method(self, *args, **kwargs):
        original_value = self.super_ext.library_method(*args, **kwargs)
        if original_value is None:
            raise ValueError
        return original_value


extend_all()

if __name__ == "__main__":
    library_class_instance = LibraryClass()
    library_class_instance.library_method()  # raises ValueError

```
