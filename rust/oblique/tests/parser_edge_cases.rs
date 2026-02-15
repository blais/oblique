use oblique::{parse_string, TypeFlavor};

#[test]
fn test_ignore_type() {
    let input = r#"
    /ignore/link External Link
    item/1 Check link/google
    "#;
    
    let (types, objects, _) = parse_string(input).unwrap();
    
    // Check type flavor
    let link_type = types.iter().find(|t| t.name == "link").unwrap();
    assert_eq!(link_type.flavor, TypeFlavor::Ignore);
    
    // Check object refs - the parser extracts them as unresolved initially.
    // The Database::resolve_references logic handles the "Ignore" flavor by NOT moving them to resolved 
    // and presumably leaving them (or removing them? let's check implementation).
    // The implementation for Ignore says: "// Ignore references to this type" which implies they are skipped in the loop,
    // so they stay in 'unresolved' set inside the loop, but wait.
    // In `resolve_references`:
    // It iterates `unresolved_refs`.
    // Match Strict -> insert to resolved or unresolved.
    // Match Lazy -> insert to resolved (and create).
    // Match Ignore -> Do nothing.
    // So for Ignore, they are NOT added to `resolved` OR `unresolved` local sets.
    // Then `object.refs = resolved; object.unresolved_refs = unresolved;`
    // So effectively, references to Ignore types are REMOVED from the object's reference lists.
    
    // Let's verify this end-to-end behavior with a Database.
    let mut db = oblique::Database::new();
    for t in types { db.add_type(t); }
    for o in objects { db.add_object(o).unwrap(); }
    
    db.resolve_references().unwrap();
    
    let obj = db.objects.values().next().unwrap();
    assert!(obj.refs.is_empty());
    assert!(obj.unresolved_refs.is_empty());
}

#[test]
fn test_auto_reference_syntax() {
    let input = r#"
    /type/p Project
    p/ Project content
    "#;
    
    let (_, objects, _) = parse_string(input).unwrap();
    assert_eq!(objects.len(), 1);
    let obj = &objects[0];
    assert_eq!(obj.id.type_name, "p");
    assert_eq!(obj.id.ident, None);
    assert_eq!(obj.contents, "Project content");
}

#[test]
fn test_default_item_syntax() {
    let input = r#"
    Just a simple item
    "#;
    
    let (_, objects, _) = parse_string(input).unwrap();
    assert_eq!(objects.len(), 1);
    let obj = &objects[0];
    assert_eq!(obj.id.type_name, "item");
    assert_eq!(obj.id.ident, None);
    assert_eq!(obj.contents, "Just a simple item");
}

#[test]
fn test_empty_input() {
    let input = "";
    let (types, objects, _) = parse_string(input).unwrap();
    assert_eq!(types.len(), 1); // Default item type
    assert!(objects.is_empty());
}
