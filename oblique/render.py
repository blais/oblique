"""Test program for rendering of a NetworkX graph of the databased."""

import time
import random
import collections
import argparse
import webbrowser
import logging

import networkx as nx

from oblique import extmodule
from oblique import nxutils


def main():
  parser = argparse.ArgumentParser(description=__doc__.strip())
  parser.add_argument('filename', help='Filename to parse')
  args = parser.parse_args()
  db = extmodule.parse_file(args.filename)

  logging.info("Convert")
  g = nxutils.convert_to_nx(db)
  agraph = nx.nx_agraph.to_agraph(g)

  logging.info("Layout")
  agraph.layout("fdp")
  tmp_filename = "/tmp/oblique.svg"

  logging.info("Drawing")
  agraph.draw(tmp_filename)

  logging.info("Opening {}".format(tmp_filename))
  webbrowser.open('file://{}'.format(tmp_filename))


if __name__ == '__main__':
   main()
