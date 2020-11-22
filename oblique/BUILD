load("//third_party/python:py_extension.bzl", "py_extension")
load("//third_party/parser:bison.bzl", "genyacc")
load("//third_party/parser:reflex.bzl", "genreflex")
load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")
load("@rules_cc//cc:defs.bzl", "cc_binary")
load("@rules_cc//cc:defs.bzl", "cc_proto_library")
load("@rules_proto//proto:defs.bzl", "proto_library")
load("@subpar//:subpar.bzl", "par_binary")

#-------------------------------------------------------------------------------
# Scanner and grammar rules.

genreflex(
    name = "example_scanner_generated",
    src = "scanner.lxx",
    out = "scanner.cc",
    # Set this to true to debug the scanner.
    debug = False,
    header_out = "scanner.h",
    includes = [
        "parser.h",
    ],
)

genyacc(
    name = "parser_generated",
    src = "parser.yxx",
    location_out = "location.h",
    header_out = "parser.h",
    source_out = "parser.cc",
)


cc_library(
    name = "parser_headers",
    hdrs = [
        "scanner.h",
        "parser.h",
        "location.h",
    ],
)

cc_library(
    name = "parser",
    srcs = [
        "scanner.cc",
        "parser.cc",
    ],
    copts = [
        "-Wno-implicit-fallthrough",
        "-O2",
        "-Wno-sign-compare",
    ],
    # Generated and real files are interdependent.
    tags = ["nofixdeps"],
    deps = [
        "//third_party/parser:reflex",
        ":data_cc_pb2",
        ":data",
        ":parser_headers",
        "@com_google_absl//absl/container:flat_hash_map",
        "@com_google_absl//absl/strings",
    ],
)

cc_test(
    name = "scanner_test",
    srcs = ["scanner_test.cc"],
    deps = [
        ":test_utils",
        ":parser",
        "@com_google_googletest//:gtest_main",
    ],
)

cc_test(
    name = "parser_test",
    srcs = ["parser_test.cc"],
    deps = [
        ":test_utils",
        ":data_cc_pb2",
        ":parser",
        ":compile",
        "@com_google_googletest//:gtest_main",
        "@com_google_absl//absl/strings",
    ],
)

#-------------------------------------------------------------------------------

proto_library(
    name = "data_proto",
    srcs = ["data.proto"],
)

cc_proto_library(
    name = "data_cc_pb2",
    deps = [
        ":data_proto"
    ],
)

load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")

# TODO(blais): Figure out why we cannot just depend on the lib here rather than
# having to include the sources.
py_proto_library(
    name = "data_py_pb2",
    srcs = ["data.proto"],
    deps = [
        #":data_proto"
    ],
)

cc_library(
    name = "data",
    hdrs = ["data.h"],
    srcs = ["data.cc"],
    deps = [
        ":data_cc_pb2",
        "@com_google_absl//absl/strings",
    ],
)

cc_library(
    name = "test_utils",
    srcs = [
        "test_utils.cc"
    ],
    hdrs = [
        "test_utils.h"
    ],
    deps = [
        ":data_cc_pb2",
        "@com_google_absl//absl/strings",
        "@com_google_protobuf//:protobuf",
    ],
)

cc_test(
    name = "test_utils_test",
    srcs = ["test_utils_test.cc"],
    deps = [
        ":test_utils",
        ":data_cc_pb2",
        "@com_google_protobuf//:protobuf",
        "@com_google_googletest//:gtest_main",
    ],
)

cc_library(
    name = "compile",
    srcs = [
        "compile.cc"
    ],
    hdrs = [
        "compile.h"
    ],
    deps = [
        ":data",
        ":data_cc_pb2",
        "@com_google_absl//absl/status",
        "@com_google_absl//absl/strings",
        "@com_google_absl//absl/container:flat_hash_map",
    ],
)

cc_test(
    name = "compile_test",
    srcs = ["compile_test.cc"],
    deps = [
        ":test_utils",
        ":data_cc_pb2",
        ":parser",
        ":compile",
        "@com_google_googletest//:gtest_main",
        "@com_google_absl//absl/strings",
    ],
)

cc_binary(
    name = "parser_main",
    srcs = [
        "parser_main.cc"
    ],
    deps = [
        ":compile",
        ":data",
        ":data_cc_pb2",
        ":parser",
    ],
)

# pybind_extension(
#     name = "extmodule",
#     srcs = ["extmodule.cc"],
#     # copts = ["-DPYTHON_EXECUTABLE=/usr/bin/python3"],
#     deps = [
#         ":parser",
#     ],
# )
# TODO(blais): Let the pybind11 author know this works better.
py_extension(
    name = "extmodule",
    srcs = ["extmodule.cc"],
    deps = [
        "@local_config_python//:python_headers",
        "@pybind11",
        ":data",
        ":compile",
        ":data_cc_pb2",
        ":parser",
        "@com_google_absl//absl/strings",
    ],
)

# cc_library(
#     name = "extmodule_hdr",
#     hdrs = ["extmodule.h"],
#     deps = [
#         "@local_config_python//:python_headers",
#     ],
# )

# py_library(
#     name = "extmodule",
#     srcs = ["extmodule.py"],
#     deps = [
#         ":_extmodule",
#         ":grammar",
#         ":printer",
#         ":hashsrc",
#         "//beancount/core:data",
#         "//beancount/core:number",
#     ],
# )

py_test(
    name = "extmodule_test",
    srcs = ["extmodule_test.py"],
    deps = [
        ":extmodule",
    ],
)

py_library(
    name = "nxutils",
    srcs = ["nxutils.py"],
    deps = [
        ":extmodule",
    ],
)

py_test(
    name = "nxutils_test",
    srcs = ["nxutils_test.py"],
    deps = [
        ":nxutils",
        ":extmodule",
    ],
)

py_binary(
    name = "render",
    srcs = ["render.py"],
    deps = [
        ":extmodule",
        ":nxutils",
    ],
)

par_binary(
    name = "render.par",
    srcs = ["render.py"],
    main = "render.py",
    deps = [
        ":extmodule",
    ],
)
