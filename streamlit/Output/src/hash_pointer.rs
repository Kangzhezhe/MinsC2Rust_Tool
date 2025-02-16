pub fn pointer_hash<T>(location: std::rc::Rc<T>) -> u32 {
    let pointer_address = std::ptr::addr_of!(*location) as usize;
    pointer_address as u32
}
