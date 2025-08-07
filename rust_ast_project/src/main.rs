use serde_json::json;
use std::env;
use std::fs;
use syn::{parse_file, spanned::Spanned, Item, Type};

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
            // Item::Impl(impl_item) => {
            //     if let Some((_, _, _)) = &impl_item.trait_ {
            //         // 忽略 trait 实现
            //         continue;
            //     }

            //     if let Type::Path(type_path) = *impl_item.self_ty.clone() {
            //         if let Some(segment) = type_path.path.segments.last() {
            //             let class_name = segment.ident.to_string();
            //             for item in impl_item.items {
            //                 if let syn::ImplItem::Method(method) = item {
            //                     let ident = &method.sig.ident;
            //                     let span = method.span();
            //                     let start = span.start();
            //                     let end = span.end();
            //                     definitions.push(json!({
            //                         "type": "Method",
            //                         "name": format!("{}::{}", class_name, ident),
            //                         "start_line": start.line,
            //                         "end_line": end.line,
            //                     }));
            //                 }
            //             }
            //         }
            //     }
            // }
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