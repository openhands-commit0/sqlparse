from sqlparse import sql, tokens as T
from sqlparse.utils import offset, indent

class AlignedIndentFilter:
    join_words = '((LEFT\\s+|RIGHT\\s+|FULL\\s+)?(INNER\\s+|OUTER\\s+|STRAIGHT\\s+)?|(CROSS\\s+|NATURAL\\s+)?)?JOIN\\b'
    by_words = '(GROUP|ORDER)\\s+BY\\b'
    split_words = ('FROM', join_words, 'ON', by_words, 'WHERE', 'AND', 'OR', 'HAVING', 'LIMIT', 'UNION', 'VALUES', 'SET', 'BETWEEN', 'EXCEPT')

    def __init__(self, char=' ', n='\n'):
        self.n = n
        self.offset = 0
        self.indent = 0
        self.char = char
        self._max_kwd_len = len('select')