"""SQL formatter"""
from sqlparse import filters
from sqlparse.exceptions import SQLParseError

def validate_options(options):
    """Validates options."""
    if options is None:
        options = {}

    # Validate reindent option
    if 'reindent' in options and not isinstance(options.get('reindent'), bool):
        raise SQLParseError('Invalid value for reindent')

    # Validate indent_width option
    if 'indent_width' in options:
        indent_width = options.get('indent_width')
        if not isinstance(indent_width, int) or indent_width < 0:
            raise SQLParseError('indent_width must be a positive integer')

    # Validate keyword_case option
    if 'keyword_case' in options:
        keyword_case = options.get('keyword_case')
        if keyword_case not in ('upper', 'lower', 'capitalize', None):
            raise SQLParseError('Invalid value for keyword_case')

    return options

def build_filter_stack(stack, options):
    """Setup and return a filter stack.

    Args:
      stack: :class:`~sqlparse.filters.FilterStack` instance
      options: Dictionary with options validated by validate_options.
    """
    # Process options
    strip_comments = options.get('strip_comments', False)
    strip_whitespace = options.get('strip_whitespace', False)
    reindent = options.get('reindent', False)
    indent_width = options.get('indent_width', 2)
    keyword_case = options.get('keyword_case', None)
    wrap_after = options.get('wrap_after', 0)
    comma_first = options.get('comma_first', False)
    right_margin = options.get('right_margin', None)
    indent_after_first = options.get('indent_after_first', False)
    indent_columns = options.get('indent_columns', False)
    compact = options.get('compact', False)

    # Enable grouping
    stack.enable_grouping()

    # Add filters
    if strip_comments:
        stack.preprocess.append(filters.StripCommentsFilter())

    if strip_whitespace:
        stack.preprocess.append(filters.StripWhitespaceFilter())

    if reindent:
        stack.preprocess.append(filters.ReindentFilter(
            width=indent_width,
            wrap_after=wrap_after,
            comma_first=comma_first,
            indent_after_first=indent_after_first,
            indent_columns=indent_columns,
            compact=compact))

    if right_margin and not reindent:
        stack.preprocess.append(filters.RightMarginFilter(right_margin))

    if keyword_case:
        stack.preprocess.append(filters.KeywordCaseFilter(keyword_case))

    return stack