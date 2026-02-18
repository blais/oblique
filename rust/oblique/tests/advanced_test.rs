use oblique::{Database, ObjectId, parse_string, Error};
use std::path::PathBuf;

// 1. Macro Chaining Test
#[test]
fn test_macro_chaining() {
    // Macros are applied in order of definition.
    // A -> B, then B -> C. Input "A" should become "C".
    let input = r#"
    /macro A B
    /macro B C
    A
    "#;

    let (_, objects, _) = parse_string(input).unwrap();
    assert_eq!(objects.len(), 1);
    // The "item" logic in parser defaults to "item" type if just a word is found.
    // "C" is a word.
    assert_eq!(objects[0].contents, "C");
}

// 2. Lazy References Test
#[test]
fn test_lazy_references() {
    let input = r#"
    /lazytype/u User
    u/1 references u/2
    "#;

    let mut db = Database::new();
    let (types, objects, _) = parse_string(input).unwrap();
    
    for t in types { db.add_type(t); }
    for o in objects { db.add_object(o).unwrap(); }
    
    // This should resolve u/2 and create it because it is Lazy
    db.resolve_references().unwrap();

    let u1_id = ObjectId { type_name: "u".to_string(), ident: Some("1".to_string()) };
    let u2_id = ObjectId { type_name: "u".to_string(), ident: Some("2".to_string()) };

    assert!(db.objects.contains_key(&u1_id));
    assert!(db.objects.contains_key(&u2_id));

    let u1 = db.objects.get(&u1_id).unwrap();
    // Verify u1 refers to u2
    assert!(u1.refs.iter().any(|r| r.type_name == "u" && r.ident == "2"));
}

// 3. Indentation Hierarchy Test
#[test]
fn test_indentation_hierarchy() {
    let input = r#"
    /type/node Node
    node/1 Root
        node/2 Child
            node/3 Grandchild
    "#;

    let mut db = Database::new();
    let (types, objects, _) = parse_string(input).unwrap();
    
    for t in types { db.add_type(t); }
    for o in objects { db.add_object(o).unwrap(); }
    db.resolve_references().unwrap();

    let _n1_id = ObjectId { type_name: "node".to_string(), ident: Some("1".to_string()) };
    let n2_id = ObjectId { type_name: "node".to_string(), ident: Some("2".to_string()) };
    let n3_id = ObjectId { type_name: "node".to_string(), ident: Some("3".to_string()) };

    let n2 = db.objects.get(&n2_id).unwrap();
    let n3 = db.objects.get(&n3_id).unwrap();

    // n2 should refer to n1 (parent)
    // Actually, let's verify exact parentage. 
    // Indentation stack logic:
    // node/1 (indent 4) -> pushed to stack
    //   node/2 (indent 8) -> parent is node/1
    //     node/3 (indent 12) -> parent is node/2
    
    assert!(n2.refs.iter().any(|r| r.type_name == "node" && r.ident == "1"));
    assert!(n3.refs.iter().any(|r| r.type_name == "node" && r.ident == "2"));
    
    // n3 should NOT refer to n1 directly
    assert!(!n3.refs.iter().any(|r| r.type_name == "node" && r.ident == "1"));
}

// 4. Complex Regex Macros Test
#[test]
fn test_complex_regex_macros() {
    let input = r#"
    /macro \buser_(\d+)\b u/\1
    user_123
    "#;

    let (_, objects, _) = parse_string(input).unwrap();
    assert_eq!(objects.len(), 1);
    let obj = &objects[0];
    
    // Expect "u/123" to be parsed as a Reference, not a Word
    assert_eq!(obj.id.type_name, "u");
    assert_eq!(obj.id.ident, Some("123".to_string()));
}

// 5. Error Handling Tests
#[test]
fn test_duplicate_definition_error() {
    let input = r#"
    /type/t T
    t/1 First definition
    t/1 Second definition
    "#;

    let mut db = Database::new();
    let (types, objects, _) = parse_string(input).unwrap();
    
    for t in types { db.add_type(t); }
    
    // First add should succeed
    db.add_object(objects[0].clone()).unwrap();
    
    // Second add should fail
    let result = db.add_object(objects[1].clone());
    
    match result {
        Err(Error::DuplicateDefinition(t, i, _)) => {
            assert_eq!(t, "t");
            assert_eq!(i, "1");
        },
        _ => panic!("Expected DuplicateDefinition error, got {:?}", result),
    }
}

#[test]
fn test_top_level_import_io_error() {
    let mut db = Database::new();
    // Top-level import_file uses fs::read_to_string directly, so it returns Error::Io
    let result = db.import_file("non_existent_file.oblique");
    
    match result {
        Err(Error::Io(_)) => {}, // Success
        _ => panic!("Expected Io error, got {:?}", result),
    }
}

#[test]
fn test_nested_import_error() {
    // Nested imports use the handle_import logic which returns Error::Import
    let input = r#"
    /import non_existent_file.oblique
    "#;
    
    let result = parse_string(input);
    
    match result {
        Err(Error::Import(path, _)) => {
            assert_eq!(path, PathBuf::from("non_existent_file.oblique"));
        },
        _ => panic!("Expected Import error, got {:?}", result),
    }
}