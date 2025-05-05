//! Error types for the Oblique parser

use std::path::PathBuf;
use thiserror::Error;

/// Errors that can occur during parsing and processing of Oblique files
#[derive(Error, Debug)]
pub enum Error {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Parse error at line {line}: {message}")]
    Parse { line: usize, message: String },

    #[error("Definition for undeclared type '{0}' at line {1}")]
    UndeclaredType(String, usize),

    #[error("Invalid type '{0}' in reference '{0}/{1}' at line {2}")]
    InvalidType(String, String, usize),

    #[error("Duplicate definition for '{0}/{1}' at line {2}")]
    DuplicateDefinition(String, String, usize),

    #[error("Failed to import file {0}: {1}")]
    Import(PathBuf, Box<Error>),

    #[error("Invalid macro pattern: {0}")]
    InvalidMacroPattern(String),
}
