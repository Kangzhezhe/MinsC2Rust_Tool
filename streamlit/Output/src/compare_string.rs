pub fn string_nocase_compare(string1: &str, string2: &str) -> i32 {
    let mut p1 = string1.chars();
    let mut p2 = string2.chars();

    loop {
        let c1 = p1.next().map_or('\0', |c| c.to_ascii_lowercase());
        let c2 = p2.next().map_or('\0', |c| c.to_ascii_lowercase());

        if c1 != c2 {
            if c1 < c2 {
                return -1;
            } else {
                return 1;
            }
        }

        if c1 == '\0' {
            break;
        }
    }

    0
}

pub fn string_nocase_equal(string1: &str, string2: &str) -> bool {
    string_nocase_compare(string1, string2) == 0
}

pub fn string_compare(string1: &str, string2: &str) -> i32 {
    let result = string1.cmp(string2);

    match result {
        std::cmp::Ordering::Less => -1,
        std::cmp::Ordering::Greater => 1,
        std::cmp::Ordering::Equal => 0,
    }
}

pub fn string_equal(string1: &str, string2: &str) -> bool {
    string1 == string2
}
