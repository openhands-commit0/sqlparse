"""SQL Lexer"""
import re
from threading import Lock
from io import TextIOBase
from sqlparse import tokens, keywords
from sqlparse.utils import consume

class Lexer:
    """The Lexer supports configurable syntax.
    To add support for additional keywords, use the `add_keywords` method."""
    _default_instance = None
    _lock = Lock()

    @classmethod
    def get_default_instance(cls):
        """Returns the lexer instance used internally
        by the sqlparse core functions."""
        with cls._lock:
            if cls._default_instance is None:
                cls._default_instance = cls()
                cls._default_instance.default_initialization()
            return cls._default_instance

    def default_initialization(self):
        """Initialize the lexer with default dictionaries.
        Useful if you need to revert custom syntax settings."""
        self.clear()
        self.add_keywords(keywords.KEYWORDS)
        self.add_keywords(keywords.KEYWORDS_COMMON)
        self.add_keywords(keywords.KEYWORDS_ORACLE)
        self.add_keywords(keywords.KEYWORDS_PLPGSQL)
        self.add_keywords(keywords.KEYWORDS_HQL)
        self.add_keywords(keywords.KEYWORDS_MSACCESS)

    def clear(self):
        """Clear all syntax configurations.
        Useful if you want to load a reduced set of syntax configurations.
        After this call, regexps and keyword dictionaries need to be loaded
        to make the lexer functional again."""
        self._keywords = []
        self._SQL_REGEX = []

    def set_SQL_REGEX(self, SQL_REGEX):
        """Set the list of regex that will parse the SQL."""
        self._SQL_REGEX = SQL_REGEX

    def add_keywords(self, keywords):
        """Add keyword dictionaries. Keywords are looked up in the same order
        that dictionaries were added."""
        self._keywords.append(keywords)

    def is_keyword(self, value):
        """Checks for a keyword.

        If the given value is in one of the KEYWORDS_* dictionary
        it's considered a keyword. Otherwise, tokens.Name is returned.
        """
        val = value.upper()
        for kwdict in self._keywords:
            if val in kwdict:
                return kwdict[val]
        return tokens.Name

    def get_tokens(self, text, encoding=None):
        """
        Return an iterable of (tokentype, value) pairs generated from
        `text`. If `unfiltered` is set to `True`, the filtering mechanism
        is bypassed even if filters are defined.

        Also preprocess the text, i.e. expand tabs and strip it if
        wanted and applies registered filters.

        Split ``text`` into (tokentype, text) pairs.

        ``stack`` is the initial stack (default: ``['root']``)
        """
        if isinstance(text, TextIOBase):
            text = text.read()

        if encoding is not None:
            if isinstance(text, str):
                text = text.encode(encoding)
            text = text.decode(encoding)

        iterable = enumerate(text)
        for pos, char in iterable:
            # Handle whitespace
            if char.isspace():
                end = pos + 1
                while end < len(text) and text[end].isspace():
                    end += 1
                consume(iterable, end - pos - 1)
                yield tokens.Whitespace, text[pos:end]
                continue

            # Handle comments
            if char == '-' and text[pos + 1] == '-':
                end = text.find('\n', pos)
                if end == -1:
                    end = len(text)
                consume(iterable, end - pos - 1)
                yield tokens.Comment.Single, text[pos:end]
                continue

            # Handle string literals
            if char in ('"', "'"):
                end = pos + 1
                escaped = False
                while end < len(text):
                    if text[end] == char and not escaped:
                        break
                    if text[end] == '\\':
                        escaped = not escaped
                    else:
                        escaped = False
                    end += 1
                if end < len(text):
                    end += 1
                consume(iterable, end - pos - 1)
                yield tokens.String, text[pos:end]
                continue

            # Handle numbers
            if char.isdigit():
                end = pos + 1
                while end < len(text) and (text[end].isdigit() or text[end] == '.'):
                    end += 1
                consume(iterable, end - pos - 1)
                yield tokens.Number, text[pos:end]
                continue

            # Handle identifiers and keywords
            if char.isalpha() or char == '_' or char == '$':
                end = pos + 1
                while end < len(text) and (text[end].isalnum() or text[end] in '_$'):
                    end += 1
                word = text[pos:end]
                consume(iterable, end - pos - 1)
                if word.upper() in ('ASC', 'DESC'):
                    yield tokens.Keyword.Order, word
                else:
                    yield self.is_keyword(word), word
                continue

            # Handle operators and punctuation
            if char in '+-*/%<>=!|&~^':
                end = pos + 1
                while end < len(text) and text[end] in '+-*/%<>=!|&~^':
                    end += 1
                consume(iterable, end - pos - 1)
                yield tokens.Operator, text[pos:end]
                continue

            # Handle punctuation
            if char in '()[]{},;.':
                yield tokens.Punctuation, char
                continue

            # Handle unknown characters
            yield tokens.Error, char

def tokenize(sql, encoding=None):
    """Tokenize sql.

    Tokenize *sql* using the :class:`Lexer` and return a 2-tuple stream
    of ``(token type, value)`` items.
    """
    lexer = Lexer.get_default_instance()
    return lexer.get_tokens(sql, encoding)