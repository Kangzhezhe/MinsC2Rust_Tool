use std::cell::RefCell;
use std::rc::Rc;
use test_project::binomial_heap::{
    binomial_heap_cmp, binomial_heap_free, binomial_heap_insert, binomial_heap_merge,
    binomial_heap_merge_undo, binomial_heap_new, binomial_heap_num_entries, binomial_heap_pop,
    binomial_tree_merge, binomial_tree_ref, binomial_tree_unref, BinomialHeap,
    BinomialHeapCompareFunc, BinomialHeapType, BinomialHeapValue, BinomialTree,
    BINOMIAL_HEAP_TYPE_MAX, BINOMIAL_HEAP_TYPE_MIN, NUM_TEST_VALUES, TEST_VALUE,
};
#[test]
pub fn test_binomial_heap_new_free() {
    let mut heap: Option<BinomialHeap>;
    let int_compare = Rc::new(|a: BinomialHeapValue, b: BinomialHeapValue| a.0.cmp(&b.0) as i32);

    for _ in 0..NUM_TEST_VALUES {
        heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, int_compare.clone());
        if let Some(h) = heap {
            binomial_heap_free(h);
        }
    }
}

pub fn verify_heap(heap: &mut BinomialHeap) {
    let mut num_vals = binomial_heap_num_entries(heap);
    assert_eq!(num_vals, NUM_TEST_VALUES as u32 - 1);

    for i in 0..NUM_TEST_VALUES {
        if i == TEST_VALUE {
            continue;
        }

        let val = binomial_heap_pop(heap);
        assert_eq!(val.0, i as i32);

        num_vals -= 1;
        assert_eq!(binomial_heap_num_entries(heap), num_vals);
    }
}

pub fn generate_heap() -> Option<BinomialHeap> {
    let mut test_array = [0; NUM_TEST_VALUES];
    let mut heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, Rc::new(int_compare));

    /* Push a load of values onto the heap */
    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        if i != TEST_VALUE {
            assert!(
                binomial_heap_insert(
                    &mut heap.as_mut().unwrap(),
                    BinomialHeapValue(test_array[i])
                ) != 0
            );
        }
    }

    heap
}

#[test]
pub fn test_pop_out_of_memory() {
    let mut heap: Option<BinomialHeap>;
    let mut i: i32 = 0;

    while i < 6 {
        heap = generate_heap();
        // Pop should fail
        // alloc_test_set_limit(i); // Removed as per requirement
        assert_eq!(
            binomial_heap_pop(&mut heap.as_mut().unwrap()),
            BinomialHeapValue(0)
        );
        // alloc_test_set_limit(-1); // Removed as per requirement

        // Check the heap is unharmed
        binomial_heap_free(heap.unwrap());

        i += 1;
    }
}

#[test]
pub fn test_binomial_heap_insert() {
    let mut heap = binomial_heap_new(
        BINOMIAL_HEAP_TYPE_MIN,
        Rc::new(|value1: BinomialHeapValue, value2: BinomialHeapValue| {
            value1.0.cmp(&value2.0) as i32
        }),
    )
    .unwrap();
    let mut test_array = vec![0; NUM_TEST_VALUES];

    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        assert!(binomial_heap_insert(&mut heap, BinomialHeapValue(test_array[i])) != 0);
    }
    assert!(binomial_heap_num_entries(&heap) == NUM_TEST_VALUES as u32);

    binomial_heap_free(heap);
}

#[test]
pub fn test_min_heap() {
    let mut heap = binomial_heap_new(BINOMIAL_HEAP_TYPE_MIN, Rc::new(int_compare)).unwrap();
    let mut val: BinomialHeapValue;
    let mut test_array = vec![0; NUM_TEST_VALUES];

    /* Push a load of values onto the heap */
    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        assert!(binomial_heap_insert(&mut heap, BinomialHeapValue(test_array[i])) != 0);
    }

    /* Pop values off the heap and check they are in order */
    let mut i = -1;
    while binomial_heap_num_entries(&heap) > 0 {
        val = binomial_heap_pop(&mut heap);

        assert_eq!(val.0, i + 1);
        i = val.0;
    }

    /* Test pop on an empty heap */
    val = binomial_heap_pop(&mut heap);
    assert_eq!(val.0, 0);

    binomial_heap_free(heap);
}

#[test]
pub fn test_insert_out_of_memory() {
    let mut heap: Option<BinomialHeap>;
    let mut i = 0;

    while i < 6 {
        heap = generate_heap();

        // Insert should fail
        let mut test_array = [0; NUM_TEST_VALUES];
        test_array[TEST_VALUE] = TEST_VALUE as i32;
        assert!(
            binomial_heap_insert(
                heap.as_mut().unwrap(),
                BinomialHeapValue(test_array[TEST_VALUE])
            ) == 0
        );

        // Check that the heap is unharmed
        verify_heap(heap.as_mut().unwrap());

        binomial_heap_free(heap.unwrap());
        i += 1;
    }
}

#[test]
pub fn test_max_heap() {
    let mut heap = binomial_heap_new(
        BINOMIAL_HEAP_TYPE_MAX,
        Rc::new(|value1: BinomialHeapValue, value2: BinomialHeapValue| {
            value2.0.cmp(&value1.0) as i32
        }),
    )
    .unwrap();
    let mut test_array = vec![0; NUM_TEST_VALUES];

    /* Push a load of values onto the heap */
    for i in 0..NUM_TEST_VALUES {
        test_array[i] = i as i32;
        assert!(binomial_heap_insert(&mut heap, BinomialHeapValue(test_array[i])) != 0);
    }

    /* Pop values off the heap and check they are in order */
    let mut i = NUM_TEST_VALUES as i32;
    while binomial_heap_num_entries(&heap) > 0 {
        let val = binomial_heap_pop(&mut heap);

        assert_eq!(val.0, i - 1);
        i = val.0 + 1;
    }

    /* Test pop on an empty heap */
    let val = binomial_heap_pop(&mut heap);
    assert_eq!(val, BinomialHeapValue(0));

    binomial_heap_free(heap);
}

pub fn int_compare(a: BinomialHeapValue, b: BinomialHeapValue) -> i32 {
    a.0.cmp(&b.0) as i32
}
