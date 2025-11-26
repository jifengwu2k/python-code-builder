# `python-code-builder`

A library for dynamically building Python code with strong, explicit scoping and symbol tracking.

This is work in progress. Currently, the following constructs are supported:

- Module
- Expression
  - Constant
  - LoadName
  - UnaryOperation
  - BinaryOperation
  - GetAttribute
  - GetItem
  - Call
- Statement
  - Function
  - Assign
  - Import
  - ImportFrom
  - Return
  - For

## Features

- Build expressions and statements as objects, not strings.
- Manage symbol tables for modules, functions, and loops; catch scoping bugs at construction time.

## Installation

```bash
pip install python-code-builder
```

## Example Usage

```python
# coding=utf-8
from __future__ import print_function
from python_code_builder import *

mod = Module()

Import(mod, module='math')
Assign(mod, 'x', Constant(3))

func = Function(mod, name='foo', args=('a',), varargs=None, kwonlyargs=(), varkwargs=None, decorators=())
Assign(func, 'y', BinaryOperation(LoadName('a'), BinaryOperator.ADD, LoadName('x')))
loop = For(func, target='item', iterable=Call(LoadName('range'), (Constant(5),), {}))
Assign(loop, 'y', BinaryOperation(LoadName('y'), BinaryOperator.ADD, LoadName('item')))
Return(func, value=LoadName('y'))

print(mod.to_source())
```

Producing:

```
import math
x = 3
def foo(a)
    y = (a + x)
    for item in range(5):
        y = (y + item)
    return y
```

## For-Loop Scoping and Variable Rules

**This library enforces a modern, safe local-scoping model for loop variables - unlike standard Python:**

| Situation                                        | Allowed? | Notes                                         |
|--------------------------------------------------|----------|-----------------------------------------------|
| Using an outer variable as a loop target         | ❌        | Shadowing outer names is not allowed          |
| Reusing the same loop variable name in new loops | ✅        | Each `for` loop gets a fresh, local variable  |
| Accessing a loop variable after the loop ends    | ❌        | Loop variable is not available/leaked outside |

### Examples

#### Disallowed (shadowing an outer name)

```python
# coding=utf-8
from __future__ import print_function
from python_code_builder import *

mod = Module()
Assign(mod, 'x', Constant(42))
Assign(mod, 'foo', Constant('ABC'))
For(mod, target='x', iterable=LoadName('foo'))  # Raises ValueError!
print(mod.to_source())
```

Raises: 

```
ValueError: target cannot be defined in an outer scope
```

#### Allowed (distinct loops, same target name)

```python
# coding=utf-8
from __future__ import print_function
from python_code_builder import *

mod = Module()
Assign(mod, 'foo', Constant('ABC'))
Assign(mod, 'bar', Constant('123'))
For(mod, target='x', iterable=LoadName('foo'))
For(mod, target='x', iterable=LoadName('bar'))  # OK!
print(mod.to_source())
```

Prints:

```
foo = 'ABC'
bar = '123'
for x in foo:
    pass
for x in bar:
    pass
```

Each `x` is _local_ to its own loop; no conflict.

#### Disallowed (leaking target)

```python
# coding=utf-8
from __future__ import print_function
from python_code_builder import *

mod = Module()
Assign(mod, 'foo', Constant('ABC'))
For(mod, target='x', iterable=LoadName('foo'))
Assign(mod, 'last_x', LoadName('x'))  # Raises ValueError!
print(mod.to_source())
```

Raises: 

```
ValueError: Name x is not defined
```

## Why These Rules?

This strict, explicit scoping:

- Prevents accidental overwriting of names
- Ensures code generation won't result in mysterious NameError at runtime
- Reduces bugs caused by Python's sometimes surprising loop-variable leaks

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).