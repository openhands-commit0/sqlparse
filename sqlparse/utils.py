import itertools
import re
from collections import deque
from contextlib import contextmanager
SPLIT_REGEX = re.compile('\n(\n (?:                     # Start of non-capturing group\n  (?:\\r\\n|\\r|\\n)      |  # Match any single newline, or\n  [^\\r\\n\'"]+          |  # Match any character series without quotes or\n                         # newlines, or\n  "(?:[^"\\\\]|\\\\.)*"   |  # Match double-quoted strings, or\n  \'(?:[^\'\\\\]|\\\\.)*\'      # Match single quoted strings\n )\n)\n', re.VERBOSE)
LINE_MATCH = re.compile('(\\r\\n|\\r|\\n)')

def split_unquoted_newlines(stmt):
    """Split a string on all unquoted newlines.

    Unlike str.splitlines(), this will ignore CR/LF/CR+LF if the requisite
    character is inside of a string."""
    matches = SPLIT_REGEX.finditer(stmt)
    matches = list(matches)
    if not matches:
        return [stmt]

    # If there are no matches, return the string as is
    if not matches:
        return [stmt]

    pieces = []
    last_end = 0
    for match in matches:
        start, end = match.span()
        if start > last_end:
            pieces.append(stmt[last_end:start])
        pieces.append(stmt[start:end])
        last_end = end

    if last_end < len(stmt):
        pieces.append(stmt[last_end:])

    return pieces

def remove_quotes(val):
    """Helper that removes surrounding quotes from strings."""
    if not val:
        return val

    if val[0] in ('"', "'") and val[-1] == val[0]:
        return val[1:-1]
    return val

def recurse(*cls):
    """Function decorator to help with recursion

    :param cls: Classes to not recurse over
    :return: function
    """
    def wrap(f):
        def wrapped(tlist):
            for token in tlist.tokens:
                if not isinstance(token, cls):
                    for t in token.flatten():
                        if isinstance(t, cls):
                            f(t)
            f(tlist)
        return wrapped
    return wrap

def imt(token, i=None, m=None, t=None):
    """Helper function to simplify comparisons Instance, Match and TokenType
    :param token:
    :param i: Class or Tuple/List of Classes
    :param m: Tuple of TokenType & Value. Can be list of Tuple for multiple
    :param t: TokenType or Tuple/List of TokenTypes
    :return:  bool
    """
    if i is not None and isinstance(i, (list, tuple)):
        for cls in i:
            if isinstance(token, cls):
                return True
        return False

    if i is not None:
        return isinstance(token, i)

    if m is not None and isinstance(m, (list, tuple)) and not isinstance(m[0], tuple):
        m = [m]

    if m is not None:
        for m_ttype, m_value in m:
            if token.match(m_ttype, m_value):
                return True
        return False

    if t is not None and isinstance(t, (list, tuple)):
        for ttype in t:
            if token.ttype is ttype:
                return True
        return False

    if t is not None:
        return token.ttype is t

    return True

def consume(iterator, n):
    """Advance the iterator n-steps ahead. If n is none, consume entirely."""
    deque(itertools.islice(iterator, n), maxlen=0) if n is not None else deque(iterator, maxlen=0)

def offset(token):
    """Returns the indentation offset of a token."""
    line = token.value.splitlines()[0]
    initial_whitespace = len(line) - len(line.lstrip())
    return initial_whitespace

def indent(stream, n=2, char=' '):
    """Returns a stream of tokens with each token indented by n characters."""
    for token in stream:
        token.value = '\n'.join(char * n + line if line else ''
                               for line in token.value.splitlines())
        yield token