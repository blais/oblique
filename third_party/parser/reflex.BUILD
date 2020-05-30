# Build file for Genivia's RE-Flex (https://github.com/Genivia/RE-flex)

cc_library(
    name = "reflex-lib",
    includes = ["include"],
    hdrs = glob(["include/reflex/*.h"]),
    srcs = glob(["lib/*.cpp", "unicode/*.cpp"]),
    copts = ["-march=native", "-mavx"],
    defines = ["HAVE_AVX"],
)

cc_library(
    name = "reflex-min",
    includes = ["include"],
    hdrs = glob(["include/reflex/*.h"]),
    srcs = ["lib/debug.cpp",
            "lib/error.cpp",
            "lib/input.cpp",
            "lib/matcher.cpp",
            "lib/pattern.cpp",
            "lib/utf8.cpp"],
    copts = ["-march=native", "-mavx"],
    defines = ["HAVE_AVX"],
)

cc_library(
    name = "reflex-main",
    includes = ["include"],
    hdrs = ["src/reflex.h"],
    srcs = ["src/reflex.cpp"],
    deps = [":reflex-lib"],
    copts = ["-march=native", "-mavx"],
    defines = ["HAVE_AVX"],
)

cc_binary(
    name = "reflex",
    deps = [":reflex-main"],
    copts = ["-march=native", "-mavx"],
    defines = ["HAVE_AVX"],
)

genrule(
    name = "example-wc-cpp",
    srcs = ["examples/wc.l"],
    outs = ["examples/wc.cpp"],
    cmd = "./$(location :reflex) --flex -o $@ $<",
    tools = [":reflex"],
)

cc_binary(
    name = "example-wc",
    srcs = [":example-wc-cpp"],
    deps = [":reflex-lib"],
)

# flexexample3:		flexexample3.l flexexample3.y
# 			$(YACC) -d flexexample3.y
# 			$(REFLEX) $(REFLAGS) --flex --bison flexexample3.l
# 			$(CC) $(CXXFLAGS) -c y.tab.c
# 			$(CXX) $(CXXFLAGS) -o $@ y.tab.o lex.yy.cpp $(LIBREFLEX)
# 			./flexexample3 < flexexample3.test

# flexexample5xx:		flexexample5.lxx flexexample5.yxx
# 			$(BISON) -d flexexample5.yxx
# 			$(REFLEX) $(REFLAGS) --flex --bison-bridge --header-file flexexample5.lxx
# 			$(CXX) $(CXXFLAGS) -o $@ flexexample5.tab.cxx lex.yy.cpp $(LIBREFLEX)
# 			./flexexample5xx < flexexample5.test
