//! Database for storing Oblique objects and types

use std::collections::{HashMap, HashSet};
use std::path::Path;

use crate::ast::{Object, ObjectId, Type, TypeFlavor};
use crate::error::Error;
use crate::macros::RenderSystem;
use crate::parser;

/// The database of Oblique objects and types
#[derive(Debug, Default)]
pub struct Database {
    /// The types defined in the database
    pub types: HashMap<String, Type>,

    /// The objects defined in the database
    pub objects: HashMap<ObjectId, Object>,

    /// The render system for the database
    pub render_system: RenderSystem,

    /// Next auto-generated identifier per type
    next_ids: HashMap<String, usize>,
}

impl Database {
    /// Create a new empty database
    pub fn new() -> Self {
        let mut db = Self {
            types: HashMap::new(),
            objects: HashMap::new(),
            render_system: RenderSystem::new(),
            next_ids: HashMap::new(),
        };

        // Add the default item type
        db.add_type(Type {
            name: "item".to_string(),
            contents: "Item type".to_string(),
            flavor: TypeFlavor::Lazy,
            lineno: None,
        });

        db
    }

    /// Add a type to the database
    pub fn add_type(&mut self, type_def: Type) {
        self.types.insert(type_def.name.clone(), type_def);
    }

    /// Add an object to the database
    pub fn add_object(&mut self, mut object: Object) -> Result<(), Error> {
        // Generate an ID if needed
        if object.id.ident.is_none() {
            let type_name = &object.id.type_name;
            let next_id = self.next_ids.entry(type_name.clone()).or_insert(1);
            object.id.ident = Some(format!("{}", next_id));
            *next_id += 1;
        }

        // Check for duplicate definitions
        if self.objects.contains_key(&object.id) {
            return Err(Error::DuplicateDefinition(
                object.id.type_name.clone(),
                object.id.ident.clone().unwrap_or_default(),
                object.lineno.unwrap_or(0),
            ));
        }

        // Add the object
        self.objects.insert(object.id.clone(), object);
        Ok(())
    }

    /// Get the type flavor for a type name
    pub fn get_type_flavor(&self, type_name: &str) -> Option<TypeFlavor> {
        self.types.get(type_name).map(|t| t.flavor)
    }

    /// Resolve references in the database
    pub fn resolve_references(&mut self) -> Result<(), Error> {
        let mut objects = std::mem::take(&mut self.objects);
        let mut new_objects: HashMap<ObjectId, Object> = HashMap::new();

        let keys: Vec<ObjectId> = objects.keys().cloned().collect();

        for key in &keys {
            let (resolved, unresolved) = {
                let object = objects.get(key).unwrap();
                let mut resolved = object.refs.clone();
                let mut unresolved = HashSet::new();

                for reference in &object.unresolved_refs {
                    let type_flavor = self.get_type_flavor(&reference.type_name).ok_or_else(|| {
                        Error::InvalidType(
                            reference.type_name.clone(),
                            reference.ident.clone(),
                            object.lineno.unwrap_or(0),
                        )
                    })?;

                    if type_flavor == TypeFlavor::Ignore {
                        continue;
                    }

                    let ref_id = ObjectId {
                        type_name: reference.type_name.clone(),
                        ident: Some(reference.ident.clone()),
                    };

                    let exists = objects.contains_key(&ref_id) || new_objects.contains_key(&ref_id);

                    if exists {
                        resolved.insert(reference.clone());
                    } else if type_flavor == TypeFlavor::Lazy {
                        new_objects.insert(
                            ref_id.clone(),
                            Object {
                                id: ref_id,
                                contents: String::new(),
                                refs: HashSet::new(),
                                unresolved_refs: HashSet::new(),
                                lineno: None,
                            },
                        );
                        resolved.insert(reference.clone());
                    } else {
                        // Strict and not found
                        unresolved.insert(reference.clone());
                    }
                }
                (resolved, unresolved)
            };

            let object = objects.get_mut(key).unwrap();
            object.refs = resolved;
            object.unresolved_refs = unresolved;
        }

        // Add the new objects to the database
        objects.extend(new_objects);
        self.objects = objects;
        Ok(())
    }

    /// Import objects and types from a file
    pub fn import_file<P: AsRef<Path>>(&mut self, path: P) -> Result<(), Error> {
        let (types, objects, render_system) = parser::parse_file(path.as_ref())?;

        for type_def in types {
            self.add_type(type_def);
        }

        for object in objects {
            self.add_object(object)?;
        }
        
        // Merge render system
        self.render_system.merge(render_system);

        self.resolve_references()?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_duplicate_definition() {
        let mut db = Database::new();
        let obj1 = Object {
            id: ObjectId { type_name: "t".to_string(), ident: Some("1".to_string()) },
            contents: "test".to_string(),
            refs: HashSet::new(),
            unresolved_refs: HashSet::new(),
            lineno: Some(1),
        };
        db.add_object(obj1.clone()).unwrap();

        let result = db.add_object(obj1);
        assert!(matches!(result, Err(Error::DuplicateDefinition(_, _, _))));
    }

    #[test]
    fn test_strict_type_missing_reference() {
        let mut db = Database::new();
        
        // Define strict type 's'
        db.add_type(Type {
            name: "s".to_string(),
            contents: "Strict".to_string(),
            flavor: TypeFlavor::Strict,
            lineno: None,
        });

        // Add object referring to non-existent 's/1'
        let mut unresolved = HashSet::new();
        unresolved.insert(crate::ast::Reference { type_name: "s".to_string(), ident: "1".to_string() });
        
        db.add_object(Object {
            id: ObjectId { type_name: "i".to_string(), ident: Some("1".to_string()) },
            contents: "ref".to_string(),
            refs: HashSet::new(),
            unresolved_refs: unresolved,
            lineno: Some(2),
        }).unwrap();

        // Resolving should leave it unresolved (or fail? The current implementation splits them into resolved/unresolved but doesn't error unless type is missing)
        // Wait, looking at resolve_references:
        // Strict -> checks if key exists. If yes -> resolved. If no -> unresolved.
        // It does NOT return an error for missing strict references, it just keeps them in unresolved_refs.
        // Errors only happen if type doesn't exist.
        
        db.resolve_references().unwrap();
        
        let obj = db.objects.get(&ObjectId { type_name: "i".to_string(), ident: Some("1".to_string()) }).unwrap();
        assert!(!obj.unresolved_refs.is_empty());
        assert!(obj.refs.is_empty());
    }

    #[test]
    fn test_invalid_type_reference() {
        let mut db = Database::new();
        
        // Add object referring to unknown type 'x'
        let mut unresolved = HashSet::new();
        unresolved.insert(crate::ast::Reference { type_name: "x".to_string(), ident: "1".to_string() });
        
        db.add_object(Object {
            id: ObjectId { type_name: "i".to_string(), ident: Some("1".to_string()) },
            contents: "ref".to_string(),
            refs: HashSet::new(),
            unresolved_refs: unresolved,
            lineno: Some(2),
        }).unwrap();

        let result = db.resolve_references();
        assert!(matches!(result, Err(Error::InvalidType(_, _, _))));
    }
}
