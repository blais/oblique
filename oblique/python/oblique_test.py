import functools
import inspect
import unittest
import subprocess
import logging
import pprint
from typing import List, Any, Optional

from matplotlib import pyplot
import networkx as nx
import ply

import oblique
from oblique import Ref


class LexerTests(unittest.TestCase):

  def assert_tokens(self, string, expected_token_types, ws=False):
    oblique.Lexer.include_ws_token = ws
    lexer = oblique.Lexer()
    lexer.build(optimize=False, debug=False)
    lexer.lex.input(string)
    tokens = list(lexer.lex)
    token_types = [tok.type for tok in tokens]
    self.assertEqual(expected_token_types, token_types)

  def test_valid_commands(self):
    self.assert_tokens(
      "/type /lazytype /macro",
      ['TYPE', 'LAZYTYPE', 'MACRO']) # 'RENDER', 'IMPORT'
    self.assert_tokens(
      "/type q Calendar quarter",
      ['TYPE', 'WORD', 'WORD', 'WORD'])

  def test_invalid_commands(self):
    with self.assertRaises(oblique.LexerError):
      self.assert_tokens("/notreally", [])

  # TODO(blais): Parameterize all tests.
  def test_indent(self):
    self.assert_tokens("  Something",
                       ['INDENT', 'WORD'])
    self.assert_tokens("  Something and something else.",
                       ['INDENT', 'WORD', 'WORD', 'WORD', 'WORD'])
    self.assert_tokens("    Two indents",
                       ['INDENT', 'INDENT', 'WORD', 'WORD'])
    self.assert_tokens("     Five chars",
                       ['INDENT', 'INDENT', 'WORD', 'WORD'])
    self.assert_tokens("Indent  within   and more",
                       ['WORD', 'WORD', 'WORD', 'WORD'])

  def test_comment_token(self):
    self.assert_tokens("# Some comment",
                       ['COMMENT'])
    self.assert_tokens("  # Indented comment",
                       ['INDENT', 'COMMENT'])


def parse_and_assert(self, string: str, expected_list: Optional[Any] = None, **kw) -> nx.Graph:
  """Parse an indented string for testing."""
  graph = oblique.parse_string(string, dedent=True, **kw)
  graph_list = oblique.graph_to_list(graph)
  if expected_list is not None:
    self.assertListEqual(expected_list, graph_list)
  return graph


class TestGrammarBasics(unittest.TestCase):

  def test_empty_lines(self):
    parse_and_assert(self, """

    """, [])

    parse_and_assert(self, """

      Some item

    """, [('item', '0', 'Some item')])

    parse_and_assert(self, """
      Item #1.

      Item #2.
    """, [('item', '0', 'Item #1.'),
          ('item', '1', 'Item #2.')])

  def test_one_item(self):
    parse_and_assert(self, """
      This is a valid item.
    """, [('item', '0', 'This is a valid item.')])

  def test_multiple_item(self):
    parse_and_assert(self, """
      Valid item number 1.
      Valid item number 2.
      Valid item number 3.
    """, [('item', '0', 'Valid item number 1.'),
          ('item', '1', 'Valid item number 2.'),
          ('item', '2', 'Valid item number 3.')])

  def test_comment(self):
    parse_and_assert(self, """
      # Some comment.
    """, [])


class TestGrammar(unittest.TestCase):

  def test_type_definitions(self):
    parse_and_assert(self, """
      /type o Objective
      /type kr Key result
      /type cl Change list
    """, [('type', 'cl', 'Change list'),
          ('type', 'kr', 'Key result'),
          ('type', 'o', 'Objective')])

  def test_type_reserved(self):
    with self.assertRaises(oblique.ParserError):
      parse_and_assert(self, """
        /type type Second type
      """)

  def test_objdef_defined(self):
    parse_and_assert(self, """
      /type o Objective
      o/big-goal
    """, [('o', 'big-goal', ''),
          ('type', 'o', 'Objective')])

  def test_objdef_defined_withdesc(self):
    parse_and_assert(self, """
      /type o Objective
      o/big-goal Big goal
    """, [('o', 'big-goal', 'Big goal'),
          ('type', 'o', 'Objective')])

  def test_objdef_undefined(self):
    with self.assertRaises(oblique.ParserError):
      parse_and_assert(self, """
        o/big-goal
      """)

  def test_objref_defined(self):
    parse_and_assert(self, """
      /type bug Bugs
      bug/123456
      Ticket bug/123456
    """, [('bug', '123456', ''),
          ('item', '0', 'Ticket bug/123456'),
          ('type', 'bug', 'Bugs')])

  def test_objref_undefined(self):
    with self.assertRaises(oblique.ParserError):
      parse_and_assert(self, """
        Ticket bug/123456
      """)

  def test_inheritance(self):
    g = parse_and_assert(self, """
      /type g Gold
      /type s Silver
      g/1
      g/2 g/1
        s/1
    """, [('g', '1', ''),
          ('g', '2', 'g/1'),
          ('s', '1', ''),
          ('type', 'g', 'Gold'),
          ('type', 's', 'Silver')])
    self.assertSetEqual({'g/1', 'g/2'}, set(map(str, g[Ref('s', '1')].keys())))


  multilevel_input = """
      /type g Gold
      g/1
        g/2
          g/3
            g/4
          g/5
            g/6
        g/7
  """

  multilevel_graph_list = [('g', '1', ''),
                           ('g', '2', ''),
                           ('g', '3', ''),
                           ('g', '4', ''),
                           ('g', '5', ''),
                           ('g', '6', ''),
                           ('g', '7', ''),
                           ('type', 'g', 'Gold')]

  def test_inheritance_multilevel(self):
    g = parse_and_assert(self,
                         self.multilevel_input,
                         self.multilevel_graph_list)
    expected = {
      'g/1': set(),
      'g/2': {'g/1'},
      'g/3': {'g/2'},
      'g/4': {'g/3'},
      'g/5': {'g/2'},
      'g/6': {'g/5'},
      'g/7': {'g/1'},
    }
    for ref in [Ref('g', str(i)) for i in range(1, 8)]:
      self.assertSetEqual(expected[str(ref)], set(map(str, g[ref].keys())))

  def test_inheritance_multilevel_cumulative(self):
    g = parse_and_assert(self,
                         self.multilevel_input,
                         self.multilevel_graph_list, cumulative_context=True)
    expected = {
      'g/1': set(),
      'g/2': {'g/1'},
      'g/3': {'g/1', 'g/2'},
      'g/4': {'g/1', 'g/2', 'g/3'},
      'g/5': {'g/1', 'g/2'},
      'g/6': {'g/1', 'g/2', 'g/5'},
      'g/7': {'g/1'},
    }
    for ref in [Ref('g', str(i)) for i in range(1, 8)]:
      self.assertSetEqual(expected[str(ref)], set(map(str, g[ref].keys())))


  def test_inheritance_indirect_refs(self):
    g = parse_and_assert(self, """
      /type g Gold
      /type u User
      u/joe
      g/1 u/joe
        g/2
    """, [('g', '1', 'u/joe'),
          ('g', '2', ''),
          ('type', 'g', 'Gold'),
          ('type', 'u', 'User'),
          ('u', 'joe', '')])
    expected = {
      'g/1': {'u/joe'},
      'g/2': {'g/1', 'u/joe'},
    }
    for ref in [Ref('g', str(i)) for i in range(1, 3)]:
      self.assertSetEqual(expected[str(ref)], set(map(str, g[ref].keys())))

  def test_inheritance_with_ws(self):
    g = parse_and_assert(self, """
      /type g Gold
      g/1
        g/2

        g/3
    """, [('g', '1', ''),
          ('g', '2', ''),
          ('g', '3', ''),
          ('type', 'g', 'Gold')])
    expected = {
      'g/1': set(),
      'g/2': {'g/1'},
      'g/3': {'g/1'},
    }
    for ref in [Ref('g', str(i)) for i in range(1, 4)]:
      self.assertSetEqual(expected[str(ref)], set(map(str, g[ref].keys())))

  def test_lazy_types(self):
    parse_and_assert(self, """
      /lazytype cl Commit
      Worked on cl/134afa96454d
    """, [('cl', '134afa96454d', ''),
          ('item', '0', 'Worked on cl/134afa96454d'),
          ('type', 'cl', 'Commit')])

  def test_lazy_types(self):
    parse_and_assert(self, """
      /lazytype cl Commit
      Worked on cl/134afa96454d
    """, [('cl', '134afa96454d', ''),
          ('item', '0', 'Worked on cl/134afa96454d'),
          ('type', 'cl', 'Commit')])

  def test_macro_priority(self):
    parse_and_assert(self, r"""
      /type p Priority
      p/1 High priority
      p/2 Medium priority
      /macro P([0-4]) p/\1
      Attend to the frobnicator P1 after cleaning it (P2)
    """, [('item', '0', 'Attend to the frobnicator P1 after cleaning it (P2)'),
          ('p', '1', 'High priority'),
          ('p', '2', 'Medium priority'),
          ('type', 'p', 'Priority')])

  def test_macro_user(self):
    parse_and_assert(self, r"""
      /lazytype u User
      /macro ([a-z]+)@ u/\1
      Help client deliver on project blais@
    """, [('item', '0', 'Help client deliver on project blais@'),
          ('type', 'u', 'User'),
          ('u', 'blais', '')])

    with self.assertRaises(oblique.ParserError):
      parse_and_assert(self, r"""
        /macro ([a-z]+)@ u/\1
        Help client deliver on project blais@
      """)



if __name__ == '__main__':
  unittest.main()
