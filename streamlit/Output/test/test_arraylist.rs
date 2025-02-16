use test_project::arraylist::{
    arraylist_append, arraylist_clear, arraylist_enlarge, arraylist_free, arraylist_index_of,
    arraylist_insert, arraylist_new, arraylist_prepend, arraylist_remove, arraylist_remove_range,
    arraylist_sort, arraylist_sort_internal,
};
pub use test_project::arraylist::{ArrayList, ArrayListComparable, CustomInt};
pub fn generate_arraylist() -> Option<ArrayList<CustomInt>> {
    let mut arraylist = match arraylist_new(0) {
        Some(list) => list,
        None => return None,
    };

    let variable1 = CustomInt(1);
    let variable2 = CustomInt(2);
    let variable3 = CustomInt(3);
    let variable4 = CustomInt(4);

    for _ in 0..4 {
        arraylist_append(&mut arraylist, variable1.clone());
        arraylist_append(&mut arraylist, variable2.clone());
        arraylist_append(&mut arraylist, variable3.clone());
        arraylist_append(&mut arraylist, variable4.clone());
    }

    Some(arraylist)
}

#[test]
pub fn test_arraylist_remove_range() {
    let mut arraylist = match generate_arraylist() {
        Some(list) => list,
        None => return,
    };

    let variable4 = CustomInt(4);
    let variable1 = CustomInt(1);
    let variable2 = CustomInt(2);
    let variable3 = CustomInt(3);

    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist.data[3], variable4);
    assert_eq!(arraylist.data[4], variable1);
    assert_eq!(arraylist.data[5], variable2);
    assert_eq!(arraylist.data[6], variable3);

    arraylist_remove_range(&mut arraylist, 4, 3);

    assert_eq!(arraylist.length, 13);
    assert_eq!(arraylist.data[3], variable4);
    assert_eq!(arraylist.data[4], variable4);
    assert_eq!(arraylist.data[5], variable1);
    assert_eq!(arraylist.data[6], variable2);

    /* Try some invalid ones and check they don't do anything */

    arraylist_remove_range(&mut arraylist, 10, 10);
    arraylist_remove_range(&mut arraylist, 0, 16);

    assert_eq!(arraylist.length, 13);

    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_insert() {
    let mut arraylist = match generate_arraylist() {
        Some(list) => list,
        None => return,
    };

    // Check for out of range insert
    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist_insert(&mut arraylist, 17, CustomInt(1)), 0);
    assert_eq!(arraylist.length, 16);

    // Insert a new entry at index 5
    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist.data[4], CustomInt(1));
    assert_eq!(arraylist.data[5], CustomInt(2));
    assert_eq!(arraylist.data[6], CustomInt(3));

    assert_ne!(arraylist_insert(&mut arraylist, 5, CustomInt(4)), 0);

    assert_eq!(arraylist.length, 17);
    assert_eq!(arraylist.data[4], CustomInt(1));
    assert_eq!(arraylist.data[5], CustomInt(4));
    assert_eq!(arraylist.data[6], CustomInt(2));
    assert_eq!(arraylist.data[7], CustomInt(3));

    // Inserting at the start
    assert_eq!(arraylist.data[0], CustomInt(1));
    assert_eq!(arraylist.data[1], CustomInt(2));
    assert_eq!(arraylist.data[2], CustomInt(3));

    assert_ne!(arraylist_insert(&mut arraylist, 0, CustomInt(4)), 0);

    assert_eq!(arraylist.length, 18);
    assert_eq!(arraylist.data[0], CustomInt(4));
    assert_eq!(arraylist.data[1], CustomInt(1));
    assert_eq!(arraylist.data[2], CustomInt(2));
    assert_eq!(arraylist.data[3], CustomInt(3));

    // Inserting at the end
    assert_eq!(arraylist.data[15], CustomInt(2));
    assert_eq!(arraylist.data[16], CustomInt(3));
    assert_eq!(arraylist.data[17], CustomInt(4));

    assert_ne!(arraylist_insert(&mut arraylist, 18, CustomInt(1)), 0);

    assert_eq!(arraylist.length, 19);
    assert_eq!(arraylist.data[15], CustomInt(2));
    assert_eq!(arraylist.data[16], CustomInt(3));
    assert_eq!(arraylist.data[17], CustomInt(4));
    assert_eq!(arraylist.data[18], CustomInt(1));

    // Test inserting many entries
    for _ in 0..10000 {
        arraylist_insert(&mut arraylist, 10, CustomInt(1));
    }

    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_prepend() {
    let mut arraylist = arraylist_new::<CustomInt>(0).unwrap();

    assert!(arraylist.length == 0);

    /* Append some entries */
    assert!(arraylist_prepend(&mut arraylist, CustomInt(1)) != 0);
    assert!(arraylist.length == 1);

    assert!(arraylist_prepend(&mut arraylist, CustomInt(2)) != 0);
    assert!(arraylist.length == 2);

    assert!(arraylist_prepend(&mut arraylist, CustomInt(3)) != 0);
    assert!(arraylist.length == 3);

    assert!(arraylist_prepend(&mut arraylist, CustomInt(4)) != 0);
    assert!(arraylist.length == 4);

    assert!(arraylist.data[0] == CustomInt(4));
    assert!(arraylist.data[1] == CustomInt(3));
    assert!(arraylist.data[2] == CustomInt(2));
    assert!(arraylist.data[3] == CustomInt(1));

    /* Test prepending many entries */
    for _ in 0..10000 {
        assert!(arraylist_prepend(&mut arraylist, CustomInt(0)) != 0);
    }

    arraylist_free(Some(Box::new(arraylist)));

    /* Test low memory scenario is removed */
}

#[test]
pub fn test_arraylist_remove() {
    let mut arraylist = match generate_arraylist() {
        Some(list) => list,
        None => return,
    };

    assert_eq!(arraylist.length, 16);
    assert_eq!(arraylist.data[3], CustomInt(4));
    assert_eq!(arraylist.data[4], CustomInt(1));
    assert_eq!(arraylist.data[5], CustomInt(2));
    assert_eq!(arraylist.data[6], CustomInt(3));

    arraylist_remove(&mut arraylist, 4);

    assert_eq!(arraylist.length, 15);
    assert_eq!(arraylist.data[3], CustomInt(4));
    assert_eq!(arraylist.data[4], CustomInt(2));
    assert_eq!(arraylist.data[5], CustomInt(3));
    assert_eq!(arraylist.data[6], CustomInt(4));

    /* Try some invalid removes */
    arraylist_remove(&mut arraylist, 15);

    assert_eq!(arraylist.length, 15);

    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_sort() {
    let mut arraylist = arraylist_new::<CustomInt>(10).unwrap();
    let entries = vec![
        CustomInt(89),
        CustomInt(4),
        CustomInt(23),
        CustomInt(42),
        CustomInt(4),
        CustomInt(16),
        CustomInt(15),
        CustomInt(4),
        CustomInt(8),
        CustomInt(99),
        CustomInt(50),
        CustomInt(30),
        CustomInt(4),
    ];
    let sorted = vec![
        CustomInt(4),
        CustomInt(4),
        CustomInt(4),
        CustomInt(4),
        CustomInt(8),
        CustomInt(15),
        CustomInt(16),
        CustomInt(23),
        CustomInt(30),
        CustomInt(42),
        CustomInt(50),
        CustomInt(89),
        CustomInt(99),
    ];

    for entry in entries.iter().cloned() {
        arraylist_prepend(&mut arraylist, entry);
    }

    arraylist_sort(&mut arraylist, CustomInt::compare);

    assert_eq!(arraylist.length, sorted.len());

    for (i, value) in arraylist.data.iter().enumerate() {
        assert_eq!(*value, sorted[i]);
    }

    arraylist_free(Some(Box::new(arraylist)));

    let mut arraylist = arraylist_new::<CustomInt>(5).unwrap();
    arraylist_sort(&mut arraylist, CustomInt::compare);
    assert_eq!(arraylist.length, 0);
    arraylist_free(Some(Box::new(arraylist)));

    let mut arraylist = arraylist_new::<CustomInt>(5).unwrap();
    arraylist_prepend(&mut arraylist, entries[0].clone());
    arraylist_sort(&mut arraylist, CustomInt::compare);
    assert_eq!(arraylist.length, 1);
    assert_eq!(arraylist.data[0], entries[0]);
    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_index_of() {
    let entries = vec![
        CustomInt(89),
        CustomInt(4),
        CustomInt(23),
        CustomInt(42),
        CustomInt(16),
        CustomInt(15),
        CustomInt(8),
        CustomInt(99),
        CustomInt(50),
        CustomInt(30),
    ];
    let mut arraylist = arraylist_new(0).unwrap();

    for entry in entries.iter().cloned() {
        arraylist_append(&mut arraylist, entry);
    }

    for (i, entry) in entries.iter().enumerate() {
        let index = arraylist_index_of(&arraylist, |a: &CustomInt, b: &CustomInt| a == b, entry);
        assert!(index == i as i32);
    }

    let val = CustomInt(0);
    assert!(arraylist_index_of(&arraylist, |a: &CustomInt, b: &CustomInt| a == b, &val) < 0);
    let val = CustomInt(57);
    assert!(arraylist_index_of(&arraylist, |a: &CustomInt, b: &CustomInt| a == b, &val) < 0);

    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_clear() {
    let mut arraylist = arraylist_new(0).unwrap();

    /* Emptying an already-empty arraylist */
    arraylist_clear(&mut arraylist);
    assert!(arraylist.length == 0);

    /* Add some items and then empty it */
    let variable1 = CustomInt(1);
    let variable2 = CustomInt(2);
    let variable3 = CustomInt(3);
    let variable4 = CustomInt(4);

    arraylist_append(&mut arraylist, variable1.clone());
    arraylist_append(&mut arraylist, variable2.clone());
    arraylist_append(&mut arraylist, variable3.clone());
    arraylist_append(&mut arraylist, variable4.clone());

    arraylist_clear(&mut arraylist);
    assert!(arraylist.length == 0);

    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_append() {
    let mut arraylist = arraylist_new::<CustomInt>(0).unwrap();

    assert_eq!(arraylist.length, 0);

    // Append some entries
    assert_ne!(arraylist_append(&mut arraylist, CustomInt(1)), 0);
    assert_eq!(arraylist.length, 1);

    assert_ne!(arraylist_append(&mut arraylist, CustomInt(2)), 0);
    assert_eq!(arraylist.length, 2);

    assert_ne!(arraylist_append(&mut arraylist, CustomInt(3)), 0);
    assert_eq!(arraylist.length, 3);

    assert_ne!(arraylist_append(&mut arraylist, CustomInt(4)), 0);
    assert_eq!(arraylist.length, 4);

    assert_eq!(arraylist.data[0], CustomInt(1));
    assert_eq!(arraylist.data[1], CustomInt(2));
    assert_eq!(arraylist.data[2], CustomInt(3));
    assert_eq!(arraylist.data[3], CustomInt(4));

    // Test appending many entries
    for _ in 0..10000 {
        assert_ne!(arraylist_append(&mut arraylist, CustomInt(0)), 0);
    }

    arraylist_free(Some(Box::new(arraylist)));
}

#[test]
pub fn test_arraylist_new_free() {
    let mut arraylist: Option<Box<ArrayList<CustomInt>>> = None;

    /* Use a default size when given zero */
    arraylist = arraylist_new(0).map(|al| Box::new(al));
    assert!(arraylist.is_some());
    arraylist_free(arraylist);

    /* Normal allocated */
    arraylist = arraylist_new(10).map(|al| Box::new(al));
    assert!(arraylist.is_some());
    arraylist_free(arraylist);

    /* Freeing a null arraylist works */
    let none_arraylist: Option<Box<ArrayList<CustomInt>>> = None;
    arraylist_free(none_arraylist);
}
