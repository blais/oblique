from absl.testing import absltest

from matplotlib import pyplot
import networkx as nx

from oblique import extmodule
from oblique import nxutils


class ApiTests(absltest.TestCase):

  def test_convert_to_nx(self):
    db = extmodule.parse_string("""\
       Conquer the world.
    """)
    g = nxutils.convert_to_nx(db)
    self.assertIsInstance(g, nx.DiGraph)


if __name__ == '__main__':
  absltest.main()
