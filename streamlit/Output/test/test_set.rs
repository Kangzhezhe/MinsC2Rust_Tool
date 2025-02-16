use test_project::set::{
    set_allocate_table, set_enlarge, set_free, set_free_entry, set_insert, set_intersection,
    set_iter_has_more, set_iter_next, set_iterate, set_new, set_num_entries, set_query,
    set_register_free_function, set_remove, set_to_array, set_union, Set, SetIterator,
};

const SET_NUM_PRIMES: usize = 24;
const SET_PRIMES: [usize; SET_NUM_PRIMES] = [
    193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317, 196613, 393241, 786433, 1572869,
    3145739, 6291469, 12582917, 25165843, 50331653, 100663319, 201326611, 402653189, 805306457,
    1610612741,
];

static mut ALLOCATED_VALUES: usize = 0;
pub fn generate_set() -> Option<Set<String>> {
    let mut set = match set_new(string_hash, string_equal) {
        Some(s) => s,
        None => return None,
    };

    let mut buf = String::with_capacity(10);
    let mut value: String;

    for i in 0..10000 {
        buf.clear();
        buf.push_str(&i.to_string());
        value = buf.clone();

        set_insert(&mut set, value);

        assert_eq!(set_num_entries(&set), i + 1);
    }

    set_register_free_function(&mut set, Some(|_| {}));

    Some(set)
}

pub fn new_value<T>(value: T) -> Box<T>
where
    T: Clone,
{
    let result = Box::new(value);
    unsafe {
        ALLOCATED_VALUES += 1;
    }
    result
}

#[test]
pub fn test_set_union() {
    let numbers1 = vec![1, 2, 3, 4, 5, 6, 7];
    let numbers2 = vec![5, 6, 7, 8, 9, 10, 11];
    let result = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    let mut set1;
    let mut set2;
    let result_set;

    // Create the first set
    set1 = set_new(int_hash, int_equal).unwrap();

    for number in numbers1.iter() {
        set_insert(&mut set1, *number);
    }

    // Create the second set
    set2 = set_new(int_hash, int_equal).unwrap();

    for number in numbers2.iter() {
        set_insert(&mut set2, *number);
    }

    // Perform the union
    result_set = set_union(&set1, &set2).unwrap();

    assert_eq!(set_num_entries(&result_set), 11);

    for number in result.iter() {
        assert_ne!(set_query(&result_set, *number), 0);
    }

    set_free(&mut result_set.into());

    // Test out of memory scenario
    // Low memory scenarios removed as per requirement

    set_free(&mut set1);
    set_free(&mut set2);
}

#[test]
pub fn test_set_to_array() {
    let mut set = set_new(pointer_hash, pointer_equal).unwrap();
    let mut values = [1; 100];

    for i in 0..100 {
        set_insert(&mut set, values[i]);
    }

    let array = set_to_array(&set);

    // Check the array
    for i in 0..100 {
        assert_eq!(array[i], 1);
        values[i] = 0;
    }

    set_free(&mut set);
}

#[test]
pub fn test_set_out_of_memory() {
    let mut set = match set_new(int_hash, int_equal) {
        Some(s) => s,
        None => return,
    };

    let mut values = [0; 66];

    // Test normal failure
    values[0] = 0;
    assert!(!set_insert(&mut set, values[0]));
    assert_eq!(set_num_entries(&set), 0);

    // Test failure when increasing table size.
    // The initial table size is 193 entries. The table increases in
    // size when 1/3 full, so the 66th entry should cause the insert
    // to fail.

    for i in 0..65 {
        values[i] = i as i32;

        assert!(set_insert(&mut set, values[i]));
        assert_eq!(set_num_entries(&set), i + 1);
    }

    assert_eq!(set_num_entries(&set), 65);

    // Test the 66th insert
    values[65] = 65;

    assert!(!set_insert(&mut set, values[65]));
    assert_eq!(set_num_entries(&set), 65);

    set_free(&mut set);
}

#[test]
pub fn test_set_insert() {
    let mut set = set_new(int_hash, int_equal).expect("Failed to create set");

    let numbers1 = [1, 2, 3, 4, 5, 6];
    let numbers2 = [5, 6, 7, 8, 9, 10];

    for &num in &numbers1 {
        set_insert(&mut set, num);
    }
    for &num in &numbers2 {
        set_insert(&mut set, num);
    }

    assert_eq!(set_num_entries(&set), 10);

    set_free(&mut set);
}

fn free_value(data: i32) {
    unsafe {
        ALLOCATED_VALUES -= 1;
    }
}

#[test]
pub fn test_set_query() {
    let mut set = match generate_set() {
        Some(s) => s,
        None => return,
    };

    let mut buf = String::with_capacity(10);

    /* Test all values */
    for i in 0..10000 {
        buf.clear();
        buf.push_str(&i.to_string());
        assert!(set_query(&set, buf.clone()) != 0);
    }

    /* Test invalid values returning zero */
    assert!(set_query(&set, "-1".to_string()) == 0);
    assert!(set_query(&set, "100001".to_string()) == 0);

    set_free(&mut set);
}

#[test]
pub fn test_set_iterating() {
    let mut set = match generate_set() {
        Some(s) => s,
        None => return,
    };

    let mut iterator = SetIterator {
        set: None,
        next_entry: None,
        next_chain: 0,
    };

    let mut count = 0;
    set_iterate(&set, &mut iterator);

    while set_iter_has_more(&iterator) {
        set_iter_next(&mut iterator);
        count += 1;
    }

    assert!(set_iter_next(&mut iterator).is_none());

    assert_eq!(count, 10000);

    set_free(&mut set);

    let mut set = match set_new(int_hash, int_equal) {
        Some(s) => s,
        None => return,
    };

    let mut iterator = SetIterator {
        set: None,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(&set, &mut iterator);

    assert!(!set_iter_has_more(&iterator));

    set_free(&mut set);
}

#[test]
pub fn test_set_intersection() {
    let numbers1 = vec![1, 2, 3, 4, 5, 6, 7];
    let numbers2 = vec![5, 6, 7, 8, 9, 10, 11];
    let result = vec![5, 6, 7];
    let mut set1: Set<i32>;
    let mut set2: Set<i32>;
    let mut result_set: Option<Set<i32>>;

    // Create the first set
    set1 = set_new(int_hash, int_equal).unwrap();

    for num in numbers1.iter() {
        set_insert(&mut set1, *num);
    }

    // Create the second set
    set2 = set_new(int_hash, int_equal).unwrap();

    for num in numbers2.iter() {
        set_insert(&mut set2, *num);
    }

    // Perform the intersection
    result_set = set_intersection(&set1, &set2);

    assert_eq!(set_num_entries(result_set.as_ref().unwrap()), 3);

    for num in result.iter() {
        assert_ne!(set_query(result_set.as_ref().unwrap(), *num), 0);
    }

    // Clean up
    set_free(&mut set1);
    set_free(&mut set2);
    if let Some(mut rs) = result_set {
        set_free(&mut rs);
    }
}

#[test]
pub fn test_set_new_free() {
    let mut set = match set_new(int_hash, int_equal) {
        Some(s) => s,
        None => panic!("Failed to create set"),
    };

    set_register_free_function(&mut set, Some(free));

    // Fill the set with many values before freeing
    for i in 0..10000 {
        let value = i;
        set_insert(&mut set, value);
    }

    // Free the set
    set_free(&mut set);
}

#[test]
pub fn test_set_remove() {
    let mut set = match generate_set() {
        Some(s) => s,
        None => return,
    };

    let mut num_entries = set_num_entries(&set);
    assert_eq!(num_entries, 10000);

    /* Remove some entries */
    for i in 4000..6000 {
        let buf = i.to_string();

        /* Check this is in the set */
        assert_ne!(set_query(&set, buf.clone()), 0);

        /* Remove it */
        assert!(set_remove(&mut set, buf.clone()));

        /* Check the number of entries decreases */
        assert_eq!(set_num_entries(&set), num_entries - 1);

        /* Check it is no longer in the set */
        assert_eq!(set_query(&set, buf), 0);

        num_entries -= 1;
    }

    /* Try to remove some invalid entries */
    for i in -1000..-500 {
        let buf = i.to_string();

        assert!(!set_remove(&mut set, buf));
        assert_eq!(set_num_entries(&set), num_entries);
    }

    for i in 50000..51000 {
        let buf = i.to_string();

        assert!(!set_remove(&mut set, buf));
        assert_eq!(set_num_entries(&set), num_entries);
    }

    set_free(&mut set);
}

#[test]
pub fn test_set_free_function() {
    let mut set = set_new(int_hash, int_equal).expect("Failed to create set");

    set_register_free_function(&mut set, Some(free_value));

    unsafe {
        ALLOCATED_VALUES = 0;
    }

    for i in 0..1000 {
        let value = new_value(i);

        set_insert(&mut set, *value);
    }

    assert_eq!(unsafe { ALLOCATED_VALUES }, 1000);

    let i = 500;
    set_remove(&mut set, i);

    assert_eq!(unsafe { ALLOCATED_VALUES }, 999);

    set_free(&mut set);

    assert_eq!(unsafe { ALLOCATED_VALUES }, 0);
}

#[test]
pub fn test_set_iterating_remove() {
    let mut set = generate_set().expect("Failed to generate set");
    let mut iterator = SetIterator::<String>::default();
    let mut count = 0;
    let mut removed = 0;

    set_iterate(&set, &mut iterator);

    while set_iter_has_more(&iterator) {
        if let Some(value) = set_iter_next(&mut iterator) {
            if value.parse::<u32>().unwrap() % 100 == 0 {
                set_remove(&mut set, value);
                removed += 1;
            }
            count += 1;
        }
    }

    assert_eq!(count, 10000);
    assert_eq!(removed, 100);
    assert_eq!(set_num_entries(&set), 10000 - removed);

    set_free(&mut set);
}

pub fn pointer_hash(data: &i32) -> usize {
    *data as usize
}

pub fn pointer_equal(a: &i32, b: &i32) -> bool {
    a == b
}

fn free(data: i32) {
    println!("Freeing: {}", data);
}

pub fn int_hash(data: &i32) -> usize {
    *data as usize
}

pub fn int_equal(a: &i32, b: &i32) -> bool {
    a == b
}

pub fn string_hash(s: &String) -> usize {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut hasher = DefaultHasher::new();
    s.hash(&mut hasher);
    hasher.finish() as usize
}

pub fn string_equal(a: &String, b: &String) -> bool {
    a == b
}
