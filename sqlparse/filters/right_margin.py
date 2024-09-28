import re
from sqlparse import sql, tokens as T

class RightMarginFilter:
    keep_together = ()

    def __init__(self, width=79):
        self.width = width
        self.line = ''