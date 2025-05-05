# Oblique Language Parser

This is a Rust implementation of a parser for the Oblique Data Language, a minimalistic language for defining typed data.

## Features

- Parse Oblique language files
- Support for types, objects, and references
- Support for strict, lazy, and ignore type flavors
- Macro system for text substitution
- Render system for HTML output

## Usage

### As a Library

```rust
use oblique::{Database, parse_file};

fn main() {
    // Create a new database
    let mut db = Database::new();
    
    // Import a file
    db.import_file("example.oblique").unwrap();
    
    // Access the database
    for (id, obj) in &db.objects {
        println!("{}/{}: {}", id.type_name, id.ident.as_deref().unwrap_or("auto"), obj.contents);
    }
}
```

### As a Command-Line Tool

```bash
# Parse a file and output in text format
cargo run -- example.oblique

# Parse a file and output in JSON format
cargo run -- example.oblique --format json
```

## Oblique Language Syntax

The Oblique language is a simple language for defining typed data. Here's a quick overview:

### Type Declarations

```
/type/task Task
/lazytype/user User
/ignore/comment Comment
```

### Object Definitions

```
task/conquer Conquer the world
user/alice Alice Smith
```

### References

```
task/conquer Conquer the world with user/alice
```

### Auto-References

```
task/ A new task without an explicit ID
```

### Default Items

```
This is a default item with no explicit type or ID
```

### Macros

```
/macro \b([a-z]+)@\b user/\1
Meeting with bob@
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
