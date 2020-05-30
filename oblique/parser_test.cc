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
bool CheckParse(string_view input, string_view expected_proto, int line_offset = 0) {
  string clean_string = StripAndDedent(input);
  auto actual_db = ParseString(clean_string, nullptr, line_offset);
  ClearLineNumbers(actual_db.get());
  return CompareMessages(*actual_db, expected_proto);
}

// // Serious wizardry in effect to get the line at the start of macro expansion.
// #define EXPECT_PARSE (SAVE_LINE RUN_CHECK
// #define SAVE_LINE { int lineno = __LINE__;
// #define RUN_CHECK(...) EXPECT_TRUE(CheckParse(__VA_ARGS__, lineno)); } )

#define EXPECT_PARSE(input, expected_proto)             \
  EXPECT_TRUE(CheckParse(input, expected_proto));

// Test just one item.
TEST(ParserTest, OneItem) {
  EXPECT_PARSE(u8R"(
    Conquer the world.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "item" ident: "0"} contents: "Conquer the world."}
  )");
}

// Test a few more items.
TEST(ParserTest, ManyItems) {
  EXPECT_PARSE(u8R"(
    Conquer the world.
    Conquer the world again.
    And again.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "item" ident: "0"} contents: "Conquer the world."}
    object {id {type: "item" ident: "1"} contents: "Conquer the world again."}
    object {id {type: "item" ident: "2"} contents: "And again."}
  )");
}

// Test one object reference.
TEST(ParserTest, UseOneRef) {
  EXPECT_PARSE(u8R"(
    Conquer the world with u/caroline
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "item" ident: "0"}
            contents: "Conquer the world with u/caroline"
            unresolved_refs {type: "u" ident: "caroline"}}
  )");
}

// Test use multiple references.
TEST(ParserTest, UseMultiRef) {
  EXPECT_PARSE(u8R"(
    Conquer the world with u/caroline and u/kai
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "item" ident: "0"}
            contents: "Conquer the world with u/caroline and u/kai"
            unresolved_refs {type: "u" ident: "caroline"}
            unresolved_refs {type: "u" ident: "kai"}}
  )");
}

// Test explicit definition of object.
TEST(ParserTest, ObjDef) {
  EXPECT_PARSE(u8R"(
    type/task Task
    task/conquer Conquer the world
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "type" ident: "task"}
            contents: "Task"}
    object {id {type: "task" ident: "conquer"}
            contents: "Conquer the world"}
  )");
}

// Test explicit definition of object with auto-id.
TEST(ParserTest, ObjAutoDef) {
  EXPECT_PARSE(u8R"(
    type/task Task
    task/ Conquer the world
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "type" ident: "task"}
            contents: "Task"}
    object {id {type: "task" ident: "0"}
            contents: "Conquer the world"}
  )");
}

// Test refs within the contents.
TEST(ParserTest, UsingRef) {
  EXPECT_PARSE(u8R"(
    task/conquer Conquer the world with u/caroline
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    object {id {type: "task" ident: "conquer"}
            contents: "Conquer the world with u/caroline"
            unresolved_refs {type: "u" ident: "caroline"}}
  )");
}

// Test type declaration
TEST(ParserTest, TypeDeclaration) {
  EXPECT_PARSE(u8R"(
    /type/task Task.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task."}
  )");
}

// TODO(blais): Do something to store lazy types properly in the graph.
// Test lazy type declaration
TEST(ParserTest, LazyTypeDeclaration) {
  EXPECT_PARSE(u8R"(
    /lazytype/task Task.
  )", u8R"(
    type {type: "item" contents: "Item type" flavor: LAZY}
    type {type: "task" contents: "Task." flavor: LAZY}
  )");
}

}  // namespace
}  // namespace oblique
