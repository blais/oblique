//! Oblique Data Language parser implementation
//! 
//! This library provides functionality to parse and process files written in the
//! Oblique Data Language, a minimalistic language for defining typed data.

mod ast;
mod error;
mod lexer;
mod parser;
mod database;
mod macros;

pub use ast::{Type, TypeFlavor, Object, ObjectId, Reference};
pub use error::Error;
pub use database::Database;
pub use parser::parse_file;
