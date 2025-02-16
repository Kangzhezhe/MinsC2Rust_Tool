pub struct IntLocation(pub i32);
pub fn int_hash(location: IntLocation) -> u32 {
    location.0 as u32
}
