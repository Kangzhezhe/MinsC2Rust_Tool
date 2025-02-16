pub fn pointer_equal<T>(location1: &T, location2: &T) -> bool {
    std::ptr::eq(location1, location2)
}

pub fn pointer_compare<T>(location1: &T, location2: &T) -> i32 {
    use std::cmp::Ordering;

    match (location1 as *const T).cmp(&(location2 as *const T)) {
        Ordering::Less => -1,
        Ordering::Greater => 1,
        Ordering::Equal => 0,
    }
}
