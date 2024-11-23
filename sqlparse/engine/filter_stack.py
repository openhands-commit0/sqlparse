"""filter"""
from sqlparse import lexer
from sqlparse.engine import grouping
from sqlparse.engine.statement_splitter import StatementSplitter
from sqlparse.filters import StripTrailingSemicolonFilter

class FilterStack:

    def __init__(self, strip_semicolon=False):
        self.preprocess = []
        self.stmtprocess = []
        self.postprocess = []
        self._grouping = False
        if strip_semicolon:
            self.stmtprocess.append(StripTrailingSemicolonFilter())

    def enable_grouping(self):
        self._grouping = True

    def run(self, sql, encoding=None):
        stream = lexer.tokenize(sql, encoding)
        # Process token stream
        for filter_ in self.preprocess:
            stream = filter_.process(stream)

        stream = StatementSplitter().process(stream)

        # Group and ungroup tokens
        if self._grouping:
            stream = grouping.group(stream)

        # Process statements
        ret = []
        for stmt in stream:
            if stmt.is_whitespace:
                continue
            for filter_ in self.stmtprocess:
                filter_.process(stmt)
            ret.append(stmt)

        # Process again after grouping
        for filter_ in self.postprocess:
            ret = filter_.process(ret)

        return ret