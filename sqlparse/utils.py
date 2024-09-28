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
    pass

def remove_quotes(val):
    """Helper that removes surrounding quotes from strings."""
    pass

def recurse(*cls):
    """Function decorator to help with recursion

    :param cls: Classes to not recurse over
    :return: function
    """
    pass

def imt(token, i=None, m=None, t=None):
    """Helper function to simplify comparisons Instance, Match and TokenType
    :param token:
    :param i: Class or Tuple/List of Classes
    :param m: Tuple of TokenType & Value. Can be list of Tuple for multiple
    :param t: TokenType or Tuple/List of TokenTypes
    :return:  bool
    """
    pass

def consume(iterator, n):
    """Advance the iterator n-steps ahead. If n is none, consume entirely."""
    pass