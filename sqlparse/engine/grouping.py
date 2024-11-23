from sqlparse import sql
from sqlparse import tokens as T
from sqlparse.utils import recurse, imt
from sqlparse.sql import (
    Parenthesis, SquareBrackets, Case, If, For, Begin,
    TypedLiteral, Identifier, IdentifierList, Operation,
    Values, Command, Comparison, Assignment, Where, Having, Over
)
T_NUMERICAL = (T.Number, T.Number.Integer, T.Number.Float)
T_STRING = (T.String, T.String.Single, T.String.Symbol)
T_NAME = (T.Name, T.Name.Placeholder)

def _group_matching(tlist, cls):
    """Groups Tokens that have beginning and end."""
    idx = 0
    while idx < len(tlist.tokens):
        token = tlist.tokens[idx]
        if token.is_whitespace:
            idx += 1
            continue

        if token.match(*cls.M_OPEN):
            end_idx = tlist.token_matching(token, idx)
            if end_idx is None:
                idx += 1
                continue

            group = tlist.group_tokens(cls, tlist.tokens[idx:end_idx + 1])
            idx = tlist.token_index(group) + 1
        else:
            idx += 1

@recurse(sql.Identifier)
def group_order(tlist):
    """Group together Identifier and Asc/Desc token"""
    idx = 0
    while idx < len(tlist.tokens) - 1:
        token = tlist.tokens[idx]
        next_token = tlist.tokens[idx + 1]
        
        if token.is_whitespace or token.is_group:
            idx += 1
            continue
            
        if next_token.is_whitespace:
            idx += 1
            continue
            
        if token.ttype in (T.Name, T.String.Symbol, T.Number) and \
           next_token.match(T.Keyword, ('ASC', 'DESC'), True):
            grp = tlist.group_tokens(sql.Identifier, tlist.tokens[idx:idx + 2])
            idx = tlist.token_index(grp) + 1
        else:
            idx += 1

def group(stream):
    """Group together tokens that form SQL statements."""
    for cls in (Parenthesis, SquareBrackets, Case, If, For, Begin,
               TypedLiteral, Identifier, IdentifierList, Operation,
               Values, Command):
        _group_matching(stream, cls)

    _group(stream, Comparison, (T.Operator.Comparison,))
    _group(stream, Assignment, (T.Assignment,))
    _group(stream, Where, (T.Keyword, 'WHERE'))
    _group(stream, Having, (T.Keyword, 'HAVING'))
    _group(stream, Over, (T.Keyword, 'OVER'))

    group_order(stream)
    return stream

def _group(tlist, cls, match, valid_prev=lambda t: True, valid_next=lambda t: True, post=None, extend=True, recurse=True):
    """Groups together tokens that are joined by a middle token. i.e. x < y"""
    idx = 1
    while idx < len(tlist.tokens) - 1:
        token = tlist.tokens[idx]
        if token.is_whitespace:
            idx += 1
            continue

        before = tlist.tokens[idx - 1]
        after = tlist.tokens[idx + 1]

        if token.match(*match) and valid_prev(before) and valid_next(after):
            if extend:
                # Look ahead to handle x > y > z
                end = idx + 1
                while end < len(tlist.tokens) - 1:
                    next_token = tlist.tokens[end + 1]
                    if next_token.is_whitespace:
                        end += 1
                        continue
                    if next_token.match(*match) and valid_next(tlist.tokens[end + 2]):
                        end += 2
                    else:
                        break
                tokens = tlist.tokens[idx - 1:end + 1]
            else:
                tokens = tlist.tokens[idx - 1:idx + 2]

            group = tlist.group_tokens(cls, tokens)
            if post:
                post(group)

            if recurse:
                _group(group, cls, match, valid_prev, valid_next, post, extend)

            idx = tlist.token_index(group) + 1
        else:
            idx += 1