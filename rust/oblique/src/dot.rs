use crate::database::Database;
use std::io::{self, Write};

fn sanitize_id(type_name: &str, ident: &str) -> String {
    format!("{}_{}", type_name, ident).replace(|c: char| !c.is_alphanumeric(), "_")
}

pub fn generate_dot<W: Write>(db: &Database, mut writer: W) -> io::Result<()> {
    writeln!(writer, "digraph Oblique {{ ")?;
    writeln!(writer, "  rankdir=LR;")?;
    writeln!(writer, "  node [shape=box, style=filled, fillcolor=white, fontname=\"Arial\"];")?;
    writeln!(writer, "  edge [color=\"#888888\"];")?;

    for (id, obj) in &db.objects {
        let node_id = sanitize_id(&id.type_name, id.ident.as_deref().unwrap_or(""));
        let rendered_label = db.render_system.render(&id.type_name, id.ident.as_deref().unwrap_or(""));
        
        // Truncate content for label
        let content_preview = if obj.contents.len() > 40 {
            format!("{}\
...", &obj.contents[..40])
        } else {
            obj.contents.clone()
        };
        
        // Escape quotes
        let label = format!("{}\
{}", rendered_label, content_preview).replace("\"", "\\\"");
        
        // Style based on type
        let (shape, color) = match id.type_name.as_str() {
            "q" => ("folder", "#E6F3FF"),      // Quarter (Blue-ish)
            "p" => ("component", "#EEEEEE"),   // Project (Grey)
            "u" => ("ellipse", "#FFF9C4"),     // User (Yellow)
            "t" => ("note", "#FFFFFF"),        // Task (White)
            "b" => ("diamond", "#FFCDD2"),     // Bug (Red)
            "m" => ("hexagon", "#C8E6C9"),     // Milestone (Green)
            "item" => ("plaintext", "white"),
            _ => ("box", "white"),
        };

        writeln!(writer, "  {} [label=\" { } \", shape={}, fillcolor=\" { } \"];", node_id, label, shape, color)?;

        for reference in &obj.refs {
             let target_id = sanitize_id(&reference.type_name, &reference.ident);
             writeln!(writer, "  {} -> {};", node_id, target_id)?;
        }
    }
    writeln!(writer, "}}")?;
    Ok(())
}
