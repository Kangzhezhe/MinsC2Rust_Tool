pub fn string_hash(string: &str) -> u32 {
    let mut result: u32 = 5381;
    for byte in string.bytes() {
        result = (result << 5) + result + byte as u32;
    }
    result
}

pub fn string_nocase_hash(string: &str) -> u32 {
    let mut result: u32 = 5381;
    for c in string.chars() {
        result = (result << 5) + result + c.to_ascii_lowercase() as u32;
    }
    result
}
