from sqlparse import sql, tokens as T

class StatementSplitter:
    """Filter that split stream at individual statements"""

    def __init__(self):
        self._reset()

    def _reset(self):
        """Set the filter attributes to its default values"""
        pass

    def _change_splitlevel(self, ttype, value):
        """Get the new split level (increase, decrease or remain equal)"""
        pass

    def process(self, stream):
        """Process the stream"""
        pass