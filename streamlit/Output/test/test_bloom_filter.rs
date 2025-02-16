use test_project::bloom_filter::{
    bloom_filter_free, bloom_filter_insert, bloom_filter_intersection, bloom_filter_load,
    bloom_filter_new, bloom_filter_query, bloom_filter_read, bloom_filter_union, BloomFilter,
    SALTS,
};
#[test]
pub fn test_bloom_filter_insert_query() {
    let mut filter = bloom_filter_new(128, string_hash, 4).unwrap();

    /* Check values are not present at the start */
    assert!(bloom_filter_query(&filter, "test 1") == 0);
    assert!(bloom_filter_query(&filter, "test 2") == 0);

    /* Insert some values */
    bloom_filter_insert(&mut filter, "test 1");
    bloom_filter_insert(&mut filter, "test 2");

    /* Check they are set */
    assert!(bloom_filter_query(&filter, "test 1") != 0);
    assert!(bloom_filter_query(&filter, "test 2") != 0);

    bloom_filter_free(&mut filter);
}

#[test]
pub fn test_bloom_filter_read_load() {
    let mut state = [0u8; 16];

    // Create a filter with some values set
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_insert(&mut filter1, "test 1");
    bloom_filter_insert(&mut filter1, "test 2");

    // Read the current state into an array
    bloom_filter_read(&filter1, &mut state);

    bloom_filter_free(&mut filter1);

    // Create a new filter and load the state
    let mut filter2 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_load(&mut filter2, &state);

    // Check the values are set in the new filter
    assert!(bloom_filter_query(&filter2, "test 1") != 0);
    assert!(bloom_filter_query(&filter2, "test 2") != 0);

    bloom_filter_free(&mut filter2);
}

#[test]
pub fn test_bloom_filter_new_free() {
    let mut filter: Option<BloomFilter<&str>>;

    /* One salt */
    filter = bloom_filter_new(128, string_hash, 1);
    assert!(filter.is_some());
    bloom_filter_free(filter.as_mut().unwrap());

    /* Maximum number of salts */
    filter = bloom_filter_new(128, string_hash, 64);
    assert!(filter.is_some());
    bloom_filter_free(filter.as_mut().unwrap());

    /* Test creation with too many salts */
    filter = bloom_filter_new(128, string_hash, 50000);
    assert!(filter.is_none());
}

#[test]
pub fn test_bloom_filter_union() {
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_insert(&mut filter1, "test 1");

    let mut filter2 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_insert(&mut filter2, "test 2");

    let mut result = bloom_filter_union(&filter1, &filter2).unwrap();

    assert!(bloom_filter_query(&result, "test 1") != 0);
    assert!(bloom_filter_query(&result, "test 2") != 0);

    bloom_filter_free(&mut result);

    bloom_filter_free(&mut filter1);
    bloom_filter_free(&mut filter2);
}

#[test]
pub fn test_bloom_filter_mismatch() {
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();

    // Different buffer size.
    let mut filter2 = bloom_filter_new(64, string_hash, 4).unwrap();
    assert!(bloom_filter_intersection(&filter1, &filter2).is_none());
    assert!(bloom_filter_union(&filter1, &filter2).is_none());
    bloom_filter_free(&mut filter2);

    // Different hash function
    let mut filter2 = bloom_filter_new(128, string_nocase_hash, 4).unwrap();
    assert!(bloom_filter_intersection(&filter1, &filter2).is_none());
    assert!(bloom_filter_union(&filter1, &filter2).is_none());
    bloom_filter_free(&mut filter2);

    // Different number of salts
    let mut filter2 = bloom_filter_new(128, string_hash, 32).unwrap();
    assert!(bloom_filter_intersection(&filter1, &filter2).is_none());
    assert!(bloom_filter_union(&filter1, &filter2).is_none());
    bloom_filter_free(&mut filter2);

    bloom_filter_free(&mut filter1);
}

#[test]
pub fn test_bloom_filter_intersection() {
    let mut filter1 = bloom_filter_new(128, string_hash, 4).unwrap();
    let mut filter2 = bloom_filter_new(128, string_hash, 4).unwrap();

    bloom_filter_insert(&mut filter1, "test 1");
    bloom_filter_insert(&mut filter1, "test 2");

    bloom_filter_insert(&mut filter2, "test 1");

    assert_eq!(bloom_filter_query(&filter2, "test 2"), 0);

    let result = bloom_filter_intersection(&filter1, &filter2).unwrap();

    assert_ne!(bloom_filter_query(&result, "test 1"), 0);
    assert_eq!(bloom_filter_query(&result, "test 2"), 0);

    let mut result = result; // Make result mutable
    bloom_filter_free(&mut result);
    bloom_filter_free(&mut filter1);
    bloom_filter_free(&mut filter2);
}

pub fn string_nocase_hash(data: &str) -> u32 {
    // Example hash function implementation that ignores case
    data.to_lowercase()
        .chars()
        .fold(0, |acc, c| acc.wrapping_add(c as u32))
}

pub fn string_hash(data: &str) -> u32 {
    let mut hash: u32 = 0;
    for c in data.chars() {
        hash = hash.wrapping_mul(31).wrapping_add(c as u32);
    }
    hash
}
