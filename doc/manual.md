# Oblique Language Manual

Oblique is a minimalistic, typed data definition language designed for creating graph databases of short text definitions. It allows you to define objects, typed relationships, and macros in plain text files, which can then be parsed, queried, or rendered into other formats (like HTML).

This manual documents the implementation of the Oblique language parser and CLI tool.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Language Reference](#language-reference)
    - [Comments](#comments)
    - [Types](#types)
    - [Objects](#objects)
    - [References](#references)
    - [Macros](#macros)
    - [Rendering](#rendering)
    - [Imports](#imports)
3. [CLI Usage](#cli-usage)
    - [Basic Parsing](#basic-parsing)
    - [Querying](#querying)
    - [JSON Output](#json-output)
4. [Complete Example](#complete-example)

---

## Getting Started

### Prerequisites

- [Rust](https://www.rust-lang.org/) (cargo) installed.

### Installation

Clone the repository and build the project:

```bash
cd rust/oblique
cargo build --release
```

The binary will be available at `target/release/oblique`.

---

## Language Reference

Oblique files are processed line-by-line. All declarations must generally appear before they are used (though macros and types apply to the parsing context they are defined in).

### Comments

Lines starting with `#` are treated as comments and ignored.

```oblique
# This is a comment
p/project1 My Project # This is NOT a comment (inline comments not supported in text content)
```

### Types

Before defining objects, you typically define **Types**. There are three "flavors" of types:

#### 1. Strict Types (`/type/`)
References to strict types must resolve to an existing, defined object. If you reference `t/1` and `t/1` is never defined, the parser generally treats it as an unresolved reference (or an error in strict mode validation).

**Syntax:** `/type/<typename> <Description>`

```oblique
/type/p Project
/type/t Task
```

#### 2. Lazy Types (`/lazytype/`)
References to lazy types **automatically create** the object if it doesn't exist. This is perfect for external entities like users, dates, or bug tickets where you don't want to manually define every single instance.

**Syntax:** `/lazytype/<typename> <Description>`

```oblique
/lazytype/u User
/lazytype/d Date
```

#### 3. Ignore Types (`/ignore/`)
References to these types are parsed but effectively ignored or stripped during resolution. Useful for annotation links that shouldn't affect the data graph.

**Syntax:** `/ignore/<typename> <Description>`

```oblique
/ignore/ext External Link
```

### Objects

The core of Oblique is the **Object**. An object consists of:
- A **Type**
- An **Identifier** (ID)
- **Content** (Text)

**Syntax:** `<type>/<id> <Content>`

```oblique
p/apollo Project Apollo
t/123 Fix the landing gear
```

#### Auto-IDs
You can omit the ID, and Oblique will assign one (mostly used for the default `item` type, but syntax allows `<type>/` with trailing space).

```oblique
# Explicit empty ID (rarely used)
t/ Some task without specific ID
```

#### Default Items
Lines that do not start with a command or a specific object definition are treated as "Items" (default type `item`).

```oblique
Just a note about something.
```
Is equivalent to:
```oblique
item/<auto-id> Just a note about something.
```

### References

You link objects by mentioning another object's reference ID within the content.

**Syntax:** `<type>/<id>`

```oblique
t/101 Fix bug reported by u/alice in p/apollo
```
In this example:
- `t/101` is the object being defined.
- It contains references to `u/alice` and `p/apollo`.

### Macros

Macros allow you to create shorthand syntax that expands into full object references. This keeps your text clean and readable.

Macros use **Regex** for matching and support `\1`, `\2`, etc., for capture groups replacement.

**Syntax:** `/macro <regex_pattern> <replacement>`

**Example:**
Map "P1", "P2" to priority objects `p/1`, `p/2`:

```oblique
/type/p Priority

# Match word boundary, "P", followed by a digit
/macro \bP(\d)\b p/\1

# Usage
item/1 Fix critical bug P0
```
*Input:* `item/1 Fix critical bug P0`
*Expanded:* `item/1 Fix critical bug p/0`

### Rendering

You can define how references are displayed when using the CLI tools (and potentially for HTML export).

**Syntax:** `/render <typename> <template>`
Use `\1` in the template to represent the object's ID.

**Example:**
Render users with an `@` symbol and projects as HTML links.

```oblique
/render u @\1
/render p <a href="/projects/\1">Project \1</a>

# When outputting:
# u/john -> @john
# p/alpha -> <a href="/projects/alpha">Project alpha</a>
```

### Imports

You can split your data across multiple files.

**Syntax:** `/import <filename>`

```oblique
/import definitions.oblique
/import 2023/tasks.oblique
```
Imports are recursive and relative to the file path.

---

## CLI Usage

The `oblique` tool processes your files.

### Basic Parsing
Read a file and dump the parsed database to stdout (human-readable text).

```bash
cargo run -- my_data.oblique
```

### Querying
Filter objects by type using the `--query` (or `-q`) flag.

**Syntax:** `--query "type:<typename>"`

```bash
# List all objects of type 'p' (Project)
cargo run -- my_data.oblique -q "type:p"
```

### JSON Output
Export the entire database (Types and Objects) to JSON for processing by other tools.

```bash
cargo run -- my_data.oblique --format json
```

---

## Complete Example

Create a file named `journal.oblique`:

```oblique
# --- Configuration ---
/type/p Project
/lazytype/u User
/lazytype/tag Tag

# Rendering Rules
/render p [\1]
/render u @\1
/render tag #\1

# Macros
# Convert #hashtag to tag/hashtag
/macro #([a-z]+) tag/\1
# Convert user@ to u/user
/macro ([a-z]+)@ u/\1

# --- Data ---

p/gemini Gemini CLI Project
p/web   Company Website

# Daily Log
Meeting with blais@ regarding p/gemini #design #api
Refactored the parser module #refactor
```

**Run it:**

```bash
$ cargo run -- journal.oblique
```

**Output (Text):**
```text
Types:
  p: Project (strict)
  u: User (lazy)
  tag: Tag (lazy)
  item: Item type (lazy)

Objects:
  item/1: Meeting with @blais regarding [gemini] #design #api
    References:
      [gemini]
      @blais
      #design
      #api
  item/2: Refactored the parser module #refactor
    References:
      #refactor
  p/gemini: Gemini CLI Project
  p/web: Company Website
  tag/api: 
  tag/design: 
  tag/refactor: 
  u/blais: 
```

**Query it:**

```bash
$ cargo run -- journal.oblique -q "type:item"
```

**Output:**
```text
Objects of type 'item':
  item/1 Meeting with @blais regarding [gemini] #design #api
  item/2 Refactored the parser module #refactor
```
