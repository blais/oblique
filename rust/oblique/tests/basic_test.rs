use std::collections::HashSet;
use oblique::{Database, Type, TypeFlavor, Object, ObjectId, Reference};

#[test]
fn test_basic_parsing() {
    let input = r#"
    /type/task Task
    task/conquer Conquer the world
    "#;
    
    let mut db = Database::new();
    let (types, objects) = oblique::parse_file(input).unwrap();
    
    // Check types
    assert_eq!(types.len(), 2); // item type + task type
    
    let task_type = types.iter().find(|t| t.name == "task").unwrap();
    assert_eq!(task_type.contents, "Task");
    assert_eq!(task_type.flavor, TypeFlavor::Strict);
    
    // Check objects
    assert_eq!(objects.len(), 1);
    
    let task_obj = &objects[0];
    assert_eq!(task_obj.id.type_name, "task");
    assert_eq!(task_obj.id.ident, Some("conquer".to_string()));
    assert_eq!(task_obj.contents, "Conquer the world");
    assert!(task_obj.unresolved_refs.is_empty());
}

#[test]
fn test_references() {
    let input = r#"
    /type/task Task
    /type/user User
    task/conquer Conquer the world with user/alice
    "#;
    
    let (types, objects) = oblique::parse_file(input).unwrap();
    
    // Check objects
    assert_eq!(objects.len(), 1);
    
    let task_obj = &objects[0];
    assert_eq!(task_obj.id.type_name, "task");
    assert_eq!(task_obj.id.ident, Some("conquer".to_string()));
    
    // Check references
    assert_eq!(task_obj.unresolved_refs.len(), 1);
    
    let user_ref = task_obj.unresolved_refs.iter().next().unwrap();
    assert_eq!(user_ref.type_name, "user");
    assert_eq!(user_ref.ident, "alice");
}

#[test]
fn test_lazy_types() {
    let input = r#"
    /lazytype/user User
    task/conquer Conquer the world with user/alice
    "#;
    
    let mut db = Database::new();
    let (types, mut objects) = oblique::parse_file(input).unwrap();
    
    for typ in types {
        db.add_type(typ);
    }
    
    for obj in objects {
        db.add_object(obj).unwrap();
    }
    
    db.resolve_references().unwrap();
    
    // Check that the user reference was automatically created
    let user_id = ObjectId {
        type_name: "user".to_string(),
        ident: Some("alice".to_string()),
    };
    
    assert!(db.objects.contains_key(&user_id));
}
