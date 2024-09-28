from sqlparse import tokens as T

class _CaseFilter:
    ttype = None

    def __init__(self, case=None):
        case = case or 'upper'
        self.convert = getattr(str, case)

class KeywordCaseFilter(_CaseFilter):
    ttype = T.Keyword

class IdentifierCaseFilter(_CaseFilter):
    ttype = (T.Name, T.String.Symbol)

class TruncateStringFilter:

    def __init__(self, width, char):
        self.width = width
        self.char = char