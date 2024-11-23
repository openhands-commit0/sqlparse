"""This module contains classes representing syntactical elements of SQL."""
import re
from sqlparse import tokens as T
from sqlparse.exceptions import SQLParseError
from sqlparse.utils import imt, remove_quotes

class NameAliasMixin:
    """Implements get_real_name and get_alias."""

    def get_real_name(self):
        """Returns the real name (object name) of this identifier."""
        return self.get_name()

    def get_alias(self):
        """Returns the alias for this identifier or ``None``."""
        return None

class Token:
    """Base class for all other classes in this module.

    It represents a single token and has two instance attributes:
    ``value`` is the unchanged value of the token and ``ttype`` is
    the type of the token.
    """
    __slots__ = ('value', 'ttype', 'parent', 'normalized', 'is_keyword', 'is_group', 'is_whitespace', 'is_newline')

    def __init__(self, ttype, value):
        value = str(value)
        self.value = value
        self.ttype = ttype
        self.parent = None
        self.is_group = False
        self.is_keyword = ttype in T.Keyword
        self.is_whitespace = self.ttype in T.Whitespace
        self.is_newline = self.ttype in T.Newline
        self.normalized = value.upper() if self.is_keyword else value

    def __str__(self):
        return self.value

    def __repr__(self):
        cls = self._get_repr_name()
        value = self._get_repr_value()
        q = '"' if value.startswith("'") and value.endswith("'") else "'"
        return '<{cls} {q}{value}{q} at 0x{id:2X}>'.format(id=id(self), **locals())

    def flatten(self):
        """Resolve subgroups."""
        yield self

    def match(self, ttype, values, regex=False):
        """Checks whether the token matches the given arguments.

        *ttype* is a token type. If this token doesn't match the given token
        type.
        *values* is a list of possible values for this token. The values
        are OR'ed together so if only one of the values matches ``True``
        is returned. Except for keyword tokens the comparison is
        case-sensitive. For convenience it's OK to pass in a single string.
        If *regex* is ``True`` (default is ``False``) the given values are
        treated as regular expressions.
        """
        if ttype is not None and not imt(self, t=ttype):
            return False

        if values is None:
            return True

        if isinstance(values, str):
            values = (values,)

        if regex:
            pattern = '|'.join('(?:{0})'.format(v) for v in values)
            return bool(re.search(pattern, self.normalized if self.is_keyword else self.value, re.IGNORECASE if self.is_keyword else 0))

        if self.is_keyword:
            return self.normalized in [v.upper() for v in values]
        return self.value in values

    def within(self, group_cls):
        """Returns ``True`` if this token is within *group_cls*.

        Use this method for example to check if an identifier is within
        a function: ``t.within(sql.Function)``.
        """
        parent = self.parent
        while parent:
            if isinstance(parent, group_cls):
                return True
            parent = parent.parent
        return False

    def is_child_of(self, other):
        """Returns ``True`` if this token is a direct child of *other*."""
        return self.parent == other

    def has_ancestor(self, other):
        """Returns ``True`` if *other* is in this tokens ancestry."""
        parent = self.parent
        while parent:
            if parent == other:
                return True
            parent = parent.parent
        return False

class TokenList(Token):
    """A group of tokens.

    It has an additional instance attribute ``tokens`` which holds a
    list of child-tokens.
    """
    __slots__ = 'tokens'

    def __init__(self, tokens=None):
        self.tokens = tokens or []
        [setattr(token, 'parent', self) for token in self.tokens]
        super().__init__(None, str(self))
        self.is_group = True

    def __str__(self):
        return ''.join((token.value for token in self.flatten()))

    def __iter__(self):
        return iter(self.tokens)

    def __getitem__(self, item):
        return self.tokens[item]

    def _pprint_tree(self, max_depth=None, depth=0, f=None, _pre=''):
        """Pretty-print the object tree."""
        if max_depth and depth > max_depth:
            return

        indent = ' ' * (depth * 2)
        for token in self.tokens:
            cls = token._get_repr_name()
            value = token._get_repr_value()
            if token.is_group:
                token._pprint_tree(max_depth, depth + 1, f, _pre)
            else:
                f.write('{}{}{} {}\n'.format(_pre, indent, cls, value))

    def get_token_at_offset(self, offset):
        """Returns the token that is on position offset."""
        idx = 0
        for token in self.flatten():
            end = idx + len(token.value)
            if idx <= offset < end:
                return token
            idx = end
        return None

    def flatten(self):
        """Generator yielding ungrouped tokens.

        This method is recursively called for all child tokens.
        """
        for token in self.tokens:
            if token.is_group:
                for t in token.flatten():
                    yield t
            else:
                yield token

    def _token_matching(self, funcs, start=0, end=None, reverse=False):
        """next token that match functions"""
        if not isinstance(funcs, (list, tuple)):
            funcs = (funcs,)

        if end is None:
            end = len(self.tokens)

        tokens = self.tokens[start:end]
        if reverse:
            tokens = reversed(tokens)

        for token in tokens:
            for func in funcs:
                if func(token):
                    return token
        return None

    def token_first(self, skip_ws=True, skip_cm=False):
        """Returns the first child token.

        If *skip_ws* is ``True`` (the default), whitespace
        tokens are ignored.

        if *skip_cm* is ``True`` (default: ``False``), comments are
        ignored too.
        """
        funcs = []
        if skip_ws:
            funcs.append(lambda t: not t.is_whitespace)
        if skip_cm:
            funcs.append(lambda t: not isinstance(t, Comment))
        return self._token_matching(funcs)

    def token_prev(self, idx, skip_ws=True, skip_cm=False):
        """Returns the previous token relative to *idx*.

        If *skip_ws* is ``True`` (the default) whitespace tokens are ignored.
        If *skip_cm* is ``True`` comments are ignored.
        ``None`` is returned if there's no previous token.
        """
        funcs = []
        if skip_ws:
            funcs.append(lambda t: not t.is_whitespace)
        if skip_cm:
            funcs.append(lambda t: not isinstance(t, Comment))
        return self._token_matching(funcs, 0, idx, reverse=True)

    def token_next(self, idx, skip_ws=True, skip_cm=False, _reverse=False):
        """Returns the next token relative to *idx*.

        If *skip_ws* is ``True`` (the default) whitespace tokens are ignored.
        If *skip_cm* is ``True`` comments are ignored.
        ``None`` is returned if there's no next token.
        """
        funcs = []
        if skip_ws:
            funcs.append(lambda t: not t.is_whitespace)
        if skip_cm:
            funcs.append(lambda t: not isinstance(t, Comment))
        return self._token_matching(funcs, idx + 1)

    def token_index(self, token, start=0):
        """Return list index of token."""
        for idx, t in enumerate(self.tokens[start:], start=start):
            if token is t:
                return idx
        return None

    def group_tokens(self, grp_cls, start, end, include_end=True, extend=False):
        """Replace tokens by an instance of *grp_cls*."""
        if not isinstance(start, int):
            start = self.token_index(start)
        if not isinstance(end, int):
            end = self.token_index(end)

        if extend:
            while end < len(self.tokens) - 1:
                if isinstance(self.tokens[end + 1], (Comment, None)):
                    end += 1
                else:
                    break

        if include_end:
            end += 1

        grp = grp_cls(self.tokens[start:end])
        self.tokens[start:end] = [grp]
        return grp

    def insert_before(self, where, token):
        """Inserts *token* before *where*."""
        if not isinstance(where, int):
            where = self.token_index(where)
        token.parent = self
        self.tokens.insert(where, token)

    def insert_after(self, where, token, skip_ws=True):
        """Inserts *token* after *where*."""
        if not isinstance(where, int):
            where = self.token_index(where)
        if skip_ws:
            next_token = self.token_next(where)
            if next_token is not None:
                where = self.token_index(next_token) - 1
        token.parent = self
        self.tokens.insert(where + 1, token)

    def has_alias(self):
        """Returns ``True`` if an alias is present."""
        return self.get_alias() is not None

    def get_alias(self):
        """Returns the alias for this identifier or ``None``."""
        pass

    def get_name(self):
        """Returns the name of this identifier.

        This is either it's alias or it's real name. The returned valued can
        be considered as the name under which the object corresponding to
        this identifier is known within the current statement.
        """
        alias = self.get_alias()
        if alias:
            return alias
        return self.get_real_name()

    def get_real_name(self):
        """Returns the real name (object name) of this identifier."""
        # Return the first token's value as real name
        token = self.token_next(0)
        if token is None:
            return None
        return token.value

    def get_parent_name(self):
        """Return name of the parent object if any.

        A parent object is identified by the first occurring dot.
        """
        dot = self.token_next_by(m=(T.Punctuation, '.'))
        if dot is None:
            return None
        prev_ = self.token_prev(self.token_index(dot))
        if prev_ is None:
            return None
        return prev_.value

    def _get_first_name(self, idx=None, reverse=False, keywords=False, real_name=False):
        """Returns the name of the first token with a name"""
        tokens = self.tokens[idx:] if idx else self.tokens
        if reverse:
            tokens = reversed(tokens)

        for token in tokens:
            if token.ttype in T.Name or (keywords and token.is_keyword):
                return token.get_real_name() if real_name else token.get_name()
            if token.is_group:
                name = token._get_first_name(reverse=reverse, keywords=keywords, real_name=real_name)
                if name is not None:
                    return name
        return None

class Statement(TokenList):
    """Represents a SQL statement."""

    def get_type(self):
        """Returns the type of a statement.

        The returned value is a string holding an upper-cased reprint of
        the first DML or DDL keyword. If the first token in this group
        isn't a DML or DDL keyword "UNKNOWN" is returned.

        Whitespaces and comments at the beginning of the statement
        are ignored.
        """
        first_token = self.token_first()
        if first_token is None:
            return 'UNKNOWN'

        if first_token.ttype in (T.Keyword.DML, T.Keyword.DDL):
            return first_token.normalized
        return 'UNKNOWN'

class Identifier(NameAliasMixin, TokenList):
    """Represents an identifier.

    Identifiers may have aliases or typecasts.
    """

    def is_wildcard(self):
        """Return ``True`` if this identifier contains a wildcard."""
        token = self.token_next_by(t=T.Wildcard)
        return token is not None

    def get_typecast(self):
        """Returns the typecast or ``None`` of this object as a string."""
        marker = self.token_next_by(m=(T.Punctuation, '::'))
        if marker is None:
            return None
        next_ = self.token_next(self.token_index(marker))
        if next_ is None:
            return None
        return next_.value

    def get_ordering(self):
        """Returns the ordering or ``None`` as uppercase string."""
        ordering = self.token_next_by(t=T.Keyword.Order)
        if ordering is None:
            return None
        return ordering.normalized

    def get_array_indices(self):
        """Returns an iterator of index token lists"""
        for token in self.tokens:
            if isinstance(token, SquareBrackets):
                yield token

class IdentifierList(TokenList):
    """A list of :class:`~sqlparse.sql.Identifier`'s."""

    def get_identifiers(self):
        """Returns the identifiers.

        Whitespaces and punctuations are not included in this generator.
        """
        for token in self.tokens:
            if isinstance(token, (Identifier, Function)):
                yield token

class TypedLiteral(TokenList):
    """A typed literal, such as "date '2001-09-28'" or "interval '2 hours'"."""
    M_OPEN = [(T.Name.Builtin, None), (T.Keyword, 'TIMESTAMP')]
    M_CLOSE = (T.String.Single, None)
    M_EXTEND = (T.Keyword, ('DAY', 'HOUR', 'MINUTE', 'MONTH', 'SECOND', 'YEAR'))

class Parenthesis(TokenList):
    """Tokens between parenthesis."""
    M_OPEN = (T.Punctuation, '(')
    M_CLOSE = (T.Punctuation, ')')

class SquareBrackets(TokenList):
    """Tokens between square brackets"""
    M_OPEN = (T.Punctuation, '[')
    M_CLOSE = (T.Punctuation, ']')

class Assignment(TokenList):
    """An assignment like 'var := val;'"""

class If(TokenList):
    """An 'if' clause with possible 'else if' or 'else' parts."""
    M_OPEN = (T.Keyword, 'IF')
    M_CLOSE = (T.Keyword, 'END IF')

class For(TokenList):
    """A 'FOR' loop."""
    M_OPEN = (T.Keyword, ('FOR', 'FOREACH'))
    M_CLOSE = (T.Keyword, 'END LOOP')

class Comparison(TokenList):
    """A comparison used for example in WHERE clauses."""

class Comment(TokenList):
    """A comment."""

class Where(TokenList):
    """A WHERE clause."""
    M_OPEN = (T.Keyword, 'WHERE')
    M_CLOSE = (T.Keyword, ('ORDER BY', 'GROUP BY', 'LIMIT', 'UNION', 'UNION ALL', 'EXCEPT', 'HAVING', 'RETURNING', 'INTO'))

class Over(TokenList):
    """An OVER clause."""
    M_OPEN = (T.Keyword, 'OVER')

class Having(TokenList):
    """A HAVING clause."""
    M_OPEN = (T.Keyword, 'HAVING')
    M_CLOSE = (T.Keyword, ('ORDER BY', 'LIMIT'))

class Case(TokenList):
    """A CASE statement with one or more WHEN and possibly an ELSE part."""
    M_OPEN = (T.Keyword, 'CASE')
    M_CLOSE = (T.Keyword, 'END')

    def get_cases(self, skip_ws=False):
        """Returns a list of 2-tuples (condition, value).

        If an ELSE exists condition is None.
        """
        ELSE = T.Keyword, 'ELSE'
        WHEN = T.Keyword, 'WHEN'
        THEN = T.Keyword, 'THEN'

        results = []
        condition = None
        value = None
        for token in self.tokens:
            if token.match(*WHEN):
                condition = []
            elif token.match(*THEN):
                value = []
            elif token.match(*ELSE):
                condition = None
                value = []
            elif condition is not None and value is None:
                condition.append(token)
            elif value is not None:
                value.append(token)
                if token.is_group and token.tokens[-1].match(T.Keyword, 'END'):
                    results.append((condition, value))
                    condition = None
                    value = None

        if value is not None:
            results.append((condition, value))

        return results

class Function(NameAliasMixin, TokenList):
    """A function or procedure call."""

    def get_parameters(self):
        """Return a list of parameters."""
        parenthesis = self.token_next_by(i=Parenthesis)
        if parenthesis is None:
            return []
        return [token for token in parenthesis.tokens[1:-1]
                if not token.is_whitespace]

    def get_window(self):
        """Return the window if it exists."""
        over = self.token_next_by(m=(T.Keyword, 'OVER'))
        if over is None:
            return None

        over_idx = self.token_index(over)
        window = self.token_next(over_idx)
        if window is None:
            return None

        if isinstance(window, Parenthesis):
            return window
        return None

class Begin(TokenList):
    """A BEGIN/END block."""
    M_OPEN = (T.Keyword, 'BEGIN')
    M_CLOSE = (T.Keyword, 'END')

class Operation(TokenList):
    """Grouping of operations"""

class Values(TokenList):
    """Grouping of values"""

class Command(TokenList):
    """Grouping of CLI commands."""