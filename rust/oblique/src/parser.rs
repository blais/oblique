//! Parser for the Oblique language

use std::collections::{HashSet};
use std::path::{Path, PathBuf};
use std::fs;

use crate::ast::{Type, TypeFlavor, Object, ObjectId, Reference};
use crate::error::Error;
use crate::lexer::{tokenize_line, Token};
use crate::macros::{MacroSystem, RenderSystem};

/// A stateful parser for the Oblique language
pub struct Parser {
    pub types: Vec<Type>,
    pub objects: Vec<Object>,
    pub macro_system: MacroSystem,
    pub render_system: RenderSystem,
    search_paths: Vec<PathBuf>,
}

impl Parser {
    /// Create a new parser
    pub fn new() -> Self {
        let mut parser = Self {
            types: Vec::new(),
            objects: Vec::new(),
            macro_system: MacroSystem::new(),
            render_system: RenderSystem::new(),
            search_paths: Vec::new(),
        };

        // Add the default item type
        parser.types.push(Type {
            name: "item".to_string(),
            contents: "Item type".to_string(),
            flavor: TypeFlavor::Lazy,
            lineno: None,
        });

        parser
    }

    /// Add a search path for imports
    pub fn add_search_path<P: AsRef<Path>>(&mut self, path: P) {
        self.search_paths.push(path.as_ref().to_path_buf());
    }

    /// Parse a file
    pub fn parse_file<P: AsRef<Path>>(&mut self, path: P) -> Result<(), Error> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)
            .map_err(|e| Error::Io(e))?;

        // Add the file's directory to search paths for relative imports
        if let Some(parent) = path.parent() {
            self.add_search_path(parent);
        }

        self.parse_string(&content)
    }

    /// Parse a string
    pub fn parse_string(&mut self, content: &str) -> Result<(), Error> {
        let lines: Vec<&str> = content.lines().collect();
        let mut line_idx = 0;
        
        // Stack of (indentation_level, parent_reference)
        let mut context_stack: Vec<(usize, Reference)> = Vec::new();

        while line_idx < lines.len() {
            let original_line = lines[line_idx];
            line_idx += 1;

            // Calculate indentation
            let trimmed = original_line.trim_start();
            if trimmed.is_empty() {
                continue;
            }
            
            let indent = original_line.len() - trimmed.len();
            
            // Adjust stack based on indentation
            while !context_stack.is_empty() {
                if context_stack.last().unwrap().0 >= indent {
                    context_stack.pop();
                } else {
                    break;
                }
            }
            
            // Capture parent reference before processing the line
            let parent_ref = context_stack.last().map(|(_, r)| r.clone());

            // Skip comments (check after indent calc but before macro/tokenizing to allow indented comments)
            if trimmed.starts_with('#') {
                continue;
            }

            // Apply macros
            let line = self.macro_system.apply(original_line);
            
            let tokens = tokenize_line(&line);
            if tokens.is_empty() {
                continue;
            }

            // Helper to add parent ref
            let add_parent = |obj: &mut Object, parent: Option<Reference>| {
                if let Some(p) = parent {
                    // Add to unresolved_refs (which acts as the bucket for all refs initially)
                    obj.unresolved_refs.insert(p);
                }
            };

            match &tokens[0] {
                Token::TypeDecl(name) => {
                    let contents = self.join_tokens(&tokens[1..tokens.len()-1]);
                    self.types.push(Type {
                        name: name.clone(),
                        contents,
                        flavor: TypeFlavor::Strict,
                        lineno: Some(line_idx),
                    });
                },
                Token::LazyTypeDecl(name) => {
                    let contents = self.join_tokens(&tokens[1..tokens.len()-1]);
                    self.types.push(Type {
                        name: name.clone(),
                        contents,
                        flavor: TypeFlavor::Lazy,
                        lineno: Some(line_idx),
                    });
                },
                Token::IgnoreTypeDecl(name) => {
                    let contents = self.join_tokens(&tokens[1..tokens.len()-1]);
                    self.types.push(Type {
                        name: name.clone(),
                        contents,
                        flavor: TypeFlavor::Ignore,
                        lineno: Some(line_idx),
                    });
                },
                Token::MacroDecl => {
                    // Parse macro from the raw line to preserve spaces and slashes in replacement
                    let trimmed = line.trim();
                    // Skip "/macro"
                    if let Some(rest) = trimmed.strip_prefix("/macro") {
                        let rest = rest.trim_start();
                        // Find end of pattern (first whitespace)
                        if let Some(idx) = rest.find(char::is_whitespace) {
                            let pattern = &rest[..idx];
                            let replacement = rest[idx..].trim_start();
                            
                            self.macro_system.add_macro(pattern, replacement)?;
                        } else {
                             return Err(Error::Parse {
                                line: line_idx,
                                message: "Invalid macro declaration: missing replacement".to_string(),
                            });
                        }
                    } else {
                         // Should not happen if token was MacroDecl
                    }
                },
                Token::RenderDecl => {
                    // Parse render from the raw line
                    let trimmed = line.trim();
                     // Skip "/render"
                    if let Some(rest) = trimmed.strip_prefix("/render") {
                        let rest = rest.trim_start();
                        // Find end of type (first whitespace)
                        if let Some(idx) = rest.find(char::is_whitespace) {
                            let type_name = &rest[..idx];
                            let template = rest[idx..].trim_start(); // Keep the rest of the line as template
                            
                            self.render_system.add_render(type_name, template);
                        } else {
                             return Err(Error::Parse {
                                line: line_idx,
                                message: "Invalid render declaration: missing template".to_string(),
                            });
                        }
                    }
                },
                Token::ImportDecl => {
                    if tokens.len() < 2 {
                        return Err(Error::Parse {
                            line: line_idx,
                            message: "Invalid import declaration".to_string(),
                        });
                    }

                    let filename = match &tokens[1] {
                        Token::Word(w) => w.clone(),
                        _ => return Err(Error::Parse {
                            line: line_idx,
                            message: "Invalid import filename".to_string(),
                        }),
                    };

                    self.handle_import(&filename)?;
                },
                Token::Reference { type_name, ident } => {
                    let contents = self.join_tokens(&tokens[1..tokens.len()-1]);
                    let (refs, unresolved_refs) = self.extract_references(&tokens[1..tokens.len()-1]);

                    let mut obj = Object {
                        id: ObjectId {
                            type_name: type_name.clone(),
                            ident: Some(ident.clone()),
                        },
                        contents,
                        refs,
                        unresolved_refs,
                        lineno: Some(line_idx),
                    };
                    add_parent(&mut obj, parent_ref);
                    
                    // Update stack
                    context_stack.push((indent, Reference { type_name: type_name.clone(), ident: ident.clone() }));
                    
                    self.objects.push(obj);
                },
                Token::AutoReference(type_name) => {
                    let contents = self.join_tokens(&tokens[1..tokens.len()-1]);
                    let (refs, unresolved_refs) = self.extract_references(&tokens[1..tokens.len()-1]);

                    let mut obj = Object {
                        id: ObjectId {
                            type_name: type_name.clone(),
                            ident: None,
                        },
                        contents,
                        refs,
                        unresolved_refs,
                        lineno: Some(line_idx),
                    };
                    add_parent(&mut obj, parent_ref);
                    
                    // Note: We can't push auto-ref to stack easily because we don't have the final ID yet.
                    // The ID is generated in Database::add_object.
                    // For now, we simply don't push it to stack, so children won't inherit from it.
                    // TODO: To support this, we'd need to pre-allocate IDs or change architecture.
                    
                    self.objects.push(obj);
                },
                Token::Word(_) => {
                    let contents = self.join_tokens(&tokens[0..tokens.len()-1]);
                    let (refs, unresolved_refs) = self.extract_references(&tokens[0..tokens.len()-1]);

                    let mut obj = Object {
                        id: ObjectId {
                            type_name: "item".to_string(),
                            ident: None,
                        },
                        contents,
                        refs,
                        unresolved_refs,
                        lineno: Some(line_idx),
                    };
                    add_parent(&mut obj, parent_ref);
                    
                    // Same as AutoReference, can't push to stack without ID.
                    
                    self.objects.push(obj);
                },
                _ => {}
            }
        }

        Ok(())
    }

    fn handle_import(&mut self, filename: &str) -> Result<(), Error> {
        // Try to find the file in search paths
        for path in &self.search_paths {
            let full_path = path.join(filename);
            if full_path.exists() {
                // We need to recurse. To avoid borrowing issues, we create a new parser 
                // or just call parse_file recursively?
                // parse_file takes &mut self, so recursion is fine.
                // We just need to handle infinite loops if needed, but for now simple recursion.
                
                // Note: We need to handle relative imports from the *imported* file.
                // parse_file adds the parent dir to search paths, so it should work.
                return self.parse_file(full_path);
            }
        }

        // Try just the filename directly
        let path = PathBuf::from(filename);
        if path.exists() {
            return self.parse_file(path);
        }

        Err(Error::Import(
            PathBuf::from(filename), 
            Box::new(std::io::Error::new(std::io::ErrorKind::NotFound, "File not found").into())
        ))
    }

    fn join_tokens(&self, tokens: &[Token]) -> String {
        tokens
            .iter()
            .map(|t| match t {
                Token::Word(w) => w.clone(),
                Token::Reference { type_name, ident } => format!("{}/{}", type_name, ident),
                Token::AutoReference(t) => format!("{}/", t),
                _ => " ".to_string(),
            })
            .collect::<Vec<_>>()
            .join(" ")
    }

    fn extract_references(&self, tokens: &[Token]) -> (HashSet<Reference>, HashSet<Reference>) {
        let mut refs = HashSet::new();
        // Initially all refs are unresolved
        for token in tokens {
            if let Token::Reference { type_name, ident } = token {
                refs.insert(Reference {
                    type_name: type_name.clone(),
                    ident: ident.clone(),
                });
            }
        }
        (HashSet::new(), refs)
    }
}

/// Convenience wrapper to maintain backward compatibility if needed, 
/// though we will update usages.
pub fn parse_file<P: AsRef<Path>>(path: P) -> Result<(Vec<Type>, Vec<Object>, RenderSystem), Error> {
    let mut parser = Parser::new();
    parser.parse_file(path)?;
    Ok((parser.types, parser.objects, parser.render_system))
}

/// Parse a string containing Oblique code
pub fn parse_string(content: &str) -> Result<(Vec<Type>, Vec<Object>, RenderSystem), Error> {
    let mut parser = Parser::new();
    parser.parse_string(content)?;
    Ok((parser.types, parser.objects, parser.render_system))
}