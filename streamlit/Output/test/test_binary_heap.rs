use test_project::binary_heap::{
    BinaryHeapCompareFunc, BinaryHeapType, _BinaryHeap, binary_heap_cmp, binary_heap_free,
    binary_heap_insert, binary_heap_new, binary_heap_num_entries, binary_heap_pop,
};
const NUM_TEST_VALUES: usize = 100;
#[test]
pub fn test_binary_heap_insert() {
    let mut heap = binary_heap_new(BinaryHeapType::Min, int_compare).unwrap();
    let mut test_array = Vec::new();

    for i in 0..NUM_TEST_VALUES {
        test_array.push(i as i32);
        assert!(binary_heap_insert(&mut heap, test_array[i]) != 0);
    }

    assert_eq!(binary_heap_num_entries(&heap), NUM_TEST_VALUES);

    binary_heap_free(heap);
}

#[test]
pub fn test_binary_heap_new_free() {
    let mut heap: Option<_BinaryHeap<i32>>;

    for _ in 0..NUM_TEST_VALUES {
        heap = binary_heap_new(BinaryHeapType::Min, int_compare);
        if let Some(h) = heap {
            binary_heap_free(h);
        }
    }
}

#[test]
pub fn test_out_of_memory() {
    let mut heap = match binary_heap_new(BinaryHeapType::Min, int_compare) {
        Some(h) => h,
        None => panic!("Failed to create binary heap"),
    };

    let values = vec![15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0];

    // Allocate a heap and fill to the default limit
    for i in 0..16 {
        assert!(binary_heap_insert(&mut heap, values[i]) != 0);
    }

    assert!(binary_heap_num_entries(&heap) == 16);

    // Check that we cannot add new values
    for i in 0..16 {
        assert!(binary_heap_insert(&mut heap, values[i]) == 0);
        assert!(binary_heap_num_entries(&heap) == 16);
    }

    // Check that we can read the values back out again and they are in the right order.
    for i in 0..16 {
        let value = binary_heap_pop(&mut heap).expect("Failed to pop from heap");
        assert!(value == i);
    }

    assert!(binary_heap_num_entries(&heap) == 0);

    binary_heap_free(heap);
}

#[test]
pub fn test_max_heap() {
    let mut heap = binary_heap_new(BinaryHeapType::Max, int_compare).unwrap();
    let mut test_array = vec![0; NUM_TEST_VALUES];

    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        assert!(binary_heap_insert(&mut heap, test_array[i]) != 0);
    }

    let mut i = NUM_TEST_VALUES;
    while binary_heap_num_entries(&heap) > 0 {
        let val = binary_heap_pop(&mut heap).unwrap();

        assert!(val == i as i32 - 1);
        i = val as usize;
    }

    binary_heap_free(heap);
}

#[test]
pub fn test_min_heap() {
    let mut test_array = [0; NUM_TEST_VALUES];
    let mut heap =
        binary_heap_new(BinaryHeapType::Min, int_compare).expect("Failed to create heap");

    /* Push a load of values onto the heap */
    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        assert!(binary_heap_insert(&mut heap, test_array[i]) != 0);
    }

    /* Pop values off the heap and check they are in order */
    let mut i = -1;
    while binary_heap_num_entries(&heap) > 0 {
        if let Some(val) = binary_heap_pop(&mut heap) {
            assert!(val == i + 1);
            i = val;
        } else {
            panic!("Unexpected None value from heap pop");
        }
    }

    /* Test popping from an empty heap */
    assert!(binary_heap_num_entries(&heap) == 0);
    assert!(binary_heap_pop(&mut heap).is_none());

    binary_heap_free(heap);
}

pub fn int_compare(a: &i32, b: &i32) -> i32 {
    a.cmp(b) as i32
}
