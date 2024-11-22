"""Module that contains the command line app.

Why does this file exist, and why not put this in __main__?
  You might be tempted to import things from __main__ later, but that will
  cause problems: the code will get executed twice:
  - When you run `python -m sqlparse` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``sqlparse.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``sqlparse.__main__`` in ``sys.modules``.
  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import argparse
import sys
from io import TextIOWrapper
import sqlparse
from sqlparse.exceptions import SQLParseError

def _error(msg):
    """Print msg and optionally exit with return code exit_."""
    sys.stderr.write(msg + '\n')
    sys.exit(1)

def create_parser():
    """Create and return command line parser."""
    parser = argparse.ArgumentParser(
        description='Format SQL files.',
        usage='%(prog)s  [OPTIONS] FILE, ...',
        add_help=True)
    parser.add_argument('files', nargs='*', help='Files to be processed')
    parser.add_argument('-o', '--outfile', help='Write output to FILE')
    parser.add_argument('-r', '--reindent', action='store_true',
                      help='Reindent statements')
    parser.add_argument('-l', '--language', choices=['English'],
                      help='Programming language (default: English)')
    parser.add_argument('--encoding', default='utf-8',
                      help='Specify the input encoding (default: utf-8)')
    parser.add_argument('--indent-width', type=int, default=2,
                      help='Number of spaces for indentation (default: 2)')
    return parser

def main(args=None):
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(args)

    if not args.files:
        parser.print_help()
        sys.exit(1)

    encoding = args.encoding
    if encoding == 'utf-8':
        # Python 3 reads files as utf-8 by default
        encoding = None

    for file_ in args.files:
        try:
            with open(file_, 'r', encoding=encoding) as f:
                data = f.read()
        except OSError as e:
            _error('Failed to read {}: {}'.format(file_, e))
            continue

        if args.reindent:
            data = sqlparse.format(data, reindent=True,
                                 indent_width=args.indent_width)

        if args.outfile:
            try:
                with open(args.outfile, 'w', encoding=encoding) as f:
                    f.write(data)
            except OSError as e:
                _error('Failed to write to {}: {}'.format(args.outfile, e))
        else:
            sys.stdout.write(data)

    return 0