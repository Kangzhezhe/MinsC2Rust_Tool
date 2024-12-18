use serde_json::json;
use std::env;
use std::fs;
use syn::{parse_file, spanned::Spanned, Item};

fn extract_definitions(file_path: &str) -> Result<serde_json::Value, Box<dyn std::error::Error>> {
    let content = fs::read_to_string(file_path)?;
    let file = parse_file(&content)?;

    let mut definitions = vec![];

    for item in file.items {
        match item {
            Item::Fn(func_item) => {
                let ident = &func_item.sig.ident;
                let span = func_item.span();
                let start = span.start();
                let end = span.end();
                definitions.push(json!({
                    "type": "Function",
                    "name": ident.to_string(),
                    "start_line": start.line,
                    "end_line": end.line,
                }));
            }
            _ => {}
        }
    }

    Ok(json!(definitions))
}

fn main() {
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <path_to_rust_file> <output_json_file>", args[0]);
        std::process::exit(1);
    }
    let rs_file_path = &args[1];
    let output_file_path = &args[2];

    match extract_definitions(rs_file_path) {
        Ok(definitions) => {
            let json_str =
                serde_json::to_string_pretty(&definitions).expect("Unable to serialize to JSON");
            fs::write(output_file_path, json_str).expect("Unable to write file");
        }
        Err(e) => {
            eprintln!("Error: {}", e);
        }
    }
}