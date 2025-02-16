use test_project::hash_table::{
    hash_table_allocate_table, hash_table_enlarge, hash_table_free, hash_table_free_entry,
    hash_table_insert, hash_table_iter_has_more, hash_table_iter_next, hash_table_iterate,
    hash_table_lookup, hash_table_new, hash_table_num_entries, hash_table_register_free_functions,
    hash_table_remove, HashTable, HashTableEntry, HashTableEqualFunc, HashTableHashFunc,
    HashTableIterator, HashTableKey, HashTableKeyFreeFunc, HashTablePair, HashTableValue,
    HashTableValueFreeFunc, ALLOCATED_KEYS, ALLOCATED_VALUES, HASH_TABLE_NUM_PRIMES,
    HASH_TABLE_PRIMES, NUM_TEST_VALUES,
};
pub fn generate_hash_table() -> Option<Box<HashTable>> {
    fn string_hash(value: HashTableKey) -> u32 {
        use std::ffi::CStr;
        use std::os::raw::c_char;
        let cstr = unsafe { CStr::from_ptr(value as *const c_char) };
        let s = cstr.to_string_lossy();
        s.chars().fold(0, |acc, c| acc + c as u32)
    }

    fn string_equal(value1: HashTableKey, value2: HashTableKey) -> i32 {
        use std::ffi::CStr;
        use std::os::raw::c_char;
        let cstr1 = unsafe { CStr::from_ptr(value1 as *const c_char) };
        let cstr2 = unsafe { CStr::from_ptr(value2 as *const c_char) };
        if cstr1 == cstr2 {
            1
        } else {
            0
        }
    }

    fn free(_value: *const std::ffi::c_void) {}

    let mut hash_table = match hash_table_new(string_hash, string_equal) {
        Some(table) => table,
        None => return None,
    };

    for i in 0..NUM_TEST_VALUES {
        let value_str = format!("{}", i);
        let value = value_str.into_bytes();
        let key = Box::leak(value.clone().into_boxed_slice()) as *const _ as HashTableKey;
        let value = Box::leak(value.into_boxed_slice()) as *const _ as HashTableValue;

        hash_table_insert(&mut hash_table, key, value);
    }

    hash_table_register_free_functions(&mut hash_table, None, Some(free));

    Some(hash_table)
}

pub fn new_key<T>(value: T) -> Option<Box<T>> {
    let mut result = Box::new(value);
    ALLOCATED_KEYS.with(|keys| keys.set(keys.get() + 1));
    Some(result)
}

pub fn new_value(value: i32) -> HashTableValue {
    let result = Box::into_raw(Box::new(value)) as HashTableValue;
    ALLOCATED_VALUES.with(|av| av.borrow_mut().count += 1);
    result
}

pub fn free_value(value: HashTableValue) {
    drop(unsafe { Box::from_raw(value as *mut i32) });
}

#[test]
pub fn test_hash_iterator_key_pair() {
    let mut hash_table = hash_table_new(int_hash, int_equal).expect("Failed to create hash table");
    let mut iterator = HashTableIterator {
        hash_table: None,
        next_entry: None,
        next_chain: 0,
    };
    let value1 = 1;
    let value2 = 2;
    let mut pair: HashTablePair;

    /* Add some values */
    hash_table_insert(
        &mut hash_table,
        &value1 as *const i32 as HashTableKey,
        &value1 as *const i32 as HashTableValue,
    );
    hash_table_insert(
        &mut hash_table,
        &value2 as *const i32 as HashTableKey,
        &value2 as *const i32 as HashTableValue,
    );

    hash_table_iterate(&mut hash_table, &mut iterator);

    while hash_table_iter_has_more(&mut iterator) {
        /* Retrieve both Key and Value */
        pair = hash_table_iter_next(&mut iterator);

        let key = pair.0 as *const i32;
        let val = pair.1 as *const i32;

        assert_eq!(unsafe { *key }, unsafe { *val });
    }

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_insert_lookup() {
    let mut hash_table = match generate_hash_table() {
        Some(table) => table,
        None => return,
    };

    assert_eq!(hash_table_num_entries(&hash_table), NUM_TEST_VALUES);

    for i in 0..NUM_TEST_VALUES {
        let value_str = format!("{}", i);
        let value = value_str.as_bytes();
        let key = Box::leak(value.to_vec().into_boxed_slice()) as *const _ as HashTableKey;
        let found_value = hash_table_lookup(&hash_table, key);

        assert_eq!(
            found_value.map(|v| unsafe {
                std::str::from_utf8_unchecked(std::slice::from_raw_parts(
                    v as *const u8,
                    value.len(),
                ))
            }),
            Some(value_str.as_str())
        );
    }

    let invalid_values = [-1, NUM_TEST_VALUES as i32];
    for &invalid_value in &invalid_values {
        let value_str = format!("{}", invalid_value);
        let value = value_str.as_bytes();
        let key = Box::leak(value.to_vec().into_boxed_slice()) as *const _ as HashTableKey;
        let found_value = hash_table_lookup(&hash_table, key);

        assert!(found_value.is_none());
    }

    let overwrite_key_str = "12345";
    let overwrite_key = overwrite_key_str.as_bytes();
    let overwrite_key_ptr =
        Box::leak(overwrite_key.to_vec().into_boxed_slice()) as *const _ as HashTableKey;
    let overwrite_value_str = "hello world";
    let overwrite_value = overwrite_value_str.as_bytes();
    let overwrite_value_ptr =
        Box::leak(overwrite_value.to_vec().into_boxed_slice()) as *const _ as HashTableValue;

    hash_table_insert(&mut hash_table, overwrite_key_ptr, overwrite_value_ptr);
    let found_overwrite_value = hash_table_lookup(&hash_table, overwrite_key_ptr);

    assert_eq!(
        found_overwrite_value.map(|v| unsafe {
            std::str::from_utf8_unchecked(std::slice::from_raw_parts(
                v as *const u8,
                overwrite_value.len(),
            ))
        }),
        Some(overwrite_value_str)
    );

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_iterating() {
    let mut hash_table = generate_hash_table().unwrap();
    let mut iterator = HashTableIterator {
        hash_table: None,
        next_entry: None,
        next_chain: 0,
    };
    let mut count = 0;

    hash_table_iterate(&mut hash_table, &mut iterator);

    while hash_table_iter_has_more(&mut iterator) {
        hash_table_iter_next(&mut iterator);
        count += 1;
    }

    assert_eq!(count, NUM_TEST_VALUES);

    let pair = hash_table_iter_next(&mut iterator);
    assert_eq!(pair.1, std::ptr::null());

    hash_table_free(hash_table);

    let mut hash_table = hash_table_new(int_hash, int_equal).unwrap();
    let mut iterator = HashTableIterator {
        hash_table: None,
        next_entry: None,
        next_chain: 0,
    };

    hash_table_iterate(&mut hash_table, &mut iterator);

    assert_eq!(hash_table_iter_has_more(&mut iterator), false);

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_out_of_memory() {
    let mut hash_table = match hash_table_new(int_hash, int_equal) {
        Some(table) => table,
        None => return,
    };

    let mut values: [i32; 66] = [0; 66];
    let mut i: u32 = 0;

    // Test normal failure
    values[0] = 0;
    assert_eq!(
        hash_table_insert(
            &mut hash_table,
            &values[0] as *const i32 as HashTableKey,
            &values[0] as *const i32 as HashTableValue
        ),
        0
    );
    assert_eq!(hash_table_num_entries(&hash_table), 0);

    // Test failure when increasing table size.
    // The initial table size is 193 entries. The table increases in
    // size when 1/3 full, so the 66th entry should cause the insert
    // to fail.

    for i in 0..65 {
        values[i as usize] = i as i32;

        assert_ne!(
            hash_table_insert(
                &mut hash_table,
                &values[i as usize] as *const i32 as HashTableKey,
                &values[i as usize] as *const i32 as HashTableValue
            ),
            0
        );
        assert_eq!(hash_table_num_entries(&hash_table), i + 1);
    }

    assert_eq!(hash_table_num_entries(&hash_table), 65);

    // Test the 66th insert
    values[65] = 65;

    assert_eq!(
        hash_table_insert(
            &mut hash_table,
            &values[65] as *const i32 as HashTableKey,
            &values[65] as *const i32 as HashTableValue
        ),
        0
    );
    assert_eq!(hash_table_num_entries(&hash_table), 65);

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_new_free() {
    let value1 = 1;
    let value2 = 2;
    let value3 = 3;
    let value4 = 4;

    let mut hash_table = hash_table_new(int_hash, int_equal);

    assert!(hash_table.is_some());

    let mut hash_table = hash_table.unwrap();

    /* Add some values */
    hash_table_insert(
        &mut hash_table,
        &value1 as *const _ as HashTableKey,
        &value1 as *const _ as HashTableValue,
    );
    hash_table_insert(
        &mut hash_table,
        &value2 as *const _ as HashTableKey,
        &value2 as *const _ as HashTableValue,
    );
    hash_table_insert(
        &mut hash_table,
        &value3 as *const _ as HashTableKey,
        &value3 as *const _ as HashTableValue,
    );
    hash_table_insert(
        &mut hash_table,
        &value4 as *const _ as HashTableKey,
        &value4 as *const _ as HashTableValue,
    );

    /* Free the hash table */
    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_iterating_remove() {
    let mut hash_table = generate_hash_table().unwrap();
    let mut iterator = HashTableIterator {
        hash_table: None,
        next_entry: None,
        next_chain: 0,
    };

    let mut count = 0;
    let mut removed = 0;

    hash_table_iterate(&mut hash_table, &mut iterator);

    while hash_table_iter_has_more(&mut iterator) {
        let pair = hash_table_iter_next(&mut iterator);
        let val = pair.1 as *const u8;
        let val_str = unsafe { std::ffi::CStr::from_ptr(val as *const std::os::raw::c_char) }
            .to_string_lossy();

        if val_str.parse::<u32>().unwrap() % 100 == 0 {
            hash_table_remove(&mut hash_table, pair.0);
            removed += 1;
        }

        count += 1;
    }

    assert_eq!(removed, 100);
    assert_eq!(count, NUM_TEST_VALUES as usize);

    assert_eq!(
        hash_table_num_entries(&hash_table),
        NUM_TEST_VALUES - removed as u32
    );

    for i in 0..NUM_TEST_VALUES {
        let buf = format!("{}", i);
        let buf_c = std::ffi::CString::new(buf).unwrap();
        let key = buf_c.as_ptr() as HashTableKey;

        if i % 100 == 0 {
            assert!(hash_table_lookup(&hash_table, key).is_none());
        } else {
            assert!(hash_table_lookup(&hash_table, key).is_some());
        }
    }

    hash_table_free(hash_table);
}

#[test]
pub fn test_hash_table_remove() {
    let mut hash_table = match generate_hash_table() {
        Some(table) => table,
        None => return,
    };

    assert_eq!(hash_table_num_entries(&hash_table), NUM_TEST_VALUES);
    let mut buf = String::with_capacity(10);
    buf.push_str("5000");
    let key = buf.as_ptr() as HashTableKey;
    assert!(hash_table_lookup(&hash_table, key).is_some());

    hash_table_remove(&mut hash_table, key);

    assert_eq!(hash_table_num_entries(&hash_table), 9999);
    assert!(hash_table_lookup(&hash_table, key).is_none());

    buf.clear();
    buf.push_str("-1");
    let non_existent_key = buf.as_ptr() as HashTableKey;
    hash_table_remove(&mut hash_table, non_existent_key);

    assert_eq!(hash_table_num_entries(&hash_table), 9999);

    hash_table_free(hash_table);
}

pub fn free_key(value: HashTableKey) {
    drop(unsafe { Box::from_raw(value as *mut u32) });
}

#[test]
pub fn test_hash_table_free_functions() {
    let mut hash_table = hash_table_new(int_hash, int_equal).expect("Failed to create hash table");

    hash_table_register_free_functions(&mut hash_table, Some(free_key), Some(free_value));

    ALLOCATED_VALUES.with(|av| av.borrow_mut().count = 0);

    for i in 0..NUM_TEST_VALUES {
        let key = new_key(i).expect("Failed to allocate key");
        let value = new_value(99);

        hash_table_insert(&mut hash_table, Box::into_raw(key) as HashTableKey, value);
    }

    assert_eq!(
        ALLOCATED_KEYS.with(|keys| keys.get()),
        NUM_TEST_VALUES as usize
    );
    assert_eq!(
        ALLOCATED_VALUES.with(|av| av.borrow().count),
        NUM_TEST_VALUES as usize
    );

    let i = NUM_TEST_VALUES / 2;
    hash_table_remove(&mut hash_table, Box::into_raw(Box::new(i)) as HashTableKey);

    assert_eq!(
        ALLOCATED_KEYS.with(|keys| keys.get()),
        (NUM_TEST_VALUES - 1) as usize
    );
    assert_eq!(
        ALLOCATED_VALUES.with(|av| av.borrow().count),
        (NUM_TEST_VALUES - 1) as usize
    );

    let key = new_key(NUM_TEST_VALUES / 3).expect("Failed to allocate key");
    let value = new_value(999);

    assert_eq!(
        ALLOCATED_KEYS.with(|keys| keys.get()),
        NUM_TEST_VALUES as usize
    );
    assert_eq!(
        ALLOCATED_VALUES.with(|av| av.borrow().count),
        NUM_TEST_VALUES as usize
    );

    hash_table_insert(&mut hash_table, Box::into_raw(key) as HashTableKey, value);

    assert_eq!(
        ALLOCATED_KEYS.with(|keys| keys.get()),
        (NUM_TEST_VALUES - 1) as usize
    );
    assert_eq!(
        ALLOCATED_VALUES.with(|av| av.borrow().count),
        (NUM_TEST_VALUES - 1) as usize
    );

    hash_table_free(hash_table);

    assert_eq!(ALLOCATED_KEYS.with(|keys| keys.get()), 0);
    assert_eq!(ALLOCATED_VALUES.with(|av| av.borrow().count), 0);
}

pub fn string_hash(value: HashTableKey) -> u32 {
    let bytes = unsafe {
        std::slice::from_raw_parts(
            value as *const u8,
            std::ffi::CStr::from_ptr(value as *const i8)
                .to_bytes()
                .len(),
        )
    };
    bytes.iter().fold(0, |acc, &x| acc.wrapping_add(x as u32))
}

pub fn string_equal(value1: HashTableKey, value2: HashTableKey) -> i32 {
    let bytes1 = unsafe {
        std::slice::from_raw_parts(
            value1 as *const u8,
            std::ffi::CStr::from_ptr(value1 as *const i8)
                .to_bytes()
                .len(),
        )
    };
    let bytes2 = unsafe {
        std::slice::from_raw_parts(
            value2 as *const u8,
            std::ffi::CStr::from_ptr(value2 as *const i8)
                .to_bytes()
                .len(),
        )
    };
    if bytes1 == bytes2 {
        1
    } else {
        0
    }
}

fn free(_value: HashTableKey) {}

pub fn int_hash(value: HashTableKey) -> u32 {
    unsafe { *(value as *const u32) }
}

pub fn int_equal(value1: HashTableKey, value2: HashTableKey) -> i32 {
    if value1 == value2 {
        1
    } else {
        0
    }
}
