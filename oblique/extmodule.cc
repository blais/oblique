#include "oblique/parser.h"
#include "oblique/compile.h"
#include "oblique/data.pb.h"
#include "oblique/data.h"

#include <memory>

#include "pybind11/pybind11.h"
#include "absl/strings/str_cat.h"

namespace oblique {
namespace py = pybind11;

std::unique_ptr<proto::Database> parse_string(const std::string& input_string) {
  static const std::string filename = "<python-string>";
  return ParseString(input_string, filename);
}

std::unique_ptr<proto::Database> parse_file(const std::string& filename) {
  return ParseFile(filename);
}

std::unique_ptr<proto::Database> parse_stdin() {
  return ParseStdin();
}

// Iterator over all the edges of a node.
py::iterator object_refs(const proto::Object& obj) {
  const auto& refs = obj.refs();
  return py::make_iterator(refs.begin(), refs.end());
}

// Iterator over all the objects in a database.
py::iterator database_object(const proto::Database& db) {
  const auto& objects = db.object();
  return py::make_iterator(objects.begin(), objects.end());
}

// Shallow read-only interface to protobuf schema.
void ExportProtos(py::module& mod) {
  py::class_<proto::Ref>(mod, "Ref")
    .def(py::init<>())
    .def_property_readonly("type", &proto::Ref::type)
    .def_property_readonly("ident", &proto::Ref::ident)
    .def("__str__", &proto::Ref::DebugString);

  py::class_<proto::Object>(mod, "Object")
    .def(py::init<>())
    .def_property_readonly("id", &proto::Object::id)
    .def_property_readonly("contents", &proto::Object::contents)
    .def("refs", &object_refs)
    .def("__str__", &proto::Object::DebugString);

  py::class_<proto::Database>(mod, "Database")
    .def(py::init<>())
    .def("__str__", &proto::Database::DebugString)
    .def("object", &database_object);
}

}  // namespace oblique


PYBIND11_MODULE(extmodule, mod) {
  mod.doc() = "Pybind11 bindings for Oblique";

  // Export the read-only proto interface.
  oblique::ExportProtos(mod);

  // Top-level entry point.
  mod.def("parse_string", &oblique::parse_string, "Parse an Oblique language string");
  mod.def("parse_file", &oblique::parse_file, "Parse an Oblique language file");
  mod.def("parse_stdin", &oblique::parse_stdin, "Parse an Oblique language from stdin");
}
