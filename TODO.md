-*- mode: markdown; fill-column: 200 -*-

# TODO

g/resolve
  Move errors into their defining entity lines.
  Make options into a struct (defined as proto)
  Rename auto <-> lazy ?
  Beyond /type/ignore, add a list of ignored common words
  Add a flag to mark that a definition was an auto-def. Maybe even fill those in in the resolution, not during parsing.


g/build
  Setup clang build
    Read in-depth about Bazel toolchains and figure out if I shouldn't be using rules_m4 and rules_bison instead of the custom built ones I'm currently using.
    . This would have saved me some trouble with Clang.

  Modify rules for running pylint and pytype by default on all codes, while compiling.

g/parser
  Handle memory deallocation.

g/build
  Libraries which define their own `python_configure.bzl` are:
  . pybind/pybind11_bazel/python_configure.bzl
  . grpc/grpc/third_party/py/python_configure.bzl
  . google/riegeli/python/riegeli/python_configure.bzl
  . tensorflow/tensorflow/third_party/py/python_configure.bzl

Documentation

- Add the fact that the typename "item" is reserved.
- Document macros.

Implement indent, inheritance vs association, document it.
Three possible decisions to be made:
1. link to the parent element or to all the refs in that element
2. link to all parent refs, or just the immediate parent
3. make this different depending on whether the parent is a definition of just
   an item, or not.

Implement multiline support with '.' for continuation.

g/types
  Allow the user to impose schema onto the types? What would this mean?

g/rendering
  Make it possible to replace objrefs by their rendered item text, in place of their reference

  What about imposing constraints, e.g., "must include HH:MM", e.g., for music database
  Web app to browse the database of entities, also renders a subset of the graph entities w/ graphviz

g/perf
  Reduce memory allocations by using string_view onto a single buffer for the entire file in memory. This should be possible.
