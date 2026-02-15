use std::fs::File;
use std::io::Write;
use tempfile::tempdir;
use oblique::{Database, ObjectId};

#[test]
fn test_full_integration() {
    let dir = tempdir().unwrap();
    let main_path = dir.path().join("main.oblique");
    let imported_path = dir.path().join("imported.oblique");

    // Create imported file
    let mut imported_file = File::create(&imported_path).unwrap();
    writeln!(imported_file, r#"/type/p Project
p/alpha Project Alpha

# Macro to reference projects
/macro \bP([a-z]+)\b p/\1

o/obj1 Linked to Palpha
"#).unwrap();

    // Create main file
    let mut main_file = File::create(&main_path).unwrap();
    writeln!(main_file, r#"/lazytype/o Object
/lazytype/u User

/import imported.oblique

# Use macro from imported file? No, macros are lexically scoped to file usually, 
# but my implementation accumulates them in the Parser object. 
# So macros defined in imported files ARE available after import!
o/obj2 Linked to Palpha and u/bob

# Test Rendering
/render p <a href="/project/\1">\1</a>
"#).unwrap();

    let mut db = Database::new();
    db.import_file(&main_path).unwrap();

    // Check types
    assert!(db.types.contains_key("p"));
    assert!(db.types.contains_key("o"));
    assert!(db.types.contains_key("u"));

    // Check objects
    // p/alpha
    let p_alpha_id = ObjectId { type_name: "p".to_string(), ident: Some("alpha".to_string()) };
    assert!(db.objects.contains_key(&p_alpha_id));

    // o/obj1
    let obj1_id = ObjectId { type_name: "o".to_string(), ident: Some("obj1".to_string()) };
    let obj1 = db.objects.get(&obj1_id).unwrap();
    // Check reference to p/alpha (Palpha -> p/alpha via macro)
    assert!(obj1.refs.iter().any(|r| r.type_name == "p" && r.ident == "alpha"));

    // o/obj2
    let obj2_id = ObjectId { type_name: "o".to_string(), ident: Some("obj2".to_string()) };
    let obj2 = db.objects.get(&obj2_id).unwrap();
    // Check reference to p/alpha (macro usage from imported file)
    assert!(obj2.refs.iter().any(|r| r.type_name == "p" && r.ident == "alpha"));
    // Check reference to u/bob (lazy type)
    assert!(obj2.refs.iter().any(|r| r.type_name == "u" && r.ident == "bob"));

    // Check lazy object creation for u/bob
    let u_bob_id = ObjectId { type_name: "u".to_string(), ident: Some("bob".to_string()) };
    assert!(db.objects.contains_key(&u_bob_id));

    // Check rendering
    let rendered = db.render_system.render("p", "alpha");
    assert_eq!(rendered, "<a href=\"/project/alpha\">alpha</a>");
}
