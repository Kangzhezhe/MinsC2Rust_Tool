use std::cell::RefCell;
use std::rc::Rc;
use test_project::list::{
    list_append, list_data, list_find_data, list_free, list_length, list_next, list_nth_data,
    list_nth_entry, list_prepend, list_prev, list_remove_data, list_remove_entry, list_sort,
    list_sort_internal, list_to_array, variable1, variable2, variable3, variable4, ListEntry,
};
pub fn generate_list() -> Option<Rc<RefCell<ListEntry<&'static i32>>>> {
    let mut list: Option<Rc<RefCell<ListEntry<&'static i32>>>> = None;

    assert!(list_append(&mut list, &variable1).is_some());
    assert!(list_append(&mut list, &variable2).is_some());
    assert!(list_append(&mut list, &variable3).is_some());
    assert!(list_append(&mut list, &variable4).is_some());

    list
}

pub fn check_list_integrity<T: PartialEq + std::fmt::Debug + Clone>(
    list: Option<Rc<RefCell<ListEntry<T>>>>,
) {
    let mut prev: Option<Rc<RefCell<ListEntry<T>>>> = None;
    let mut rover = list;

    while let Some(current) = rover {
        assert_eq!(list_prev(&Some(current.clone())), prev);
        prev = Some(current.clone());
        rover = list_next(Some(current));
    }
}

#[test]
pub fn test_list_next() {
    let mut list = generate_list();
    let mut rover = list.clone();

    assert_eq!(list_data(rover.clone()), Some(&variable1));
    rover = list_next(rover);
    assert_eq!(list_data(rover.clone()), Some(&variable2));
    rover = list_next(rover);
    assert_eq!(list_data(rover.clone()), Some(&variable3));
    rover = list_next(rover);
    assert_eq!(list_data(rover.clone()), Some(&variable4));
    rover = list_next(rover);
    assert_eq!(rover, None);

    list_free(list);
}

#[test]
pub fn test_list_nth_entry() {
    let mut list: Option<Rc<RefCell<ListEntry<&'static i32>>>> = generate_list();
    let mut entry: Option<Rc<RefCell<ListEntry<&'static i32>>>>;

    /* Check all values in the list */
    entry = list_nth_entry(list.clone(), 0);
    assert_eq!(list_data(entry), Some(&variable1));
    entry = list_nth_entry(list.clone(), 1);
    assert_eq!(list_data(entry), Some(&variable2));
    entry = list_nth_entry(list.clone(), 2);
    assert_eq!(list_data(entry), Some(&variable3));
    entry = list_nth_entry(list.clone(), 3);
    assert_eq!(list_data(entry), Some(&variable4));

    /* Check out of range values */
    entry = list_nth_entry(list.clone(), 4);
    assert_eq!(entry, None);
    entry = list_nth_entry(list.clone(), 400);
    assert_eq!(entry, None);

    list_free(list);
}

#[test]
pub fn test_list_remove_entry() {
    let mut empty_list: Option<Rc<RefCell<ListEntry<&'static i32>>>> = None;
    let mut list = generate_list();
    let mut entry;

    // Remove the third entry
    entry = list_nth_entry(list.clone(), 2).unwrap();
    assert!(list_remove_entry(&mut list, &entry) != 0);
    assert!(list_length(list.clone()) == 3);
    check_list_integrity(list.clone());

    // Remove the first entry
    entry = list_nth_entry(list.clone(), 0).unwrap();
    assert!(list_remove_entry(&mut list, &entry) != 0);
    assert!(list_length(list.clone()) == 2);
    check_list_integrity(list.clone());

    // Try some invalid removes

    // NULL
    assert!(
        list_remove_entry(
            &mut list,
            &Rc::new(RefCell::new(ListEntry {
                data: &0,
                prev: None,
                next: None
            }))
        ) == 0
    );

    // Removing NULL from an empty list
    assert!(
        list_remove_entry(
            &mut empty_list,
            &Rc::new(RefCell::new(ListEntry {
                data: &0,
                prev: None,
                next: None
            }))
        ) == 0
    );

    list_free(list);

    // Test removing an entry when it is the only entry.
    list = None;
    assert!(list_append(&mut list, &variable1).is_some());
    assert!(list.is_some());
    let only_entry = list.clone().unwrap();
    assert!(list_remove_entry(&mut list, &only_entry) != 0);
    assert!(list.is_none());

    // Test removing the last entry
    list = generate_list();
    entry = list_nth_entry(list.clone(), 3).unwrap();
    assert!(list_remove_entry(&mut list, &entry) != 0);
    check_list_integrity(list.clone());
    list_free(list);
}

#[test]
pub fn test_list_remove_data() {
    let entries = vec![89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let mut list: Option<Rc<RefCell<ListEntry<i32>>>> = None;

    for entry in entries.iter().rev() {
        assert!(list_prepend(&mut list, *entry).is_some());
    }

    let mut val = 0;
    assert_eq!(list_remove_data(&mut list, int_equal, &val), 0);
    val = 56;
    assert_eq!(list_remove_data(&mut list, int_equal, &val), 0);
    check_list_integrity(list.clone());

    val = 8;
    assert_eq!(list_remove_data(&mut list, int_equal, &val), 1);
    assert_eq!(list_length(list.clone()), entries.len() - 1);
    check_list_integrity(list.clone());

    val = 4;
    assert_eq!(list_remove_data(&mut list, int_equal, &val), 4);
    assert_eq!(list_length(list.clone()), entries.len() - 5);
    check_list_integrity(list.clone());

    val = 89;
    assert_eq!(list_remove_data(&mut list, int_equal, &val), 1);
    assert_eq!(list_length(list.clone()), entries.len() - 6);
    check_list_integrity(list.clone());

    list_free(list);
}

#[test]
pub fn test_list_length() {
    let mut list: Option<Rc<RefCell<ListEntry<&'static i32>>>> = generate_list();

    assert!(list_length(list.clone()) == 4);

    assert!(list_prepend(&mut list, &variable1).is_some());

    assert!(list_length(list.clone()) == 5);

    list_free(list);

    assert!(list_length::<&'static i32>(None) == 0);
}

#[test]
pub fn test_list_free() {
    let mut list = generate_list();

    list_free(list);

    /* Check the empty list frees correctly */
    list_free::<&'static i32>(None);
}

#[test]
pub fn test_list_prepend() {
    let mut list: Option<Rc<RefCell<ListEntry<&'static i32>>>> = None;

    assert!(list_prepend(&mut list, &variable1).is_some());
    check_list_integrity(list.clone());
    assert!(list_prepend(&mut list, &variable2).is_some());
    check_list_integrity(list.clone());
    assert!(list_prepend(&mut list, &variable3).is_some());
    check_list_integrity(list.clone());
    assert!(list_prepend(&mut list, &variable4).is_some());
    check_list_integrity(list.clone());

    assert_eq!(list_nth_data(list.clone(), 0), Some(&variable4));
    assert_eq!(list_nth_data(list.clone(), 1), Some(&variable3));
    assert_eq!(list_nth_data(list.clone(), 2), Some(&variable2));
    assert_eq!(list_nth_data(list.clone(), 3), Some(&variable1));

    list_free(list);
}

#[test]
pub fn test_list_sort() {
    let mut list: Option<Rc<RefCell<ListEntry<i32>>>> = None;
    let entries = vec![89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let sorted = vec![4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    for i in 0..num_entries {
        assert!(list_prepend(&mut list, entries[i]).is_some());
    }

    list_sort(&mut list, Some(int_compare));

    assert_eq!(list_length(list.clone()), num_entries);

    for i in 0..num_entries {
        let value = list_nth_data(list.clone(), i).unwrap();
        assert_eq!(value, sorted[i]);
    }

    list_free(list);

    list = None;

    list_sort(&mut list, Some(int_compare));

    assert!(list.is_none());
}

#[test]
pub fn test_list_find_data() {
    let entries = vec![89, 23, 42, 16, 15, 4, 8, 99, 50, 30];
    let mut list: Option<Rc<RefCell<ListEntry<i32>>>> = None;

    for entry in entries.iter() {
        assert!(list_append(&mut list, *entry).is_some());
    }

    for entry in entries.iter() {
        let result = list_find_data(&list, int_equal, entry);
        assert!(result.is_some());

        let data = list_data(result);
        assert_eq!(data, Some(*entry));
    }

    let val = 0;
    assert!(list_find_data(&list, int_equal, &val).is_none());
    let val = 56;
    assert!(list_find_data(&list, int_equal, &val).is_none());

    list_free(list);
}

#[test]
pub fn test_list_append() {
    let mut list: Option<Rc<RefCell<ListEntry<&i32>>>> = None;

    assert!(list_append(&mut list, &variable1).is_some());
    check_list_integrity(list.clone());
    assert!(list_append(&mut list, &variable2).is_some());
    check_list_integrity(list.clone());
    assert!(list_append(&mut list, &variable3).is_some());
    check_list_integrity(list.clone());
    assert!(list_append(&mut list, &variable4).is_some());
    check_list_integrity(list.clone());

    assert_eq!(list_length(list.clone()), 4);

    assert_eq!(list_nth_data(list.clone(), 0), Some(&variable1));
    assert_eq!(list_nth_data(list.clone(), 1), Some(&variable2));
    assert_eq!(list_nth_data(list.clone(), 2), Some(&variable3));
    assert_eq!(list_nth_data(list.clone(), 3), Some(&variable4));

    list_free(list);
}

#[test]
pub fn test_list_nth_data() {
    let mut list = generate_list();

    /* Check all values in the list */
    assert_eq!(list_nth_data(list.clone(), 0), Some(&variable1));
    assert_eq!(list_nth_data(list.clone(), 1), Some(&variable2));
    assert_eq!(list_nth_data(list.clone(), 2), Some(&variable3));
    assert_eq!(list_nth_data(list.clone(), 3), Some(&variable4));

    /* Check out of range values */
    assert_eq!(list_nth_data(list.clone(), 4), None);
    assert_eq!(list_nth_data(list.clone(), 400), None);

    list_free(list);
}

#[test]
pub fn test_list_to_array() {
    let mut list = generate_list();

    let array = list_to_array(list.clone());

    assert_eq!(array.as_ref().unwrap()[0], &variable1);
    assert_eq!(array.as_ref().unwrap()[1], &variable2);
    assert_eq!(array.as_ref().unwrap()[2], &variable3);
    assert_eq!(array.as_ref().unwrap()[3], &variable4);

    list_free(list);
}

pub fn int_compare(a: &i32, b: &i32) -> i32 {
    a.cmp(b) as i32
}

pub fn int_equal(a: &i32, b: &i32) -> bool {
    a == b
}
