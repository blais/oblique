"""Parser for Beancount Query Language.
"""
__copyright__ = "Copyright (C) 2014-2016  Martin Blais"
__license__ = "GNU GPLv2"

import collections
import datetime
import enum
import io
import re

import dateutil.parser

import ply.lex
import ply.yacc


class ParseError(Exception):
    """A parser error."""


class Lexer:
    """PLY lexer for the Oblique DSL."""

    def __init__(self, **options):
        self.lexer = ply.lex.lex(module=self,
                                 reflags=re.MULTILINE, **options)

    # optimize=False,
    # debuglog=None,
    # debug=False)

    def tokenize(self, string):
        lx = self.lexer
        lx.input(string)
        while True:
            tok = lx.token()
            if not tok:
                break
            yield tok

    # List of valid tokens from the lexer.
    tokens = ["TYPE", "LAZYTYPE", "IGNORE", "REF", "ANONREF", "WORD"]
    # TODO: COMMENT?

    # reftype = "[a-z]{1,9}"
    # ident = "[a-z0-9_]+"

    # TODO: add ^

    def t_TYPE(self, t):
        r"^/type/([a-z0-9_]+)\b"
        return t

    def t_LAZYTYPE(self, t):
        r"^/lazytype/([a-z0-9_]+)\b"
        return t

    def t_IGNORE(self, t):
        r"^/ignore/([a-z0-9_]+)\b"
        return t

    def t_REF(self, t):
        r"([a-z]{1,9})/([a-z0-9_]+)\b"
        return t

    def t_ANONREF(self, t):
        r"([a-z]{1,9})/"
        return t

    def t_WORD(self, t):
        r"\w+"
        if t.value.strip():
            return t

    # Ignore whitespace.
    t_ignore = " \t\n"

    # Error handler.
    def t_error(self, t):
        raise ParseError("Unknown token: {}".format(t))


# class SelectParser(Lexer):
#     """PLY parser for the Beancount Query Language's SELECT statement.
#     """
#
#     start = 'select_statement'
#
#     def __init__(self, **options):
#         self.lexer = ply.lex.lex(module=self,
#                                  optimize=False,
#                                  debuglog=None,
#                                  debug=False)
#         self.parser = ply.yacc.yacc(module=self,
#                                     optimize=False,
#                                     write_tables=False,
#                                     debuglog=None,
#                                     debug=False,
#                                     **options)
#
#         # The default value to use for the close date.
#         self.default_close_date = None
#
#
#     def parse(self, line, debug=False, default_close_date=None):
#         try:
#             self.default_close_date = default_close_date
#             return self.parser.parse(line, lexer=self.lexer, debug=debug)
#         finally:
#             self.default_close_date = None
#
#     def handle_comma_separated_list(self, p):
#         """Handle a list of 0, 1 or more comma-separated values.
#         Args:
#           p: A grammar object.
#         """
#         if len(p) == 2:
#             return [] if p[1] is None else [p[1]]
#         return p[1] + [p[3]]
#
#     def p_account(self, p):
#         """
#         account : STRING
#         """
#         p[0] = p[1]
#
#     def p_select_statement(self, p):
#         """
#         select_statement : SELECT distinct target_spec from_subselect where \
#                            group_by order_by pivot_by limit
#         """
#         p[0] = Select(p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[2])
#
#     def p_distinct(self, p):
#         """
#         distinct : empty
#                  | DISTINCT
#         """
#         p[0] = True if p[1] == 'DISTINCT' else None
#
#     def p_target_spec(self, p):
#         """
#         target_spec : ASTERISK
#                     | target_list
#         """
#         p[0] = Wildcard() if p[1] == '*' else p[1]
#
#     def p_target_list(self, p):
#         """
#         target_list : target
#                     | target_list COMMA target
#         """
#         p[0] = self.handle_comma_separated_list(p)
#
#     def p_target(self, p):
#         """
#         target : expression AS ID
#                | expression
#         """
#         p[0] = Target(p[1], p[3] if len(p) == 4 else None)
#
#     def p_from(self, p):
#         """
#         from : empty
#              | FROM opt_expression opt_open opt_close opt_clear
#         """
#         if len(p) != 2:
#             if all(p[i] is None for i in range(2, 6)):
#                 raise ParseError("Empty FROM expression is not allowed")
#             p[0] = From(p[2], p[3], p[4], p[5])
#         else:
#             p[0] = None
#
#     def p_from_subselect(self, p):
#         """
#         from_subselect : from
#                        | FROM LPAREN select_statement RPAREN
#         """
#         if len(p) == 2:
#             p[0] = p[1]
#         else:
#             p[0] = p[3]
#
#     def p_opt_open(self, p):
#         """
#         opt_open : empty
#                  | OPEN ON DATE
#         """
#         p[0] = p[3] if len(p) == 4 else None
#
#     def p_opt_close(self, p):
#         """
#         opt_close : empty
#                   | CLOSE
#                   | CLOSE ON DATE
#         """
#         p[0] = p[3] if len(p) == 4 else (True
#                                          if (p[1] == 'CLOSE') else
#                                          self.default_close_date)
#
#     def p_opt_clear(self, p):
#         """
#         opt_clear : empty
#                   | CLEAR
#         """
#         p[0] = True if (p[1] == 'CLEAR') else None
#
#     def p_where(self, p):
#         """
#         where : empty
#               | WHERE expression
#         """
#         if len(p) == 3:
#             assert p[2], "Empty WHERE clause is not allowed"
#             p[0] = p[2]
#
#     def p_expr_index_list(self, p):
#         """
#         expr_index_list : expr_index
#                         | expr_index_list COMMA expr_index
#         """
#         p[0] = self.handle_comma_separated_list(p)
#
#     def p_expr_index(self, p):
#         """
#         expr_index : expression
#                    | INTEGER
#         """
#         p[0] = p[1]
#
#     def p_group_by(self, p):
#         """
#         group_by : empty
#                  | GROUP BY expr_index_list having
#         """
#         p[0] = GroupBy(p[3], p[4]) if len(p) != 2 else None
#
#     def p_having(self, p):
#         """
#         having : empty
#                | HAVING expression
#         """
#         p[0] = p[2] if len(p) == 3 else None
#
#     def p_order_by(self, p):
#         """
#         order_by : empty
#                  | ORDER BY order_expr_list
#         """
#         p[0] = p[3] if len(p) == 4 else None
#
#     def p_order_expr_list(self, p):
#         """
#         order_expr_list : order_expr
#                         | order_expr_list COMMA order_expr
#         """
#         p[0] = self.handle_comma_separated_list(p)
#
#     def p_order_expr(self, p):
#         """
#         order_expr : expr_index ordering
#         """
#         p[0] = OrderBy(p[1], Ordering[p[2] or 'ASC'])
#
#     def p_ordering(self, p):
#         """
#         ordering : empty
#                  | ASC
#                  | DESC
#         """
#         p[0] = p[1]
#
#     def p_pivot_by_empty(self, p):
#         """
#         pivot_by : empty
#         """
#         p[0] = None
#
#     def p_pivot_by(self, p):
#         """
#         pivot_by : PIVOT BY column_or_index COMMA column_or_index
#         """
#         p[0] = PivotBy([p[3], p[5]])
#
#     def p_limit(self, p):
#         """
#         limit : empty
#               | LIMIT INTEGER
#         """
#         p[0] = p[2] if len(p) == 3 else None
#
#
#     precedence = [
#         ('left', 'OR'),
#         ('left', 'AND'),
#         ('left', 'NOT'),
#         ('left', 'PLUS', 'MINUS'),
#         ('left', 'ASTERISK', 'SLASH'),
#         ('right', 'UMINUS'),
#         ('right', 'UPLUS'),
#         ('nonassoc', 'EQ', 'NE', 'GT', 'GTE', 'LT', 'LTE', 'TILDE', 'IN'),
#     ]
#
#     def p_expression_uminus(self, p):
#         "expression : MINUS expression %prec UMINUS"
#         # Optimization: if the argument is a numeric constant, rewrite
#         # the constant instead than emitting a unary operation.
#         p[0] = Constant(-p[2].value) if isinstance(p[2], Constant) and isinstance(p[2].value, numbers.Number) else Neg(p[2])
#
#     def p_expression_uplus(self, p):
#         "expression : PLUS expression %prec UPLUS"
#         p[0] = p[2]
#
#     def p_expression_is_null(self, p):
#         "expression : expression IS NULL"
#         p[0] = IsNull(p[1])
#
#     def p_expression_is_not_null(self, p):
#         "expression : expression IS NOT NULL"
#         p[0] = IsNotNull(p[1])
#
#     def p_expression_and(self, p):
#         "expression : expression AND expression"
#         p[0] = And(p[1], p[3])
#
#     def p_expression_or(self, p):
#         "expression : expression OR expression"
#         p[0] = Or(p[1], p[3])
#
#     def p_expression_not(self, p):
#         "expression : NOT expression"
#         p[0] = Not(p[2])
#
#     def p_expression_paren(self, p):
#         "expression : LPAREN expression RPAREN"
#         p[0] = p[2]
#
#     def p_expression_eq(self, p):
#         "expression : expression EQ expression"
#         p[0] = Equal(p[1], p[3])
#
#     def p_expression_ne(self, p):
#         "expression : expression NE expression"
#         p[0] = Not(Equal(p[1], p[3]))
#
#     def p_expression_gt(self, p):
#         "expression : expression GT expression"
#         p[0] = Greater(p[1], p[3])
#
#     def p_expression_gte(self, p):
#         "expression : expression GTE expression"
#         p[0] = GreaterEq(p[1], p[3])
#
#     def p_expression_lt(self, p):
#         "expression : expression LT expression"
#         p[0] = Less(p[1], p[3])
#
#     def p_expression_lte(self, p):
#         "expression : expression LTE expression"
#         p[0] = LessEq(p[1], p[3])
#
#     def p_expression_match(self, p):
#         "expression : expression TILDE expression"
#         p[0] = Match(p[1], p[3])
#
#     def p_expression_contains(self, p):
#         "expression : expression IN expression"
#         p[0] = Contains(p[1], p[3])
#
#     def p_expression_column(self, p):
#         "expression : column"
#         p[0] = p[1]
#
#     def p_expression_constant(self, p):
#         "expression : constant"
#         p[0] = p[1]
#
#     def p_expression_mul(self, p):
#         "expression : expression ASTERISK expression"
#         p[0] = Mul(p[1], p[3])
#
#     def p_expression_div(self, p):
#         "expression : expression SLASH expression"
#         p[0] = Div(p[1], p[3])
#
#     def p_expression_add(self, p):
#         "expression : expression PLUS expression"
#         p[0] = Add(p[1], p[3])
#
#     def p_expression_sub(self, p):
#         "expression : expression MINUS expression"
#         p[0] = Sub(p[1], p[3])
#
#     def p_expression_function(self, p):
#         "expression : ID LPAREN expression_list_opt RPAREN"
#         p[0] = Function(p[1], p[3])
#
#     def p_opt_expression(self, p):
#         """
#         opt_expression : empty
#                        | expression
#         """
#         p[0] = p[1]
#
#     def p_expression_list_opt(self, p):
#         """
#         expression_list_opt : empty
#                             | expression
#                             | expression_list COMMA expression
#         """
#         p[0] = self.handle_comma_separated_list(p)
#
#     def p_expression_list(self, p):
#         """
#         expression_list : expression
#                         | expression_list COMMA expression
#         """
#         p[0] = self.handle_comma_separated_list(p)
#
#     def p_column(self, p):
#         """
#         column : ID
#         """
#         p[0] = Column(p[1])
#
#     def p_column_or_index(self, p):
#         """
#         column_or_index : column
#                         | INTEGER
#         """
#         p[0] = p[1]
#
#     def p_literal(self, p):
#         """
#         literal : NULL
#                 | boolean
#                 | INTEGER
#                 | DECIMAL
#                 | STRING
#                 | DATE
#         """
#         p[0] = p[1]
#
#     def p_literal_list(self, p):
#         """
#         literals_list : literal COMMA
#         """
#         p[0] = [p[1]]
#
#     def p_literal_list_many(self, p):
#         """
#         literals_list : literals_list literal
#                       | literals_list literal COMMA
#         """
#         p[0] = p[1] + [p[2]]
#
#     def p_constant(self, p):
#         """
#         constant : literal
#                  | list
#         """
#         p[0] = Constant(p[1] if p[1] != 'NULL' else None)
#
#     def p_list(self, p):
#         """
#         list : LPAREN literals_list RPAREN
#         """
#         p[0] = p[2]
#
#     def p_boolean(self, p):
#         """
#         boolean : TRUE
#                 | FALSE
#         """
#         p[0] = (p[1] == 'TRUE')
#
#     def p_empty(self, _):
#         """
#         empty :
#         """
#
#     def p_error(self, token):
#         if token is None:
#             raise ParseError("ERROR: unterminated statement. Missing a semicolon?")
#
#         oss = io.StringIO()
#         oss.write("ERROR: Syntax error near '{}' (at {})\n".format(token.value,
#                                                                    token.lexpos))
#         oss.write("  ")
#         oss.write(self.lexer.lexdata)
#         oss.write("\n")
#         oss.write("  {}^".format(' ' * token.lexpos))
#         raise ParseError(oss.getvalue())
#
#
# class Parser(SelectParser):
#     """PLY parser for the Beancount Query Language's full command syntax.
#     """
#     start = 'top_statement'
#
#     def p_regular_statement(self, p):
#         "top_statement : statement delimiter"
#         p[0] = p[1]
#
#     def p_statement(self, p):
#         """
#         statement : select_statement
#                   | balances_statement
#                   | journal_statement
#                   | print_statement
#         """
#         p[0] = p[1]
#
#     def p_delimiter(self, p):
#         """
#         delimiter : SEMI
#                   | empty
#         """
#
#     def p_balances_statement(self, p):
#         """
#         balances_statement : BALANCES summary_func from where
#         """
#         p[0] = Balances(p[2], p[3], p[4])
#
#     def p_journal_statement(self, p):
#         """
#         journal_statement : JOURNAL summary_func from
#                           | JOURNAL account summary_func from
#         """
#         p[0] = Journal(None, p[2], p[3]) if len(p) == 4 else Journal(p[2], p[3], p[4])
#
#     def p_summary_func(self, p):
#         """
#         summary_func : empty
#                      | AT ID
#         """
#         p[0] = p[2] if len(p) == 3 else None
#
#     def p_print_statement(self, p):
#         """
#         print_statement : PRINT from
#         """
#         p[0] = Print(p[2])
#
#
# def get_expression_name(expr):
#     """Come up with a reasonable identifier for an expression.
#
#     Args:
#       expr: An expression node.
#     """
#     if isinstance(expr, Column):
#         return expr.name.lower()
#
#     if isinstance(expr, Function):
#         operands = ', '.join(get_expression_name(operand) for operand in expr.operands)
#         return f'{expr.fname.lower()}({operands})'
#
#     if isinstance(expr, Constant):
#         if isinstance(expr.value, str):
#             return repr(expr.value)
#         return str(expr.value)
#
#     if isinstance(expr, UnaryOp):
#         operand = get_expression_name(expr.operand)
#         return f'{type(expr).__name__.lower()}({operand})'
#
#     if isinstance(expr, BinaryOp):
#         operands = ', '.join(get_expression_name(operand) for operand in (expr.left, expr.right))
#         return f'{type(expr).__name__.lower()}({operands})'
#
#     raise NotImplementedError
#
