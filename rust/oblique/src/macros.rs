//! Macro system for the Oblique language
#![allow(dead_code)]

use crate::error::Error;
use regex::Regex;
use std::collections::HashMap;

/// A macro definition in the Oblique language
#[derive(Debug, Clone)]
pub struct Macro {
    /// The pattern to match
    pub pattern: Regex,

    /// The replacement template
    pub replacement: String,
}

/// A collection of macros
#[derive(Debug, Default)]
pub struct MacroSystem {
    /// The macros defined in the system
    macros: Vec<Macro>,
}

impl MacroSystem {
    /// Create a new empty macro system
    pub fn new() -> Self {
        Self { macros: Vec::new() }
    }

    /// Add a macro to the system
    pub fn add_macro(&mut self, pattern: &str, replacement: &str) -> Result<(), Error> {
        let regex =
            Regex::new(pattern).map_err(|_| Error::InvalidMacroPattern(pattern.to_string()))?;

        // Convert \1 to $1 for Rust regex compatibility
        let rust_replacement = Regex::new(r"\\(\d+)")
            .unwrap()
            .replace_all(replacement, "$$${1}")
            .to_string();

        self.macros.push(Macro {
            pattern: regex,
            replacement: rust_replacement,
        });

        Ok(())
    }

    /// Apply macros to a string
    pub fn apply(&self, input: &str) -> String {
        let mut result = input.to_string();

        for mac in &self.macros {
            result = mac
                .pattern
                .replace_all(&result, &mac.replacement)
                .to_string();
        }

        result
    }
}

/// A collection of render rules
#[derive(Debug, Default)]
pub struct RenderSystem {
    /// The render rules defined in the system
    renders: HashMap<String, String>,
}

impl RenderSystem {
    /// Create a new empty render system
    pub fn new() -> Self {
        Self {
            renders: HashMap::new(),
        }
    }

    /// Add a render rule to the system
    pub fn add_render(&mut self, type_name: &str, template: &str) {
        self.renders
            .insert(type_name.to_string(), template.to_string());
    }

    /// Render a reference
    pub fn render(&self, type_name: &str, ident: &str) -> String {
        if let Some(template) = self.renders.get(type_name) {
            template.replace("\\1", ident)
        } else {
            format!("{}/{}", type_name, ident)
        }
    }

    /// Merge another render system into this one
    pub fn merge(&mut self, other: RenderSystem) {
        self.renders.extend(other.renders);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_macro_system_basic() {
        let mut ms = MacroSystem::new();
        ms.add_macro(r"\bP(\d)\b", "p/$1").unwrap();
        
        assert_eq!(ms.apply("Task P0"), "Task p/0");
        assert_eq!(ms.apply("P1 and P2"), "p/1 and p/2");
        assert_eq!(ms.apply("No match"), "No match");
    }

    #[test]
    fn test_macro_system_backreference_conversion() {
        let mut ms = MacroSystem::new();
        // Test \1 conversion to $1
        ms.add_macro(r"test(\d)", r"result/\1").unwrap();
        assert_eq!(ms.apply("test5"), "result/5");
    }

    #[test]
    fn test_render_system() {
        let mut rs = RenderSystem::new();
        rs.add_render("p", "Project: \\1");
        
        assert_eq!(rs.render("p", "alpha"), "Project: alpha");
        assert_eq!(rs.render("u", "bob"), "u/bob"); // Default
    }

    #[test]
    fn test_render_system_merge() {
        let mut rs1 = RenderSystem::new();
        rs1.add_render("p", "P: \\1");
        
        let mut rs2 = RenderSystem::new();
        rs2.add_render("u", "U: \\1");
        
        rs1.merge(rs2);
        
        assert_eq!(rs1.render("p", "test"), "P: test");
        assert_eq!(rs1.render("u", "test"), "U: test");
    }
}
