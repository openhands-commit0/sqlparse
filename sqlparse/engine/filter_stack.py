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