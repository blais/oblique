"""Test program for rendering of a NetworkX graph of the databased."""

import argparse
import collections
import random
import time
import webbrowser
from typing import Text

import colour
import networkx as nx

from oblique import extmodule


_COLORS = """
aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond
blue blueviolet brown burlywood cadetblue chartreuse chocolate coral
cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray
darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey
darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue
firebrick floralwhite forestgreen fuchsia gainsboro gold goldenrod gray grey
green greenyellow honeydew hotpink indianred indigo ivory khaki lavender
lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon
lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue
lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue
mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod
palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
powderblue purple red rosybrown royalblue saddlebrown salmon sandybrown seagreen
seashell sienna silver skyblue slateblue slategray slategrey snow springgreen
steelblue tan thistle tomato turquoise violet wheat yellow yellowgreen
""".split()


def make_id(ref: extmodule.Ref) -> Text:
  """Convert a ref to a string iddentifier."""
  return "{}/{}".format(ref.type, ref.ident)


def convert_to_nx(db: extmodule.Database) -> nx.DiGraph:
  """Convert an internal database to a NetworkX graph."""
  colors = list(_COLORS)
  colormap = collections.defaultdict(lambda: colors.pop())
  g = nx.DiGraph()
  for obj in db.object():
    color = colormap[obj.id.type]
    objid = make_id(obj.id) if obj.id.type != 'item' else obj.contents
    col = colour.Color(color)
    g.add_node(objid, contents=obj.contents, fillcolor="{}60".format(col.hex_l), style="filled")
    for ref in obj.refs():
      nid = make_id(ref)
      g.add_edge(objid, nid)
  return g


if __name__ == '__main__':
    main()
