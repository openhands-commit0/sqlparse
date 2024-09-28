"""SQL formatter"""
from sqlparse import filters
from sqlparse.exceptions import SQLParseError

def validate_options(options):
    """Validates options."""
    pass

def build_filter_stack(stack, options):
    """Setup and return a filter stack.

    Args:
      stack: :class:`~sqlparse.filters.FilterStack` instance
      options: Dictionary with options validated by validate_options.
    """
    pass