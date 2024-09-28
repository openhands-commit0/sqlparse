"""Tokens"""

class _TokenType(tuple):
    parent = None

    def __contains__(self, item):
        return item is not None and (self is item or item[:len(self)] == self)

    def __getattr__(self, name):
        if name.startswith('__'):
            return super().__getattr__(self, name)
        new = _TokenType(self + (name,))
        setattr(self, name, new)
        new.parent = self
        return new

    def __repr__(self):
        return 'Token' + ('.' if self else '') + '.'.join(self)
Token = _TokenType()
Text = Token.Text
Whitespace = Text.Whitespace
Newline = Whitespace.Newline
Error = Token.Error
Other = Token.Other
Keyword = Token.Keyword
Name = Token.Name
Literal = Token.Literal
String = Literal.String
Number = Literal.Number
Punctuation = Token.Punctuation
Operator = Token.Operator
Comparison = Operator.Comparison
Wildcard = Token.Wildcard
Comment = Token.Comment
Assignment = Token.Assignment
Generic = Token.Generic
Command = Generic.Command
Token.Token = Token
Token.String = String
Token.Number = Number
DML = Keyword.DML
DDL = Keyword.DDL
CTE = Keyword.CTE