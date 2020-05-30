"""Bazel workspace for the Oblique language."""
workspace(name = "oblique")

load("//third_party/foreign:setup.bzl", "setup_rules_foreign")
setup_rules_foreign()

load("//third_party/cppbase:setup.bzl", "setup_cppbase")
setup_cppbase()

load("//third_party/python:setup.bzl", "setup_python")
setup_python()

load("//third_party/proto:setup.bzl", "setup_proto")
setup_proto()
load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
rules_proto_dependencies()
rules_proto_toolchains()

load("//third_party/parser:setup.bzl", "setup_parser")
setup_parser()
