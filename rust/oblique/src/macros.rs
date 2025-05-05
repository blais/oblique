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

        self.macros.push(Macro {
            pattern: regex,
            replacement: replacement.to_string(),
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
}
