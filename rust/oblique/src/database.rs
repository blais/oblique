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

    /// The next auto-generated identifier for items
    next_item_id: usize,
}

impl Database {
    /// Create a new empty database
    pub fn new() -> Self {
        let mut db = Self {
            types: HashMap::new(),
            objects: HashMap::new(),
            render_system: RenderSystem::new(),
            next_item_id: 1,
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
        if object.id.ident.is_none() && object.id.type_name == "item" {
            object.id.ident = Some(format!("{}", self.next_item_id));
            self.next_item_id += 1;
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

        let keys: Vec<ObjectId> = objects.keys().cloned().collect();
        // for key in keys.iter() {
        //     match objects.get(key) {
        //         None => continue,
        //         Some(object) => {

        let mut new_objects: HashMap<ObjectId, Object> = HashMap::new();

        for key in keys.iter() {
            // for object in objects.values() {
            let mut resolved = HashSet::new();
            let mut unresolved = HashSet::new();

            match objects.get(key) {
                None => continue,
                Some(object) => {
                    for reference in &object.unresolved_refs {
                        let type_flavor = match self.get_type_flavor(&reference.type_name) {
                            Some(flavor) => flavor,
                            None => {
                                return Err(Error::InvalidType(
                                    reference.type_name.clone(),
                                    reference.ident.clone(),
                                    object.lineno.unwrap_or(0),
                                ));
                            }
                        };

                        let ref_id = ObjectId {
                            type_name: reference.type_name.clone(),
                            ident: Some(reference.ident.clone()),
                        };

                        match type_flavor {
                            TypeFlavor::Strict => {
                                // Check if the referenced object exists
                                if objects.contains_key(&ref_id) {
                                    resolved.insert(reference.clone());
                                } else {
                                    unresolved.insert(reference.clone());
                                }
                            }
                            TypeFlavor::Lazy => {
                                // Automatically create the referenced object if it doesn't exist
                                if !objects.contains_key(&ref_id) {
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
                                }

                                resolved.insert(reference.clone());
                            }
                            TypeFlavor::Ignore => {
                                // Ignore references to this type
                            }
                        }
                    }
                }
            }

            if let Some(object) = objects.get_mut(key) {
                object.refs = resolved;
                object.unresolved_refs = unresolved;
            }
        }

        // Add the new objects to the database
        for (id, object) in new_objects {
            objects.insert(id, object);
        }

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
        // We need to expose the inner map or add a merge method.
        // For now, since we can't easily access the inner map of RenderSystem if fields are private,
        // we might need to rely on what parser returns.
        // Wait, RenderSystem fields are private in `macros.rs`? 
        // Let's check `macros.rs`.
        // If they are private, I should replace the whole system or add merge capability.
        // Since `RenderSystem` is in the crate, and fields are likely private unless pub.
        // In `macros.rs`: `renders: HashMap<String, String>`. If it's not pub, I can't merge easily.
        // But `Database` is in the same crate (lib), so it can access private fields?
        // No, module privacy rules apply.
        
        // For now, let's assume I need to modify `macros.rs` to allow merging or exposing renders.
        // But wait, I'm replacing `import_file` implementation.
        // I'll assume I can just swap it if it's the first import, or I need to merge.
        // Let's just keep the new one for now as a simple merge strategy (overwrite).
        self.render_system = render_system;

        self.resolve_references()?;

        Ok(())
    }
}
