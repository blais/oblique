//! Lexer for the Oblique language

use lazy_static::lazy_static;
use regex::Regex;

/// Token types for the Oblique lexer
#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    /// A word (any non-whitespace text)
    Word(String),

    /// A reference to an object (type/id)
    Reference { type_name: String, ident: String },

    /// An auto-reference (type/ with no id)
    AutoReference(String),

    /// A type declaration (/type/name)
    TypeDecl(String),

    /// A lazy type declaration (/lazytype/name)
    LazyTypeDecl(String),

    /// An ignore type declaration (/ignore/name)
    IgnoreTypeDecl(String),

    /// A macro declaration (/macro)
    MacroDecl,

    /// An import declaration (/import)
    ImportDecl,

    /// A render declaration (/render)
    RenderDecl,

    /// A comment (# text)
    Comment(String),

    /// End of line
    EOL,
}

lazy_static! {
    static ref WORD_RE: Regex = Regex::new(r"^[^\s/]+").unwrap();
    static ref REFERENCE_RE: Regex = Regex::new(r"^([a-z]+)/([^\s]+)").unwrap();
    static ref AUTO_REFERENCE_RE: Regex = Regex::new(r"^([a-z]+)/\s").unwrap();
    static ref TYPE_DECL_RE: Regex = Regex::new(r"^/type/([a-z]+)").unwrap();
    static ref LAZY_TYPE_DECL_RE: Regex = Regex::new(r"^/lazytype/([a-z]+)").unwrap();
    static ref IGNORE_TYPE_DECL_RE: Regex = Regex::new(r"^/ignore/([a-z]+)").unwrap();
    static ref MACRO_DECL_RE: Regex = Regex::new(r"^/macro\b").unwrap();
    static ref IMPORT_DECL_RE: Regex = Regex::new(r"^/import\b").unwrap();
    static ref RENDER_DECL_RE: Regex = Regex::new(r"^/render\b").unwrap();
    static ref COMMENT_RE: Regex = Regex::new(r"^#(.*)$").unwrap();
}

/// Tokenize a line of Oblique code
pub fn tokenize_line(line: &str) -> Vec<Token> {
    let mut tokens = Vec::new();
    let mut remaining = line.trim_start();

    // Empty line
    if remaining.is_empty() {
        tokens.push(Token::EOL);
        return tokens;
    }

    // Process tokens until the line is empty
    while !remaining.is_empty() {
        if remaining.starts_with(' ') {
            remaining = remaining.trim_start();
            continue;
        }

        // Comment
        if let Some(captures) = COMMENT_RE.captures(remaining) {
            tokens.push(Token::Comment(captures[1].to_string()));
            tokens.push(Token::EOL);
            return tokens;
        }

        // Try to match each token type
        if let Some(captures) = TYPE_DECL_RE.captures(remaining) {
            tokens.push(Token::TypeDecl(captures[1].to_string()));
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = LAZY_TYPE_DECL_RE.captures(remaining) {
            tokens.push(Token::LazyTypeDecl(captures[1].to_string()));
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = IGNORE_TYPE_DECL_RE.captures(remaining) {
            tokens.push(Token::IgnoreTypeDecl(captures[1].to_string()));
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = MACRO_DECL_RE.captures(remaining) {
            tokens.push(Token::MacroDecl);
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = IMPORT_DECL_RE.captures(remaining) {
            tokens.push(Token::ImportDecl);
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = RENDER_DECL_RE.captures(remaining) {
            tokens.push(Token::RenderDecl);
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = AUTO_REFERENCE_RE.captures(remaining) {
            tokens.push(Token::AutoReference(captures[1].to_string()));
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = REFERENCE_RE.captures(remaining) {
            tokens.push(Token::Reference {
                type_name: captures[1].to_string(),
                ident: captures[2].to_string(),
            });
            remaining = &remaining[captures[0].len()..];
        } else if let Some(captures) = WORD_RE.captures(remaining) {
            tokens.push(Token::Word(captures[0].to_string()));
            remaining = &remaining[captures[0].len()..];
        } else {
            // If we can't match anything, just take the next character as a word
            tokens.push(Token::Word(remaining[0..1].to_string()));
            remaining = &remaining[1..];
        }
    }

    tokens.push(Token::EOL);
    tokens
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tokenize_simple_words() {
        let tokens = tokenize_line("hello world");
        assert_eq!(
            tokens,
            vec![
                Token::Word("hello".to_string()),
                Token::Word("world".to_string()),
                Token::EOL
            ]
        );
    }

    #[test]
    fn test_tokenize_reference() {
        let tokens = tokenize_line("p/alpha");
        assert_eq!(
            tokens,
            vec![
                Token::Reference {
                    type_name: "p".to_string(),
                    ident: "alpha".to_string()
                },
                Token::EOL
            ]
        );
    }

    #[test]
    fn test_tokenize_mixed() {
        let tokens = tokenize_line("Task p/alpha needs action");
        assert_eq!(
            tokens,
            vec![
                Token::Word("Task".to_string()),
                Token::Reference {
                    type_name: "p".to_string(),
                    ident: "alpha".to_string()
                },
                Token::Word("needs".to_string()),
                Token::Word("action".to_string()),
                Token::EOL
            ]
        );
    }

    #[test]
    fn test_tokenize_declarations() {
        assert_eq!(
            tokenize_line("/type/p Project"),
            vec![
                Token::TypeDecl("p".to_string()),
                Token::Word("Project".to_string()),
                Token::EOL
            ]
        );
        
        assert_eq!(
            tokenize_line("/lazytype/u User"),
            vec![
                Token::LazyTypeDecl("u".to_string()),
                Token::Word("User".to_string()),
                Token::EOL
            ]
        );

        assert_eq!(
            tokenize_line("/ignore/x IgnoreMe"),
            vec![
                Token::IgnoreTypeDecl("x".to_string()),
                Token::Word("IgnoreMe".to_string()),
                Token::EOL
            ]
        );
    }

    #[test]
    fn test_tokenize_commands() {
        assert_eq!(
            tokenize_line("/macro pattern replacement"),
            vec![
                Token::MacroDecl,
                Token::Word("pattern".to_string()),
                Token::Word("replacement".to_string()),
                Token::EOL
            ]
        );

        assert_eq!(
            tokenize_line("/render p <template>"),
            vec![
                Token::RenderDecl,
                Token::Word("p".to_string()),
                Token::Word("<template>".to_string()),
                Token::EOL
            ]
        );

        assert_eq!(
            tokenize_line("/import file.oblique"),
            vec![
                Token::ImportDecl,
                Token::Word("file.oblique".to_string()),
                Token::EOL
            ]
        );
    }

    #[test]
    fn test_tokenize_comments() {
        assert_eq!(
            tokenize_line("# This is a comment"),
            vec![
                Token::Comment(" This is a comment".to_string()),
                Token::EOL
            ]
        );

        assert_eq!(
            tokenize_line("content # comment"),
            vec![
                Token::Word("content".to_string()),
                Token::Comment(" comment".to_string()),
                Token::EOL
            ]
        );
    }

    #[test]
    fn test_tokenize_auto_reference() {
        assert_eq!(
            tokenize_line("p/ content"),
            vec![
                Token::AutoReference("p".to_string()),
                Token::Word("content".to_string()),
                Token::EOL
            ]
        );
    }
}
