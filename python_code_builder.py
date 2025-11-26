# coding=utf-8
# Copyright (c) 2025 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import sys
from collections import OrderedDict
from enum import Enum
from itertools import chain
from typing import Iterable, List, Mapping, MutableMapping, Optional, Sequence, Text, Union

if sys.version_info < (3,):
    import __builtin__ as builtins
else:
    import builtins


class Expression(object):
    def names_read(self):
        # type: () -> Iterable[str]
        for name in tuple():
            yield name

    def to_source(self):
        # type: () -> str
        raise NotImplementedError


class Constant(Expression):
    def __init__(
            self,
            value,  # type: Union[int, float, Text, str, bytes, Ellipsis, None]
    ):
        self.value = value  # type: Union[int, float, Text, str, bytes, Ellipsis, None]

    def to_source(self):  # type: () -> str
        return repr(self.value)


class Slice(Expression):
    def __init__(
            self,
            start=None,  # type: Optional[Expression]
            stop=None,  # type: Optional[Expression]
            step=None,  # type: Optional[Expression]
    ):
        self.start = start  # type: Optional[int]
        self.stop = stop  # type: Optional[int]
        self.step = step  # type: Optional[int]

    def to_source(self):  # type: () -> str
        if self.start is not None:
            if self.stop is not None:
                if self.step is not None:
                    return '%s:%s:%s' % (self.start.to_source(), self.stop.to_source(), self.step.to_source())
                else:
                    return '%s:%s' % (self.start.to_source(), self.stop.to_source())
            else:
                if self.step is not None:
                    return '%s::%s' % (self.start.to_source(), self.step.to_source())
                else:
                    return '%s:' % (self.start.to_source(),)
        else:
            if self.stop is not None:
                if self.step is not None:
                    return ':%s:%s' % (self.stop.to_source(), self.step.to_source())
                else:
                    return ':%s' % (self.stop.to_source(),)
            else:
                if self.step is not None:
                    return '::%s' % (self.step.to_source(),)
                else:
                    return ':'


class LoadName(Expression):
    def __init__(
            self,
            name,  # type: str
    ):
        self.name = name  # type: str

    def names_read(self):
        yield self.name

    def to_source(self):  # type: () -> str
        return self.name


class UnaryOperator(Enum):
    INVERT = '~'
    NOT = 'not'
    UNARY_ADD = '+'
    UNARY_SUB = '-'


class UnaryOperation(Expression):
    def __init__(
            self,
            operator,  # type: UnaryOperator
            operand,  # type: Expression
    ):
        self.operator = operator  # type: UnaryOperator
        self.operand = operand  # type: Expression

    def names_read(self):
        for name in self.operand.names_read():
            yield name

    def to_source(self):  # type: () -> str
        return '(%s %s)' % (self.operator.value, self.operand.to_source())


class BinaryOperator(Enum):
    AND = 'and'
    OR = 'or'
    ADD = '+'
    SUB = '-'
    MULT = '*'
    MAT_MULT = '@'
    DIV = '/'
    MOD = '%'
    POW = '**'
    LEFT_SHIFT = '<<'
    RIGHT_SHIFT = '>>'
    BITWISE_OR = '|'
    BITWISE_XOR = '^'
    BITWISE_AND = '&'
    FLOOR_DIV = '//'
    EQ = '=='
    NOT_EQ = '!='
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    IS = 'is'
    IS_NOT = 'is not'
    IN = 'in'
    NOT_IN = 'not in'


class BinaryOperation(Expression):
    def __init__(
            self,
            left,  # type: Expression
            operator,  # type: BinaryOperator
            right,  # type: Expression
    ):
        self.left = left  # type: Expression
        self.operator = operator  # type: BinaryOperator
        self.right = right  # type: Expression

    def names_read(self):
        for name in self.left.names_read():
            yield name

        for name in self.right.names_read():
            yield name

    def to_source(self):  # type: () -> str
        return '(%s %s %s)' % (self.left.to_source(), self.operator.value, self.right.to_source())


class GetAttribute(Expression):
    def __init__(
            self,
            expression,  # type: Expression
            attribute,  # type: str
    ):
        self.expression = expression  # type: Expression
        self.attribute = attribute  # type: str

    def names_read(self):
        for name in self.expression.names_read():
            yield name

    def to_source(self):  # type: () -> str
        return '%s.%s' % (self.expression.to_source(), self.attribute)


class GetItem(Expression):
    def __init__(
            self,
            expression,  # type: Expression
            key,  # type: Expression
    ):
        self.expression = expression  # type: Expression
        self.key = key  # type: Expression

    def names_read(self):
        for name in self.expression.names_read():
            yield name

        for name in self.key.names_read():
            yield name

    def to_source(self):  # type: () -> str
        return '%s[%s]' % (self.expression.to_source(), self.key.to_source())


class Tuple(Expression):
    def __init__(
            self,
            elements,  # type: Sequence[Expression]
    ):
        self.elements = elements  # type: Sequence[Expression]

    def names_read(self):
        for element in self.elements:
            for name in element.names_read():
                yield name

    def to_source(self):  # type: () -> str
        if not self.elements:
            return 'tuple()'
        elif len(self.elements) == 1:
            return '(%s,)' % (self.elements[0].to_source(),)
        else:
            return '(%s)' % (', '.join(element.to_source() for element in self.elements),)


class Call(Expression):
    def __init__(
            self,
            function,  # type: Expression
            arguments,  # type: Sequence[Expression]
            keywords,  # type: Mapping[str, Expression]
    ):
        self.function = function  # type: Expression
        self.arguments = arguments  # type: Sequence[Expression]
        self.keywords = keywords  # type: Mapping[str, Expression]

    def names_read(self):
        for name in self.function.names_read():
            yield name

        for argument in self.arguments:
            for name in argument.names_read():
                yield name

        for keyword_value in self.keywords.values():
            for name in keyword_value.names_read():
                yield name

    def to_source(self):  # type: () -> str
        return '%s(%s)' % (
            self.function.to_source(),
            ', '.join(
                chain(
                    (argument.to_source() for argument in self.arguments),
                    (
                        '%s=%s' % (keyword_name, keyword_value.to_source())
                        for keyword_name, keyword_value in self.keywords.items()
                    )
                )
            )
        )


class StatementContainer(object):
    def __init__(
            self,
            parent  # type: Optional[StatementContainer]
    ):
        self.parent = parent  # type: Optional[StatementContainer]
        self.statements = []  # type: List[Statement]

    def is_name_defined(
            self,
            name,  # type: str
    ):
        for ancestor_with_symbol_table in walk_symbol_tables(self):
            if name in ancestor_with_symbol_table.names_to_definitions_and_uses:
                return True

        return False

    def add_name_read(
            self,
            name,  # type: str
            statement,  # type: Statement
    ):
        for ancestor_with_symbol_table in walk_symbol_tables(self):
            if name in ancestor_with_symbol_table.names_to_definitions_and_uses:
                ancestor_with_symbol_table.names_to_definitions_and_uses[name].append(NameRead(statement=statement))
                break
        else:
            raise ValueError('Name %s is not defined' % name)

    def add_name_definition_or_write(
            self,
            name,  # type: str
            statement,  # type: Statement
    ):
        for ancestor_with_symbol_table in walk_symbol_tables(self):
            if name in ancestor_with_symbol_table.names_to_definitions_and_uses:
                ancestor_with_symbol_table.names_to_definitions_and_uses[name].append(NameWrite(statement=statement))
            else:
                ancestor_with_symbol_table.names_to_definitions_and_uses[name] = [NameDefinition(statement=statement)]


class NameDefinitionOrUse(object):
    def __init__(
            self,
            statement  # type: Statement
    ):
        self.statement = statement  # type: Statement


class NameDefinition(NameDefinitionOrUse):
    def __init__(
            self,
            statement  # type: Statement
    ):
        NameDefinitionOrUse.__init__(self, statement=statement)


class NameRead(NameDefinitionOrUse):
    def __init__(
            self,
            statement  # type: Statement
    ):
        NameDefinitionOrUse.__init__(self, statement=statement)


class NameWrite(NameDefinitionOrUse):
    def __init__(
            self,
            statement  # type: Statement
    ):
        NameDefinitionOrUse.__init__(self, statement=statement)


def walk_symbol_tables(start):
    # type: (StatementContainer) -> Iterable[StatementContainerWithSymbolTable]
    ancestor = start
    while ancestor is not None:
        if isinstance(ancestor, StatementContainerWithSymbolTable):
            yield ancestor
        ancestor = ancestor.parent


class StatementContainerWithSymbolTable(StatementContainer):
    def __init__(
            self,
            parent  # type: Optional[StatementContainer]
    ):
        StatementContainer.__init__(self, parent=parent)
        self.names_to_definitions_and_uses = OrderedDict()  # type: MutableMapping[str, List[NameDefinitionOrUse]]


def get_indent(indent_level):
    # type: (int) -> str
    return '    ' * indent_level


class Statement(object):
    def __init__(
            self,
            container  # type: StatementContainer
    ):
        self.container = container  # type: StatementContainer
        self.container.statements.append(self)

    def to_source(self, indent_level=0):
        # type: (int) -> str
        raise NotImplementedError


class Module(StatementContainerWithSymbolTable):
    class InitializeBuiltins(Statement):
        """Dummy Statement used to initialize builtins in a Module"""

        def __init__(
                self,
                container,  # type: Module
        ):
            Statement.__init__(self, container=container)

            for builtin in vars(builtins):
                container.add_name_definition_or_write(builtin, self)

        def to_source(self, indent_level=0):  # type: (int) -> str
            return ''

    def __init__(self):
        StatementContainerWithSymbolTable.__init__(self, parent=None)
        Module.InitializeBuiltins(container=self)

    def to_source(self):
        # type: () -> str
        def collect_all_statement_to_source():
            for statement in self.statements:
                statement_to_source = statement.to_source(indent_level=0)
                if statement_to_source:
                    yield statement_to_source

        return '\n'.join(collect_all_statement_to_source())


class Function(StatementContainerWithSymbolTable, Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            name,  # type: str
            args,  # type: Sequence[str]
            varargs,  # type: Optional[str]
            kwonlyargs,  # type: Sequence[str]
            varkwargs,  # type: Optional[str]
            decorators,  # type: Sequence[Union[LoadName, Call]]
    ):
        StatementContainerWithSymbolTable.__init__(self, parent=container)
        Statement.__init__(self, container=container)

        self.name = name  # type: str
        self.args = args  # type: Sequence[str]
        self.varargs = varargs  # type: Optional[str]
        self.kwonlyargs = kwonlyargs  # type: Sequence[str]
        self.varkwargs = varkwargs  # type: Optional[str]
        self.decorators = decorators  # type: Sequence[Union[LoadName, Call]]

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            for decorator in decorators:
                for name_read in decorator.names_read():
                    ancestor_with_symbol_table.add_name_read(name_read, self)
            ancestor_with_symbol_table.add_name_definition_or_write(name, self)
            break

        for arg in args:
            self.add_name_definition_or_write(arg, self)

        if varargs is not None:
            self.add_name_definition_or_write(varargs, self)

        for kwonlyarg in kwonlyargs:
            self.add_name_definition_or_write(kwonlyarg, self)

        if varkwargs is not None:
            self.add_name_definition_or_write(varkwargs, self)

    def to_source(self, indent_level=0):  # type: (int) -> str
        decorator_lines = (
            '%s@%s' % (get_indent(indent_level=indent_level), decorator.to_source())
            for decorator in self.decorators
        )

        definition_lines = (
            '%sdef %s(%s):' % (
                get_indent(indent_level=indent_level),
                self.name,
                ', '.join(
                    chain(
                        self.args,
                        (self.varargs,) if self.varargs is not None else (),
                        self.kwonlyargs,
                        (self.varkwargs,) if self.varkwargs is not None else (),
                    )
                )
            ),
        )

        if self.statements:
            body_lines = (
                statement.to_source(indent_level=indent_level + 1)
                for statement in self.statements
            )
        else:
            body_lines = ('%spass' % (get_indent(indent_level=indent_level + 1),),)

        return '\n'.join(chain(decorator_lines, definition_lines, body_lines))


class Class(StatementContainerWithSymbolTable, Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            name,  # type: str
            bases,  # type: Sequence[Expression]
            decorators,  # type: Sequence[Union[LoadName, Call]]
    ):
        StatementContainerWithSymbolTable.__init__(self, parent=container)
        Statement.__init__(self, container=container)

        self.name = name  # type: str
        self.bases = bases  # type: Sequence[Expression]
        self.decorators = decorators  # type: Sequence[Union[LoadName, Call]]

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            for base in bases:
                for name_read in base.names_read():
                    ancestor_with_symbol_table.add_name_read(name_read, self)

            for decorator in decorators:
                for name_read in decorator.names_read():
                    ancestor_with_symbol_table.add_name_read(name_read, self)

            ancestor_with_symbol_table.add_name_definition_or_write(name, self)

            break

    def to_source(self, indent_level=0):  # type: (int) -> str
        decorator_lines = (
            '%s@%s' % (get_indent(indent_level=indent_level), decorator.to_source())
            for decorator in self.decorators
        )

        definition_lines = (
            '%sclass %s(%s):' % (
                get_indent(indent_level=indent_level),
                self.name,
                ', '.join(base.to_source() for base in self.bases)
            ),
        )

        if self.statements:
            body_lines = (
                statement.to_source(indent_level=indent_level + 1)
                for statement in self.statements
            )
        else:
            body_lines = ('%spass' % (get_indent(indent_level=indent_level + 1),),)

        return '\n'.join(chain(decorator_lines, definition_lines, body_lines))


class Assign(Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            name,  # type: str
            value,  # type: Expression
    ):
        Statement.__init__(self, container=container)

        self.name = name  # type: str
        self.value = value  # type: Expression

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            for name_read in value.names_read():
                ancestor_with_symbol_table.add_name_read(name_read, self)
            ancestor_with_symbol_table.add_name_definition_or_write(name, self)
            break

    def to_source(self, indent_level=0):
        return '%s%s = %s' % (get_indent(indent_level=indent_level), self.name, self.value.to_source())


class SetItem(Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            expression,  # type: Expression
            key,  # type: Expression
            value,  # type: Expression
    ):
        Statement.__init__(self, container=container)

        self.expression = expression  # type: Expression
        self.key = key  # type: Expression
        self.value = value  # type: Expression

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            for name_read in value.names_read():
                ancestor_with_symbol_table.add_name_read(name_read, self)

            for name_read in expression.names_read():
                ancestor_with_symbol_table.add_name_definition_or_write(name_read, self)

            for name_read in key.names_read():
                ancestor_with_symbol_table.add_name_read(name_read, self)

            break

    def to_source(self, indent_level=0):  # type: (int) -> str
        return '%s%s[%s] = %s' % (get_indent(indent_level=indent_level), self.expression.to_source(),
                                  self.key.to_source(), self.value.to_source())


class Import(Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            module,  # type: str
            alias=None,  # type: Optional[str]
    ):
        Statement.__init__(self, container=container)

        self.module = module  # type: str
        self.alias = alias  # type: Optional[str]

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            if alias is not None:
                ancestor_with_symbol_table.add_name_definition_or_write(alias, self)
            else:
                module_first_component = self.module.split('.')[0]
                # Have we defined this name yet?
                if not ancestor_with_symbol_table.is_name_defined(module_first_component):
                    ancestor_with_symbol_table.add_name_definition_or_write(module_first_component, self)
            break

    def to_source(self, indent_level=0):  # type: (int) -> str
        if self.alias is not None:
            return '%simport %s as %s' % (get_indent(indent_level=indent_level), self.module, self.alias)
        else:
            return '%simport %s' % (get_indent(indent_level=indent_level), self.module)


class ImportFrom(Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            module,  # type: str
            names_to_aliases,  # type: Mapping[str, str]
    ):
        if not names_to_aliases:
            raise ValueError('Empty names_to_aliases')

        Statement.__init__(self, container=container)

        self.module = module  # type: str
        self.names_to_aliases = names_to_aliases  # type: Mapping[str, str]

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            for alias in self.names_to_aliases.values():
                ancestor_with_symbol_table.add_name_definition_or_write(alias, self)
            break

    def to_source(self, indent_level=0):
        return '%sfrom %s import %s' % (
            get_indent(indent_level=indent_level),
            self.module,
            ', '.join(
                (
                    '%s as %s' % (name, alias) if name != alias else name
                    for name, alias in self.names_to_aliases.items()
                )
            )
        )


class Return(Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            value,  # type: Optional[Expression]
    ):
        Statement.__init__(self, container)
        self.value = value

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            if value is not None:
                for name in value.names_read():
                    ancestor_with_symbol_table.add_name_read(name, self)
            break

    def to_source(self, indent_level=0):  # type: (int) -> str
        return '%sreturn %s' % (get_indent(indent_level=indent_level), self.value.to_source())


class NameReadInLoop(NameRead):
    def __init__(
            self,
            statement  # type: Statement
    ):
        if not isinstance(statement.container, LoopStatementContainer):
            raise ValueError('Statement is not in a loop')
        NameRead.__init__(self, statement=statement)


class NameWriteInLoop(NameWrite):
    def __init__(
            self,
            statement  # type: Statement
    ):
        if not isinstance(statement.container, LoopStatementContainer):
            raise ValueError('Statement is not in a loop')
        NameWrite.__init__(self, statement=statement)


class LoopStatementContainer(StatementContainerWithSymbolTable):
    def __init__(
            self,
            parent  # type: Optional[StatementContainer]
    ):
        StatementContainerWithSymbolTable.__init__(self, parent=parent)

    def add_name_definition_or_write(
            self,
            name,  # type: str
            statement,  # type: Statement
    ):
        if not isinstance(statement.container, LoopStatementContainer):
            raise ValueError('Statement is not in a loop')

        # Has this name been defined in an immediate outer scope?
        # If so, add a NameWriteInLoop there
        # If not, add a NameDefinition in the loop (the variable won't be available outside the loop)
        for ancestor_with_symbol_table in walk_symbol_tables(self.parent):
            if name in ancestor_with_symbol_table.names_to_definitions_and_uses:
                ancestor_with_symbol_table.names_to_definitions_and_uses[name].append(NameWriteInLoop(statement))
            else:
                self.names_to_definitions_and_uses[name] = [NameDefinition(statement)]
            break

    def add_name_read(
            self,
            name,  # type: str
            statement,  # type: Statement
    ):
        # Is the name defined in the loop?
        # If so, add a NameRead in the loop
        if name in self.names_to_definitions_and_uses:
            self.names_to_definitions_and_uses[name].append(NameRead(statement))
        # Is the name defined in an outer scope?
        # If so, add a NameReadInLoop there
        else:
            for ancestor_with_symbol_table in walk_symbol_tables(self.parent):
                if name in ancestor_with_symbol_table.names_to_definitions_and_uses:
                    ancestor_with_symbol_table.names_to_definitions_and_uses[name].append(NameReadInLoop(statement))
                    break
            else:
                raise ValueError('Name %s is not defined' % name)


class For(LoopStatementContainer, Statement):
    def __init__(
            self,
            container,  # type: StatementContainer
            target,  # type: str
            iterable,  # type: Expression
    ):
        # target cannot be defined in an outer scope
        for ancestor_with_symbol_table in walk_symbol_tables(container):
            if ancestor_with_symbol_table.is_name_defined(target):
                raise ValueError('target cannot be defined in an outer scope')
            break

        LoopStatementContainer.__init__(self, parent=container)
        Statement.__init__(self, container=container)

        self.target = target  # type: str
        self.iterable = iterable  # type: Expression

        for ancestor_with_symbol_table in walk_symbol_tables(container):
            for name_read in iterable.names_read():
                ancestor_with_symbol_table.add_name_read(name_read, self)
            break

        # define target in the loop scope
        self.names_to_definitions_and_uses[target] = [NameDefinition(self)]

    def to_source(self, indent_level=0):  # type: (int) -> str
        header_lines = (
            '%sfor %s in %s:' % (get_indent(indent_level=indent_level), self.target, self.iterable.to_source()),
        )

        if self.statements:
            body_lines = (
                statement.to_source(indent_level=indent_level + 1)
                for statement in self.statements
            )
        else:
            body_lines = ('%spass' % (get_indent(indent_level=indent_level + 1),),)

        return '\n'.join(chain(header_lines, body_lines))
