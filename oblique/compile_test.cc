#include "oblique/compile.h"
#include "oblique/data.pb.h"
#include "oblique/parser.h"
#include "oblique/scanner.h"
#include "oblique/test_utils.h"

#include <algorithm>
#include <cassert>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include "absl/strings/string_view.h"
#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "reflex/input.h"

namespace oblique {
namespace {

// TODO(blais): When symbol_name() is made public, make a << operator on the symbol_type.
using std::pair;
using std::string;
using std::vector;
using std::cout;
using std::endl;
using absl::string_view;

// Run the parser and check that its proto output equivalent matches.
bool CheckResolve(string_view input, string_view expected_proto, int line_offset = 0) {
  string clean_string = StripAndDedent(input);
  std::unique_ptr<proto::Database> db = ParseString(clean_string, nullptr, line_offset);
  if (!Resolve(db.get(), true).ok()) {
    // TODO(blais): Issue compiling error.
  }
  ClearLineNumbers(db.get());
  return CompareMessages(*db, expected_proto);
}

#define EXPECT_COMPILE(input, expected_proto)           \
  EXPECT_TRUE(CheckResolve(input, expected_proto));

// One item with an associated type definition should be fine.
TEST(ResolveTest, DefToValid) {
  EXPECT_COMPILE(u8R"(
    /type/task Task.
    task/conquer All the world.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task."}
    object {id {type: "task" ident: "conquer"} contents: "All the world."}
  )");
}

// One item without a type declaration issues an error.
TEST(ResolveTest, DefToUndeclared) {
  EXPECT_COMPILE(u8R"(
    task/conquer All the world.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "task" ident: "conquer"} contents: "All the world."}
    error {lineno: 1
           error_message: "Definition for undeclared type \'task/conquer\'"}
  )");
}

// A reference to an undeclared type should be ignored by default.
TEST(ResolveTest, RefToUndeclared) {
  EXPECT_COMPILE(u8R"(
    All the world. task/conquer
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "item" ident: "0"}
            contents: "All the world. task/conquer"}
            #unresolved_refs {type: "task" ident: "conquer"}}
    # error {lineno: 1 error_message: "Invalid type \'task\' in reference \'task/conquer\'"}
  )");
}

// TODO(blais): Add test with eror


// A reference to a strictly declared type but it is not found.
TEST(ResolveTest, RefToStrictInvalid) {
  EXPECT_COMPILE(u8R"(
    /type/task Task
    All the world. task/conquer
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task"}
    object {id {type: "item" ident: "0"}
            contents: "All the world. task/conquer"
            unresolved_refs {type: "task" ident: "conquer"}}
    error {lineno: 2 error_message: "Invalid reference to strict type \'task/conquer\'"}
  )");
}

// A reference to a strictly declared type and it is found.
TEST(ResolveTest, RefToStrictValid) {
  EXPECT_COMPILE(u8R"(
    /type/task Task
    task/conquer Conquer it
    All the world. task/conquer
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task"}
    object {id {type: "task" ident: "conquer"}
            contents: "Conquer it"}
    object {id {type: "item" ident: "0"}
            contents: "All the world. task/conquer"
            refs {type: "task" ident: "conquer"}}
  )");
}

// A reference to an unknown lazy object should work and create that object
// on-the-fly; that's the intended use case for lazy references.
TEST(ResolveTest, RefToLazyInvalid) {
  EXPECT_COMPILE(u8R"(
    /lazytype/task Task
    All the world. task/conquer
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task" flavor: LAZY}
    object {id {type: "item" ident: "0"}
            contents: "All the world. task/conquer"
            refs {type: "task" ident: "conquer"}}
    object {id {type: "task" ident: "conquer"}}
  )");
}

// A reference to a valid object of a lazy type should do the same as that for a
// strict type.
TEST(ResolveTest, RefToLazyValid) {
  EXPECT_COMPILE(u8R"(
    /lazytype/task Task
    All the world. task/conquer
    task/conquer Conquer it
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task" flavor: LAZY}
    object {id {type: "item" ident: "0"}
            contents: "All the world. task/conquer"
            refs {type: "task" ident: "conquer"}}
    object {id {type: "task" ident: "conquer"}
            contents: "Conquer it"}
  )");
}

// A reference to an unknown instance of an ignored type should be kept as a
// word.
TEST(ResolveTest, RefToIgnoreInvalid) {
  EXPECT_COMPILE(u8R"(
    /ignore/task Task
    All the world. task/conquer
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task" flavor: IGNORE}
    object {id {type: "item" ident: "0"}
            contents: "All the world. task/conquer"}
  )");
}

// A reference to an apparently known instance of an ignored type should be kept
// as a word as well.
TEST(ResolveTest, RefToIgnoreValid) {
  EXPECT_COMPILE(u8R"(
    /ignore/task Task
    task/conquer Conquer it
    All the world. task/conquer
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task" flavor: IGNORE}
    object {id {type: "item" ident: "0"}
            contents: "task/conquer Conquer it"}
    object {id {type: "item" ident: "1"}
            contents: "All the world. task/conquer"}
  )");
}

// A definition of an instance of an ignored type should just appear as a word.
TEST(ResolveTest, DefToIgnore) {
  EXPECT_COMPILE(u8R"(
    /ignore/task Task
    task/conquer All the world.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task" flavor: IGNORE}
    object {id {type: "item" ident: "0"}
            contents: "task/conquer All the world."}
  )");
}

// An auto-definition of an instance of an ignored type should also just appear
// as a word.
TEST(ResolveTest, AutoDefToIgnore) {
  EXPECT_COMPILE(u8R"(
    /ignore/task Task
    task/ All the world.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task" flavor: IGNORE}
    object {id {type: "item" ident: "0"}
            contents: "task/ All the world."}
  )");
}

// TODO(blais): Add tests to auto defs from other types above.

}  // namespace
}  // namespace oblique
