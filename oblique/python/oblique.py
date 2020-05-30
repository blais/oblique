#!/usr/bin/env python3
"""Oblique self-describing database language.

Oblique is a simple computer language that allows you to define types and data
entries in the same file. It was originally designed to make it possible to
input todo lists, snippets, and planning tasks all in one place, in a format
that is remarkably terse yet typed and general at the same time.
"""

import argparse
import collections
import logging
import itertools
import textwrap
import re
import pprint
import subprocess
from typing import NamedTuple, List, Union, Tuple

import ply.lex
import ply.yacc
import networkx as nx


# Regexp for valid type names.
TYPE_RE = re.compile(r"[a-z]+")

# Regexp for identifiers.
IDENT_RE = re.compile(r"[a-z0-9A-Z-]+")

# Regexp for object references.
OBJREF_RE = re.compile(f"{TYPE_RE.pattern}/{IDENT_RE.pattern}")

# Type name for types.
TYPE = "type"

# Type name and description for items.
ITEM = "item"
ITEM_DESCRIPTION = "Item"



class LexerError(Exception):
  "Syntax error."


class ParserError(Exception):
  "All program errors."


class Ref(NamedTuple("Ref", [('otype', str),
                             ('ident', str)])):

  def __str__(self):
    return "{}/{}".format(self.otype, self.ident)

  def __repr__(self):
    return "Ref({}/{})".format(self.otype, self.ident)


Macro = NamedTuple("Macro", [('regexp', re.Pattern),
                             ('replacement', str)])


class Lexer:
  """Token generator."""

  # Flag that controls where we discard or return whitespace tokens.
  include_ws_token = False

  reserved = {
     'type': 'TYPE',
     'lazytype': 'LAZYTYPE',
     'macro': 'MACRO',
     # 'render': 'RENDER',
     # 'import': 'IMPORT',
  }

  # Note: Names of types are validate in the parser itself. This keeps the lexer
  # substantially simpler, since it is impossible to distinguish between
  # identifiers used in context text and within commands without introducing
  # significant state.
  tokens = (['INDENT', 'COMMENT', 'EOL', 'OBJREF', 'WORD'] +
            list(reserved.values()))

  # The INITIAL state eats up the indents at the beginning of each line and any
  # other token will cause a rewind. The 'decl' state is used to parse all other
  # tokens.
  states = (
    ('decl', 'exclusive'),
  )

  start = 'linebegin'

  def build(self, **kwargs):
    "Build a lexer from this class."
    self.lex = ply.lex.lex(module=self, **kwargs)
    return self.lex

  def rewind(self, token):
    "Rewind the lexer to reprocess this token."
    token.lexer.skip(-len(token.value))

  def t_INDENT(self, token):
    r"\ \ "
    return token

  def t_COMMENT(self, token):
    r"\#.*"
    token.lexer.begin('INITIAL')
    token.value = token.value[1:].lstrip()
    return token

  def t_WORD(self, token):
    r"[^\r\n]"
    # This is a catch-all pattern to switch to decl state and retry the token.
    self.rewind(token)
    token.lexer.begin('decl')

  def t_EOL(self, token):
    r"\r?\n"
    return token

  def t_error(self, token):
      raise LexerError(f"Unknown token: {token}")

  #------------------------------------------------
  # Tokens valid in declarations, past the indents

  def t_decl_COMMAND(self, token):
    r'/[a-z]+\b'
    token.type = self.reserved.get(token.value[1:], None)
    if token.type is None:
      raise LexerError(f"Invalid command token: {token.value}")
    return token

  def t_decl_OBJREF(self, token):
    #r"[a-z]+/[a-z0-9A-Z-]+"
    token.value = Ref(*token.value.split("/"))
    return token
  t_decl_OBJREF.__doc__ = OBJREF_RE.pattern

  def t_decl_WORD(self, token):
    r"[^ \t\n]+"
    return token

  def t_decl_WS(self, token):
    r"[ \t]+"
    if self.include_ws_token:
      return token

  def t_decl_EOL(self, token):
    r"\r?\n"
    token.lexer.begin('INITIAL')
    return token

  t_decl_error = t_error


def create_default_graph() -> nx.DiGraph:
  """Create a default empty graph, insert the root type/type object, and the
  default type/item type."""
  graph = nx.DiGraph()
  typeref = Ref(TYPE, TYPE)
  graph.add_node(typeref, content="Type")
  itemref = Ref(TYPE, ITEM)
  define(graph, itemref, [ITEM_DESCRIPTION], [])
  return graph


def define(graph: nx.DiGraph, objref: Ref,
           words: List[str], refs: List[Ref], **attribs):
  "Define a new object."
  assert isinstance(objref, Ref)
  assert all(isinstance(xref, Ref) for xref in refs)
  content = " ".join(words)

  # Add a new node for the object.
  if objref in graph.nodes:
    raise ParserError(f"Object already defined: {objref}")
  graph.add_node(objref, content=content, **attribs)

  # Add a reference from the object's type object to the object.
  typeref = Ref(TYPE, objref.otype)
  typenode = graph.nodes.get(typeref, None)
  if typenode is None:
    raise ParserError(f"Undefined type: {typeref}")
  graph.add_edge(typeref, objref)
  # TODO: Deal with lazy types.

  # Add references to other objects.
  for outref in refs:
    assert isinstance(outref, Ref)
    typeref = Ref(TYPE, outref.otype)
    typenode = graph.nodes.get(typeref, None)
    if typenode is None:
      raise ParserError(f"Undefined type for ref: {typeref}")
    if typenode['lazy']:
      # Automatically create the node.
      graph.add_node(outref, content='')
    elif outref not in graph.nodes:
      raise ParserError(f"Undefined reference: {outref}")
    graph.add_edge(objref, outref)

  return objref, refs


class Grammar:
  """Grammar parser."""

  start = 'declarations'

  tokens = Lexer.tokens

  def build(self, **kwargs):
    self.cumulative_context = bool(kwargs.pop("cumulative_context", False))
    self.yacc = ply.yacc.yacc(module=self, **kwargs)
    self.ident_counter = itertools.count()
    self.graph = create_default_graph()
    # A cumulative stack of ref lists.
    self.context = [list()]
    self.macros = []
    return self.yacc

  def p_declarations(self, p):
    """
    declarations : declaration
                 | declarations indented_declaration
    """
    p[0] = self.graph

  def p_indented_declaration(self, p):
    """
    indented_declaration : indentlist declaration
    """
    level, decl = p[1:3]
    if isinstance(decl, tuple):
      (ref, refs) = decl

      # Add contextual refs to the just defined ref.
      assert isinstance(level, int)
      while len(self.context) > level:
        self.context.pop()

      context = self.context[-1] if self.context else []

      assert isinstance(ref, Ref)
      for ctxref in context:
        assert isinstance(ctxref, Ref)
        self.graph.add_edge(ref, ctxref)

      if len(self.context) == level:
        new_context = list(context) if self.cumulative_context else []
        new_context.append(ref)
        new_context.extend(refs)
        self.context.append(new_context)

    p[0] = None

  def p_declaration(self, p):
    """
    declaration : emptyline
                | command_type
                | command_lazytype
                | command_macro
                | definition
    """
    p[0] = p[1]

  def p_indentlist(self, p):
    """
    indentlist :
               | indentlist INDENT
    """
    p[0] = 0 if len(p) == 1 else (p[1] + 1)

  def p_emptyline(self, p):
    """
    emptyline : EOL
              | COMMENT EOL
    """

  def p_macroable_term(self, p):
    "macroable_term : WORD"
    word = p[1]
    ref = None
    # Attempt macro replacement and stop after first match.
    for macro in self.macros:
      match = macro.regexp.match(word)
      if match:
        refstr = match.expand(macro.replacement)
        if not OBJREF_RE.match(refstr):
          raise ParserError("Macro replacement did not result in a ref.")
        ref = Ref(*refstr.split("/"))
        break
    p[0] = (word, ref)

  def p_term(self, p):
    """
    term : OBJREF
         | macroable_term
    """
    term = p[1]
    if isinstance(term, Ref):
      p[0] = (str(term), term)
    else:
      p[0] = term  # Word, Ref

  def p_termlist(self, p):
    """
    termlist :
             | termlist term
    """
    if len(p) == 1:
      # wordlist, reflist
      p[0] = ([], [])
    else:
      wordlist, reflist = p[1]
      word, ref = p[2]
      wordlist = list(wordlist)
      wordlist.append(word)
      if ref:
        reflist = list(reflist)
        reflist.append(ref)
      p[0] = (wordlist, reflist)

  def p_object_definition(self, p):
    "definition : OBJREF termlist EOL"
    ref = p[1]
    words, refs = p[2]
    p[0] = define(self.graph, ref, words, refs)

  def p_item_definition(self, p):
    "definition : termlist EOL"
    ident = str(next(self.ident_counter))
    ref = Ref(ITEM, ident)
    words, refs = p[1]
    p[0] = define(self.graph, ref, words, refs)

  def p_otype(self, p):
    "otype : WORD"
    ident = p[1]
    if not TYPE_RE.match(ident):
      raise ParserError(f"Invalid syntax for types: {ident}")
    p[0] = ident

  def p_regexp(self, p):
    "regexp : WORD"
    p[0] = re.compile(p[1])

  def p_replacement(self, p):
    "replacement : WORD"
    p[0] = p[1]  # No validation.

  def p_command_type(self, p):
    "command_type : TYPE otype termlist EOL"
    ref = Ref(TYPE, p[2])
    words, refs = p[3]
    p[0] = define(self.graph, ref, words, refs, lazy=False)

  def p_command_lazytype(self, p):
    "command_lazytype : LAZYTYPE otype termlist EOL"
    ref = Ref(TYPE, p[2])
    words, refs = p[3]
    p[0] = define(self.graph, ref, words, refs, lazy=True)

  def p_command_macro(self, p):
    "command_macro : MACRO regexp replacement EOL"
    regexp = p[2]
    # Macros must match full words. Ensure this.
    if not regexp.pattern.endswith(r"$"):
      regexp = re.compile(regexp.pattern + "$")
    self.macros.append(Macro(regexp, p[3]))

  def p_error(self, p):
    raise ParserError(f"Syntax error: {p}")


def parse_string(string: str,
                 filename: str = "<string>",
                 firstline: str = 1,
                 dedent: bool = False,
                 **kwargs) -> nx.DiGraph:
  """Parse and compile a string into a graph database.

  TODO: Convert this into a grammar.
  """
  #pprint.pprint(string)
  if dedent:
    string = textwrap.dedent(string)
  #pprint.pprint(string)

  lexer = Lexer()
  lexer.build(optimize=False, debug=False)

  grammar = Grammar()
  parser = grammar.build(optimize=False, write_tables=False, debug=False, **kwargs)
  graph = parser.parse(string, lexer=lexer.lex, debug=False)

  return graph


def parse(filename: str):
  """Parse and compile a top-level file into a graph database."""
  with open(filename) as infile:
    return parse_string(infile.read(), filename=filename)


def tokenize_and_print(filename: str):
  lexer = Lexer()
  lexer.build(optimize=False, debug=True)
  with open(filename) as infile:
    contents = infile.read()
  lexer.lex.input(contents)
  for token in lexer.lex:
    print(token)


def render_test_graph(ingraph: nx.DiGraph, render_types: bool = False):
  """Render the parsed graph and display it. For debugging."""
  graph = ingraph.copy()
  remove = []
  for ref, node in graph.nodes.items():
    if not render_types and ref.otype in TYPE:
      remove.append(ref)
    content = node.get("content", None)
    if content and len(content) > 32:
      content = f"{content[:32]}..."
    node["label"] = "{} {}".format(ref, content)
  graph.remove_nodes_from(remove)

  agraph = nx.nx_agraph.to_agraph(graph)
  agraph.layout('dot')
  outfile = "/tmp/out.pdf"
  agraph.draw(outfile)
  subprocess.check_call(["evince", outfile], shell=False)


def graph_to_list(graph: nx.DiGraph) -> List[str]:
  """Convert a graph to a sorted list we can assert against."""
  outlist = []
  for ref, node in graph.nodes.items():
    if ref.otype == TYPE and ref.ident in (TYPE, ITEM):
      continue
    outlist.append((ref.otype, ref.ident, node['content']))
  outlist.sort()
  return outlist


def main():
  logging.basicConfig(level=logging.INFO, format='%(levelname)-8s: %(message)s')
  parser = argparse.ArgumentParser(description=__doc__.strip())
  parser.add_argument('filenames', nargs='+',
                      help='Oblique filenames to process')
  parser.add_argument('--tokenize', '-v', action='store_true',
                      help='Tokenize the input to debug it')
  parser.add_argument('--draw', '-g', action='store_true',
                      help='Render the graph')

  args = parser.parse_args()

  for filename in args.filenames:
    if args.tokenize:
      tokenize_and_print(filename)
    graph = parse(filename)
    if args.draw:
      render_test_graph(graph)
    else:
      pprint.pprint(graph_to_list(graph), width=200)


if __name__ == '__main__':
  main()
