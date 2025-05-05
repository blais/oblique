//! Abstract Syntax Tree definitions for the Oblique language

use serde::{Deserialize, Serialize};
use std::collections::HashSet;

/// The flavor of a type, determining how references to it are handled
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TypeFlavor {
    /// Strict type - references must be defined
    Strict,

    /// Lazy type - references are automatically defined when referenced
    Lazy,

    /// Ignore type - references are treated as plain text
    Ignore,
}

/// A type definition in the Oblique language
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Type {
    /// The name of the type
    pub name: String,

    /// The description of the type
    pub contents: String,

    /// The flavor of the type
    pub flavor: TypeFlavor,

    /// The line number where this type was defined
    pub lineno: Option<usize>,
}

/// An identifier for an object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ObjectId {
    /// The type of the object
    pub type_name: String,

    /// The identifier of the object, if specified
    pub ident: Option<String>,
}

/// A reference to another object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Reference {
    /// The type of the referenced object
    pub type_name: String,

    /// The identifier of the referenced object
    pub ident: String,
}

/// An object in the Oblique language
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Object {
    /// The identifier of the object
    pub id: ObjectId,

    /// The contents of the object
    pub contents: String,

    /// References to other objects that have been resolved
    pub refs: HashSet<Reference>,

    /// References to other objects that have not been resolved
    pub unresolved_refs: HashSet<Reference>,

    /// The line number where this object was defined
    pub lineno: Option<usize>,
}
