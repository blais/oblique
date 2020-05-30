import tempfile

from absl.testing import absltest
import networkx as nx

from oblique import extmodule


class ApiTests(absltest.TestCase):

  def test_parse_string(self):
    db = extmodule.parse_string("""\
       Conquer the world.
    """)
    self.assertIsInstance(db, extmodule.Database)

  def test_parse_file(self):
    with tempfile.NamedTemporaryFile(mode='w') as tmpfile:
      tmpfile.write("""\
          Conquer the world.
      """)
      tmpfile.flush()
      db = extmodule.parse_file(tmpfile.name)
    self.assertIsInstance(db, extmodule.Database)

  def test_proto_interface(self):
    db = extmodule.parse_string("""\
       t/conquer Conquer the world.
       And another world again.  t/conquer
    """)
    for node in db.object():
      self.assertIsInstance(node, extmodule.Object)
      self.assertIsInstance(node.id, extmodule.Ref)
      self.assertIsInstance(node.contents, str)
      for ref in node.refs():
        self.assertIsInstance(ref, extmodule.Ref)


if __name__ == '__main__':
  absltest.main()
