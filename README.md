# Oblique - Lightweigh Graph Language

> Oblique is to graphs,
> what Markdown is to documents, and
> what Beancount is to bookkeeping

Oblique is a DSL to define in-memory graph databases from text files. It
provides directives to declare a schema (type definitions) and a syntax to
define objects (rows).

> [!WARNING]
> This project is not released yet. This is work-in-progress for now.
> There isn't much to use as of yet, but if you do, do at your own peril.

## Documentation

See the [User Manual](doc/manual.md) for detailed usage instructions, syntax guide, and examples.

## Implementation

The core implementation is currently in Rust.

```bash
cd rust/oblique
cargo run -- examples/example.oblique
```

## Author

Martin Blais <blais@furius.ca>
