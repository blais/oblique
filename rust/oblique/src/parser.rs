//! Parser for the Oblique language

use std::collections::{HashSet};
use std::path::Path;
use std::fs;

use crate::ast::{Type, TypeFlavor, Object, ObjectId, Reference};
use crate::error::Error;
use crate::lexer::{tokenize_line, Token};
use crate::macros::{MacroSystem, RenderSystem};

/// Parse a file containing Oblique code
pub fn parse_file<P: AsRef<Path>>(path: P) -> Result<(Vec<Type>, Vec<Object>), Error> {
    let content = fs::read_to_string(path)
        .map_err(|e| Error::Io(e))?;

    parse_string(&content)
}

/// Parse a string containing Oblique code
pub fn parse_string(content: &str) -> Result<(Vec<Type>, Vec<Object>), Error> {
    let mut types = Vec::new();
    let mut objects = Vec::new();
    let mut macro_system = MacroSystem::new();
    let mut render_system = RenderSystem::new();

    // Add the default item type
    types.push(Type {
        name: "item".to_string(),
        contents: "Item type".to_string(),
        flavor: TypeFlavor::Lazy,
        lineno: None,
    });

    let lines: Vec<&str> = content.lines().collect();
    let mut line_idx = 0;

    while line_idx < lines.len() {
        let line = lines[line_idx].trim();
        line_idx += 1;

        // Skip empty lines and comments
        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        let tokens = tokenize_line(line);
        if tokens.is_empty() {
            continue;
        }

        match &tokens[0] {
            Token::TypeDecl(name) => {
                // Parse type declaration
                let contents = tokens[1..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                types.push(Type {
                    name: name.clone(),
                    contents,
                    flavor: TypeFlavor::Strict,
                    lineno: Some(line_idx),
                });
            },
            Token::LazyTypeDecl(name) => {
                // Parse lazy type declaration
                let contents = tokens[1..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                types.push(Type {
                    name: name.clone(),
                    contents,
                    flavor: TypeFlavor::Lazy,
                    lineno: Some(line_idx),
                });
            },
            Token::IgnoreTypeDecl(name) => {
                // Parse ignore type declaration
                let contents = tokens[1..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                types.push(Type {
                    name: name.clone(),
                    contents,
                    flavor: TypeFlavor::Ignore,
                    lineno: Some(line_idx),
                });
            },
            Token::MacroDecl => {
                // Parse macro declaration
                if tokens.len() < 3 {
                    return Err(Error::Parse {
                        line: line_idx,
                        message: "Invalid macro declaration".to_string(),
                    });
                }

                let pattern = match &tokens[1] {
                    Token::Word(w) => w.clone(),
                    _ => {
                        return Err(Error::Parse {
                            line: line_idx,
                            message: "Invalid macro pattern".to_string(),
                        });
                    }
                };

                let replacement = match &tokens[2] {
                    Token::Word(w) => w.clone(),
                    Token::Reference { type_name, ident } => format!("{}/{}", type_name, ident),
                    _ => {
                        return Err(Error::Parse {
                            line: line_idx,
                            message: "Invalid macro replacement".to_string(),
                        });
                    }
                };

                macro_system.add_macro(&pattern, &replacement)?;
            },
            Token::RenderDecl => {
                // Parse render declaration
                if tokens.len() < 3 {
                    return Err(Error::Parse {
                        line: line_idx,
                        message: "Invalid render declaration".to_string(),
                    });
                }

                let type_name = match &tokens[1] {
                    Token::Word(w) => w.clone(),
                    _ => {
                        return Err(Error::Parse {
                            line: line_idx,
                            message: "Invalid render type".to_string(),
                        });
                    }
                };

                let template = tokens[2..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                render_system.add_render(&type_name, &template);
            },
            Token::ImportDecl => {
                // Parse import declaration
                if tokens.len() < 2 {
                    return Err(Error::Parse {
                        line: line_idx,
                        message: "Invalid import declaration".to_string(),
                    });
                }

                let _filename = match &tokens[1] {
                    Token::Word(w) => w.clone(),
                    _ => {
                        return Err(Error::Parse {
                            line: line_idx,
                            message: "Invalid import filename".to_string(),
                        });
                    }
                };

                // TODO: Implement file import
            },
            Token::Reference { type_name, ident } => {
                // Parse object definition
                let contents = tokens[1..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        Token::Reference { type_name, ident } => format!("{}/{}", type_name, ident),
                        Token::AutoReference(t) => format!("{}/", t),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                // Extract references
                let mut refs = HashSet::new();
                for token in &tokens[1..tokens.len()-1] {
                    if let Token::Reference { type_name, ident } = token {
                        refs.insert(Reference {
                            type_name: type_name.clone(),
                            ident: ident.clone(),
                        });
                    }
                }

                objects.push(Object {
                    id: ObjectId {
                        type_name: type_name.clone(),
                        ident: Some(ident.clone()),
                    },
                    contents,
                    refs: HashSet::new(),
                    unresolved_refs: refs,
                    lineno: Some(line_idx),
                });
            },
            Token::AutoReference(type_name) => {
                // Parse auto-reference object definition
                let contents = tokens[1..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        Token::Reference { type_name, ident } => format!("{}/{}", type_name, ident),
                        Token::AutoReference(t) => format!("{}/", t),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                // Extract references
                let mut refs = HashSet::new();
                for token in &tokens[1..tokens.len()-1] {
                    if let Token::Reference { type_name, ident } = token {
                        refs.insert(Reference {
                            type_name: type_name.clone(),
                            ident: ident.clone(),
                        });
                    }
                }

                objects.push(Object {
                    id: ObjectId {
                        type_name: type_name.clone(),
                        ident: None,
                    },
                    contents,
                    refs: HashSet::new(),
                    unresolved_refs: refs,
                    lineno: Some(line_idx),
                });
            },
            Token::Word(_) => {
                // Parse default item
                let contents = tokens[0..tokens.len()-1]
                    .iter()
                    .map(|t| match t {
                        Token::Word(w) => w.clone(),
                        Token::Reference { type_name, ident } => format!("{}/{}", type_name, ident),
                        Token::AutoReference(t) => format!("{}/", t),
                        _ => " ".to_string(),
                    })
                    .collect::<Vec<_>>()
                    .join(" ");

                // Extract references
                let mut refs = HashSet::new();
                for token in &tokens[0..tokens.len()-1] {
                    if let Token::Reference { type_name, ident } = token {
                        refs.insert(Reference {
                            type_name: type_name.clone(),
                            ident: ident.clone(),
                        });
                    }
                }

                objects.push(Object {
                    id: ObjectId {
                        type_name: "item".to_string(),
                        ident: None,
                    },
                    contents,
                    refs: HashSet::new(),
                    unresolved_refs: refs,
                    lineno: Some(line_idx),
                });
            },
            _ => {
                // Skip other tokens
            }
        }
    }

    Ok((types, objects))
}
