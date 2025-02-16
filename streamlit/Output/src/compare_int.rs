pub struct IntLocation(pub i32);
pub fn int_compare(a: &i32, b: &i32) -> i32 {
    a.cmp(b) as i32
}

pub fn int_equal(location1: &IntLocation, location2: &IntLocation) -> bool {
    location1.0 == location2.0
}
