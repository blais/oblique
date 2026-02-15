//! Command-line interface for the Oblique parser

use clap::Parser;
use serde_json::json;
use std::path::PathBuf;

use oblique::Database;

/// Command-line arguments
#[derive(Parser, Debug)]
#[clap(author, version, about)]
struct Args {
    /// Input file to parse
    #[clap(name = "FILE")]
    input_file: PathBuf,

    /// Output format (json or text)
    #[clap(short, long, default_value = "text")]
    format: String,

    /// Query string
    #[clap(short, long)]
    query: Option<String>,
}

fn main() {
    let args = Args::parse();

    // Create a new database
    let mut db = Database::new();

    // Import the file
    match db.import_file(&args.input_file) {
        Ok(()) => {
            if let Some(query) = args.query {
                // TODO: Implement proper query parsing
                // For now, simple "list items of type X"
                // format: "type:X"
                if query.starts_with("type:") {
                    let type_name = &query[5..];
                    println!("Objects of type '{}':", type_name);
                    for (id, obj) in &db.objects {
                        if id.type_name == type_name {
                             let rendered_id = db.render_system.render(&id.type_name, id.ident.as_deref().unwrap_or(""));
                             println!("  {} {}", rendered_id, obj.contents);
                        }
                    }
                } else {
                    eprintln!("Unsupported query format. Use 'type:<typename>'");
                }
                return;
            }

            // Output the database
            match args.format.as_str() {
                "json" => {
                    let output = json!({
                        "types": db.types,
                        "objects": db.objects,
                    });
                    println!("{}", serde_json::to_string_pretty(&output).unwrap());
                }
                _ => {
                    println!("Types:");
                    for (name, typ) in &db.types {
                        println!(
                            "  {}: {} ({})",
                            name,
                            typ.contents,
                            match typ.flavor {
                                oblique::TypeFlavor::Strict => "strict",
                                oblique::TypeFlavor::Lazy => "lazy",
                                oblique::TypeFlavor::Ignore => "ignore",
                            }
                        );
                    }

                    println!("\nObjects:");
                    for (id, obj) in &db.objects {
                        let rendered_id = db.render_system.render(&id.type_name, id.ident.as_deref().unwrap_or(""));
                        println!(
                            "  {}: {}",
                            rendered_id,
                            obj.contents
                        );

                        if !obj.refs.is_empty() {
                            println!("    References:");
                            for reference in &obj.refs {
                                let rendered_ref = db.render_system.render(&reference.type_name, &reference.ident);
                                println!("      {}", rendered_ref);
                            }
                        }

                        if !obj.unresolved_refs.is_empty() {
                            println!("    Unresolved References:");
                            for reference in &obj.unresolved_refs {
                                println!("      {}/{}", reference.type_name, reference.ident);
                            }
                        }
                    }
                }
            }
        }
        Err(err) => {
            eprintln!("Error: {}", err);
            std::process::exit(1);
        }
    }
}
