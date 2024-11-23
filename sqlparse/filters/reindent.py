from sqlparse import sql, tokens as T
from sqlparse.utils import offset, indent

class ReindentFilter:

    def __init__(self, width=2, char=' ', wrap_after=0, n='\n', comma_first=False, indent_after_first=False, indent_columns=False, compact=False):
        self.n = n
        self.width = width
        self.char = char
        self.indent = 1 if indent_after_first else 0
        self.offset = 0
        self.wrap_after = wrap_after
        self.comma_first = comma_first
        self.indent_columns = indent_columns
        self.compact = compact
        self._curr_stmt = None
        self._last_stmt = None
        self._last_func = None

    def _flatten_up_to_token(self, token):
        """Yields all tokens up to token but excluding current."""
        if token is None:
            return
        parent = token.parent
        if parent is None:
            return

        for t in parent.tokens:
            if t == token:
                break
            yield t

    def _get_offset(self, token):
        raw = str(token)
        line = raw.splitlines()[0]
        initial_whitespace = len(line) - len(line.lstrip())
        return initial_whitespace

    def _get_offset_at_depth(self, token, depth):
        offset = 0
        for t in self._flatten_up_to_token(token):
            if t.is_whitespace:
                continue
            offset += self._get_offset(t)
        return offset + (depth * self.width)

    def process(self, stream):
        """Process the stream."""
        for token in stream:
            if token.is_whitespace:
                token.value = self.n
                yield token
                continue

            if token.is_group:
                depth = len(list(self._flatten_up_to_token(token)))
                offset = self._get_offset_at_depth(token, depth)
                token.value = self.char * offset + str(token)
                yield token
                continue

            yield token