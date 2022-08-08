__copyright__ = "Copyright (C) 2014-2016  Martin Blais"
__license__ = "GNU GPLv2"

from oblique import parser

from decimal import Decimal as D
import datetime
import unittest
import textwrap


class TestLexer(unittest.TestCase):

    # def setUp(self):
    #     self.parser = qp.Parser()

    def tokenize(self, string, **opts):
        lx = parser.Lexer(*opts)
        return [(t.type, t.value) for t in lx.tokenize(textwrap.dedent(string))]

    def test_tokens(self):
        lx = parser.Lexer()#debug=True)
        tokens = self.tokenize(
            """
          /type/andrew
          /lazytype/sam
          /ignore/george
          kr/action
          kr/
          o/obj Objective
          o/ Objective
          Multiple words
        """
        )
        self.assertEqual(
            [
                ("TYPE", "/type/andrew"),
                ("LAZYTYPE", "/lazytype/sam"),
                ("IGNORE", "/ignore/george"),
                ("REF", "kr/action"),
                ("ANONREF", "kr/"),
                ("REF", "o/obj"),
                ("WORD", "Objective"),
                ("ANONREF", "o/"),
                ("WORD", "Objective"),
                ("WORD", "Multiple"),
                ("WORD", "words"),
            ],
            tokens,
        )
