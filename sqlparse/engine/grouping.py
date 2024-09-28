from sqlparse import sql
from sqlparse import tokens as T
from sqlparse.utils import recurse, imt
T_NUMERICAL = (T.Number, T.Number.Integer, T.Number.Float)
T_STRING = (T.String, T.String.Single, T.String.Symbol)
T_NAME = (T.Name, T.Name.Placeholder)

def _group_matching(tlist, cls):
    """Groups Tokens that have beginning and end."""
    pass

@recurse(sql.Identifier)
def group_order(tlist):
    """Group together Identifier and Asc/Desc token"""
    pass

def _group(tlist, cls, match, valid_prev=lambda t: True, valid_next=lambda t: True, post=None, extend=True, recurse=True):
    """Groups together tokens that are joined by a middle token. i.e. x < y"""
    pass