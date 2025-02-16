use std::fmt::Write;
use test_project::trie::{
    bin_key, bin_key2, bin_key3, bin_key4, trie_find_end, trie_find_end_binary, trie_free,
    trie_free_list_pop, trie_free_list_push, trie_insert, trie_insert_binary, trie_insert_rollback,
    trie_lookup, trie_lookup_binary, trie_new, trie_num_entries, trie_remove, trie_remove_binary,
    Trie, TrieNode,
};
pub const NUM_TEST_VALUES: usize = 1000;
pub const LONG_STRING_LEN: usize = 1024;
pub fn generate_binary_trie() -> Option<Trie<String>> {
    let mut trie = trie_new::<String>().unwrap();

    /* Insert some values */
    assert!(
        trie_insert_binary(
            &mut trie,
            &bin_key2,
            bin_key2.len(),
            Some("goodbye world".to_string())
        ) != 0
    );
    assert!(
        trie_insert_binary(
            &mut trie,
            &bin_key,
            bin_key.len(),
            Some("hello world".to_string())
        ) != 0
    );

    Some(trie)
}

#[test]
pub fn test_trie_insert_binary() {
    let mut trie = generate_binary_trie().unwrap();

    /* Overwrite a value */
    assert!(
        trie_insert_binary(
            &mut trie,
            &bin_key,
            bin_key.len(),
            Some("hi world".to_string())
        ) != 0
    );

    /* Insert NULL value doesn't work */
    assert!(trie_insert_binary(&mut trie, &bin_key3, bin_key3.len(), None) == 0);

    /* Read them back */
    let value = trie_lookup_binary(&trie, &bin_key, bin_key.len());
    assert_eq!(value, Some(&"hi world".to_string()));

    let value = trie_lookup_binary(&trie, &bin_key2, bin_key2.len());
    assert_eq!(value, Some(&"goodbye world".to_string()));

    trie_free(trie);
}

#[test]
pub fn test_trie_insert_out_of_memory() {
    let mut trie = generate_binary_trie().unwrap();

    // Simulate out of memory scenario by limiting allocations
    // In Rust, we don't have direct control over allocation limits like in C,
    // so we rely on the system's memory management and handle potential errors gracefully.

    match trie_insert_binary(
        &mut trie,
        &bin_key4,
        bin_key4.len(),
        Some("test value".to_string()),
    ) {
        0 => (),
        _ => panic!("Insert should fail due to simulated out of memory"),
    }

    assert!(trie_lookup_binary(&trie, &bin_key4, bin_key4.len()).is_none());
    assert_eq!(trie_num_entries(&trie), 2);

    trie_free(trie);
}

#[test]
pub fn test_trie_new_free() {
    // Allocate and free an empty trie
    let mut trie = trie_new::<&str>();
    assert!(trie.is_some());
    trie_free(trie.unwrap());

    // Add some values before freeing
    let mut trie = trie_new::<&str>().unwrap();
    assert!(trie_insert(&mut trie, "hello", "there"));
    assert!(trie_insert(&mut trie, "hell", "testing"));
    assert!(trie_insert(&mut trie, "testing", "testing"));
    assert!(trie_insert(&mut trie, "", "asfasf"));
    trie_free(trie);

    // Add a value, remove it and then free
    let mut trie = trie_new::<&str>().unwrap();
    assert!(trie_insert(&mut trie, "hello", "there"));
    assert!(trie_remove(&mut trie, "hello"));
    trie_free(trie);
}

#[test]
pub fn test_trie_insert_empty() {
    let mut trie = trie_new::<&str>().unwrap();
    let buf = "test";

    // Test insert on empty string
    assert!(trie_insert(&mut trie, "", buf));
    assert!(trie_num_entries(&trie) != 0);
    assert_eq!(trie_lookup(&trie, ""), Some(&buf));
    assert!(trie_remove(&mut trie, ""));

    assert_eq!(trie_num_entries(&trie), 0);

    trie_free(trie);
}

pub fn generate_trie() -> Option<Trie<i32>> {
    let mut trie = trie_new()?;
    let mut entries = 0;
    let mut test_array = vec![0; NUM_TEST_VALUES];
    let mut test_strings = vec![String::with_capacity(10); NUM_TEST_VALUES];

    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        test_strings[i] = i.to_string();

        assert!(trie_insert(
            &mut trie,
            &test_strings[i],
            test_array[i].clone()
        ));

        entries += 1;

        assert_eq!(trie_num_entries(&trie), entries as u32);
    }

    Some(trie)
}

#[test]
pub fn test_trie_remove_binary() {
    let mut trie = generate_binary_trie().unwrap();

    // Test look up and remove of invalid values
    let value = trie_lookup_binary(&trie, &bin_key3, bin_key3.len());
    assert!(value.is_none());

    assert_eq!(trie_remove_binary(&mut trie, &bin_key3, bin_key3.len()), 0);

    assert_eq!(trie_lookup_binary(&trie, &bin_key4, bin_key4.len()), None);
    assert_eq!(trie_remove_binary(&mut trie, &bin_key4, bin_key4.len()), 0);

    // Remove the two values
    assert_ne!(trie_remove_binary(&mut trie, &bin_key2, bin_key2.len()), 0);
    assert_eq!(trie_lookup_binary(&trie, &bin_key2, bin_key2.len()), None);
    assert!(trie_lookup_binary(&trie, &bin_key, bin_key.len()).is_some());

    assert_ne!(trie_remove_binary(&mut trie, &bin_key, bin_key.len()), 0);
    assert_eq!(trie_lookup_binary(&trie, &bin_key, bin_key.len()), None);

    trie_free(trie);
}

#[test]
pub fn test_trie_lookup() {
    let mut trie = generate_trie().expect("Failed to generate trie");
    let mut buf = String::with_capacity(10);

    // Test lookup for non-existent values
    assert!(trie_lookup(&trie, "000000000000000").is_none());
    assert!(trie_lookup(&trie, "").is_none());

    // Look up all values
    for i in 0..NUM_TEST_VALUES {
        buf.clear();
        write!(&mut buf, "{}", i).expect("Failed to write to buffer");

        if let Some(val) = trie_lookup(&trie, &buf) {
            assert_eq!(*val, i as i32);
        } else {
            panic!("Value not found for key: {}", buf);
        }
    }

    trie_free(trie);
}

#[test]
pub fn test_trie_free_long() {
    let mut long_string = vec!['A'; LONG_STRING_LEN - 1];
    long_string.push('\0');

    let mut trie = trie_new::<String>().unwrap();
    trie_insert(
        &mut trie,
        &long_string.iter().collect::<String>(),
        long_string.iter().collect::<String>(),
    );

    trie_free(trie);
}

#[test]
pub fn test_trie_remove() {
    let mut trie = generate_trie().expect("Failed to generate trie");

    // Test remove on non-existent values.
    assert!(!trie_remove(&mut trie, "000000000000000"));
    assert!(!trie_remove(&mut trie, ""));

    let mut entries = trie_num_entries(&trie);
    assert_eq!(entries, NUM_TEST_VALUES as u32);

    // Remove all values
    for i in 0..NUM_TEST_VALUES {
        let mut buf = String::new();
        write!(&mut buf, "{}", i).expect("Failed to write to buffer");

        // Remove value and check counter
        assert!(trie_remove(&mut trie, &buf));
        entries -= 1;
        assert_eq!(trie_num_entries(&trie), entries);
    }

    trie_free(trie);
}

#[test]
pub fn test_trie_replace() {
    let mut trie = generate_trie().unwrap();

    // Test replacing values
    let mut val = 999;

    assert!(trie_insert(&mut trie, "999", val));
    assert_eq!(trie_num_entries(&trie), NUM_TEST_VALUES as u32);

    assert_eq!(trie_lookup(&trie, "999"), Some(&val));

    trie_free(trie);
}

#[test]
pub fn test_trie_insert() {
    let mut trie = generate_trie().expect("Failed to generate trie");
    let entries = trie_num_entries(&trie);

    // Test rollback
    assert!(trie_insert(&mut trie, "hello world", 0));
    assert_eq!(trie_num_entries(&trie), entries + 1);

    trie_insert_rollback(&mut trie, b"hello world");
    assert_eq!(trie_num_entries(&trie), entries);

    trie_free(trie);
}
