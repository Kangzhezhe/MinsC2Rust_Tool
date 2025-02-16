use test_project::compare_int::int_compare;
use test_project::sortedarray::{
    sortedarray_first_index, sortedarray_free, sortedarray_get, sortedarray_index_of,
    sortedarray_insert, sortedarray_last_index, sortedarray_length, sortedarray_new,
    sortedarray_remove, sortedarray_remove_range, SortedArray,
};

pub struct SortedArrayValue;
pub type SortedArrayCompareFunc<T> = fn(&T, &T) -> i32;
pub type SortedArrayEqualFunc<T> = fn(&T, &T) -> bool;

pub struct IntLocation(pub i32);
pub fn generate_sortedarray_equ(
    equ_func: SortedArrayEqualFunc<i32>,
) -> Option<Box<SortedArray<i32>>> {
    const TEST_SIZE: usize = 20;
    let array: [i32; TEST_SIZE] = [
        10, 12, 12, 1, 2, 3, 6, 7, 2, 23, 13, 23, 23, 34, 31, 9, 0, 0, 0, 0,
    ];

    let mut sortedarray = SortedArray::new(0, equ_func, int_compare)?;

    for &value in &array[..TEST_SIZE] {
        let data = value;
        sortedarray_insert(&mut sortedarray, data);
    }

    Some(sortedarray)
}

pub fn generate_sortedarray() -> Option<Box<SortedArray<i32>>> {
    generate_sortedarray_equ(int_equal)
}

pub fn free_sorted_ints(sortedarray: Option<Box<SortedArray<i32>>>) {
    if let Some(sa) = sortedarray {
        for i in 0..sortedarray_length(&sa) {
            if let Some(_value) = sortedarray_get(Some(&sa), i) {}
        }
    }
}

pub fn check_sorted_prop<T>(sortedarray: &SortedArray<T>)
where
    T: std::cmp::Ord,
{
    for i in 1..sortedarray_length(sortedarray) {
        assert!(
            (sortedarray.cmp_func)(
                &sortedarray_get(Some(sortedarray), i - 1).unwrap(),
                &sortedarray_get(Some(sortedarray), i).unwrap()
            ) <= 0
        );
    }
}

#[test]
pub fn test_sortedarray_index_of() {
    let mut sortedarray = generate_sortedarray().expect("Failed to generate sorted array");

    for i in 0..20 {
        let data = sortedarray_get(Some(&sortedarray), i)
            .expect("Failed to get element from sorted array");
        let r = sortedarray_index_of(&sortedarray, data);
        assert!(r >= 0);
        assert_eq!(
            *sortedarray_get(Some(&sortedarray), r as usize)
                .expect("Failed to get element from sorted array"),
            *data
        );
    }

    free_sorted_ints(Some(sortedarray));
}

#[test]
pub fn test_sortedarray_new_free() {
    let mut sortedarray: Option<Box<SortedArray<i32>>> = None;

    /* test normal */
    sortedarray = SortedArray::new(0, int_equal, int_compare);
    assert!(sortedarray.is_some());
    sortedarray_free(sortedarray);

    /* freeing null */
    sortedarray_free::<i32>(None);
}

#[test]
pub fn test_sortedarray_remove() {
    const TEST_REMOVE_EL: usize = 5;
    let mut sortedarray = generate_sortedarray().expect("Failed to create sorted array");

    /* remove index 24 */
    let ip = sortedarray_get(Some(&sortedarray), TEST_REMOVE_EL + 1).expect("Index out of bounds");
    let i = *ip;
    sortedarray_remove(&mut sortedarray, TEST_REMOVE_EL);
    assert_eq!(
        *sortedarray_get(Some(&sortedarray), TEST_REMOVE_EL).expect("Index out of bounds"),
        i
    );

    check_sorted_prop(&sortedarray);
    free_sorted_ints(Some(sortedarray));
}

#[test]
pub fn test_sortedarray_get() {
    let mut i = 0;

    let arr = generate_sortedarray();

    if let Some(array) = arr {
        while i < sortedarray_length(&array) {
            assert_eq!(
                sortedarray_get(Some(&array), i),
                sortedarray_get(Some(&array), i)
            );
            if let Some(value) = sortedarray_get(Some(&array), i) {
                assert_eq!(*value, *value);
            }
            i += 1;
        }
        free_sorted_ints(Some(array));
    }
}

pub fn ptr_equal(a: &i32, b: &i32) -> bool {
    std::ptr::eq(a, b)
}

#[test]
pub fn test_sortedarray_remove_range() {
    const TEST_REMOVE_RANGE: usize = 5;
    const TEST_REMOVE_RANGE_LENGTH: usize = 3;

    let mut sortedarray = generate_sortedarray().expect("Failed to generate sorted array");

    /* get values in test range */
    let mut new = vec![0; TEST_REMOVE_RANGE_LENGTH];
    for i in 0..TEST_REMOVE_RANGE_LENGTH {
        if let Some(value) = sortedarray_get(
            Some(&sortedarray),
            TEST_REMOVE_RANGE + TEST_REMOVE_RANGE_LENGTH + i,
        ) {
            new[i] = *value;
        }
    }

    /* free removed elements */
    for i in 0..TEST_REMOVE_RANGE_LENGTH {
        if let Some(_) = sortedarray_get(Some(&sortedarray), TEST_REMOVE_RANGE + i) {
            // In Rust, we don't need to manually free memory for integers as they are owned and dropped automatically.
        }
    }

    /* remove */
    sortedarray_remove_range(
        &mut sortedarray,
        TEST_REMOVE_RANGE,
        TEST_REMOVE_RANGE_LENGTH,
    );

    /* assert */
    for i in 0..TEST_REMOVE_RANGE_LENGTH {
        if let Some(value) = sortedarray_get(Some(&sortedarray), TEST_REMOVE_RANGE + i) {
            assert_eq!(*value, new[i]);
        }
    }

    check_sorted_prop(&sortedarray);
    free_sorted_ints(Some(sortedarray));
}

#[test]
pub fn test_sortedarray_index_of_equ_key() {
    let sortedarray = generate_sortedarray_equ(ptr_equal).unwrap();
    let mut i = 0;

    while i < 20 {
        let r = sortedarray_index_of(
            &sortedarray,
            sortedarray_get(Some(&sortedarray), i).unwrap(),
        );
        assert!(r >= 0);
        assert_eq!(i, r as usize);
        i += 1;
    }

    sortedarray_free(Some(sortedarray));
}

#[test]
pub fn test_sortedarray_insert() {
    let mut sortedarray = generate_sortedarray().unwrap();

    for _ in 0..20 {
        let i: i32 = 0; // Removed rand dependency
        sortedarray_insert(&mut sortedarray, i);
    }

    check_sorted_prop(&sortedarray);
    free_sorted_ints(Some(sortedarray));
}

pub fn int_equal(a: &i32, b: &i32) -> bool {
    a == b
}
