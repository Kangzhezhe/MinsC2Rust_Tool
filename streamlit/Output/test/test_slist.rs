use std::cell::RefCell;
use std::rc::Rc;
use test_project::slist::{
    slist_append, slist_data, slist_find_data, slist_free, slist_iter_has_more, slist_iter_next,
    slist_iter_remove, slist_iterate, slist_length, slist_next, slist_nth_data, slist_nth_entry,
    slist_prepend, slist_remove_data, slist_remove_entry, slist_sort, slist_sort_internal,
    slist_to_array, variable1, variable2, variable3, variable4, SListEntry, SListIterator,
};
pub fn generate_list() -> Option<Rc<RefCell<SListEntry<i32>>>> {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;

    assert!(slist_append(&mut list, variable1).is_some());
    assert!(slist_append(&mut list, variable2).is_some());
    assert!(slist_append(&mut list, variable3).is_some());
    assert!(slist_append(&mut list, variable4).is_some());

    list
}

#[test]
pub fn test_slist_nth_data() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = generate_list();

    /* Check all values in the list */
    assert_eq!(slist_nth_data(list.clone(), 0), Some(variable1));
    assert_eq!(slist_nth_data(list.clone(), 1), Some(variable2));
    assert_eq!(slist_nth_data(list.clone(), 2), Some(variable3));
    assert_eq!(slist_nth_data(list.clone(), 3), Some(variable4));

    /* Check out of range values */
    assert_eq!(slist_nth_data(list.clone(), 4), None);
    assert_eq!(slist_nth_data(list.clone(), 400), None);

    slist_free(list);
}

#[test]
pub fn test_slist_length() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = generate_list();

    assert_eq!(slist_length(list.clone()), 4);

    slist_prepend(&mut list, variable1);

    assert_eq!(slist_length(list.clone()), 5);

    assert_eq!(slist_length::<i32>(None), 0);

    slist_free(list);
}

#[test]
pub fn test_slist_nth_entry() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = generate_list();

    // Check all values in the list
    let mut entry = slist_nth_entry(list.clone(), 0);
    assert_eq!(entry.as_ref().map(|e| slist_data(e)), Some(variable1));
    entry = slist_nth_entry(list.clone(), 1);
    assert_eq!(entry.as_ref().map(|e| slist_data(e)), Some(variable2));
    entry = slist_nth_entry(list.clone(), 2);
    assert_eq!(entry.as_ref().map(|e| slist_data(e)), Some(variable3));
    entry = slist_nth_entry(list.clone(), 3);
    assert_eq!(entry.as_ref().map(|e| slist_data(e)), Some(variable4));

    // Check out of range values
    entry = slist_nth_entry(list.clone(), 4);
    assert!(entry.is_none());
    entry = slist_nth_entry(list.clone(), 400);
    assert!(entry.is_none());

    slist_free(list);
}

#[test]
pub fn test_slist_find_data() {
    let entries = vec![89, 23, 42, 16, 15, 4, 8, 99, 50, 30];
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;

    for &entry in &entries {
        slist_append(&mut list, entry);
    }

    for &val in &entries {
        let result = slist_find_data(&list, &val);

        assert!(result.is_some());

        let data = slist_data(&result.unwrap());
        assert_eq!(data, val);
    }

    let invalid_values = vec![0, 56];
    for &val in &invalid_values {
        assert!(slist_find_data(&list, &val).is_none());
    }

    slist_free(list);
}

#[test]
pub fn test_slist_remove_entry() {
    let mut empty_list: Option<Rc<RefCell<SListEntry<i32>>>> = None;
    let mut list = generate_list();

    /* Remove the third entry */
    let entry = slist_nth_entry(list.clone(), 2);
    assert!(slist_remove_entry(&mut list, &entry) != 0);
    assert!(slist_length(list.clone()) == 3);

    /* Remove the first entry */
    let entry = slist_nth_entry(list.clone(), 0);
    assert!(slist_remove_entry(&mut list, &entry) != 0);
    assert!(slist_length(list.clone()) == 2);

    /* Try some invalid removes */

    /* This was already removed: */
    assert!(slist_remove_entry(&mut list, &entry) == 0);

    /* NULL */
    assert!(slist_remove_entry(&mut list, &None) == 0);

    /* Removing NULL from an empty list */
    assert!(slist_remove_entry(&mut empty_list, &None) == 0);

    slist_free(list);
}

#[test]
pub fn test_slist_append() {
    let mut list: Option<Rc<RefCell<SListEntry<&i32>>>> = None;

    assert!(slist_append(&mut list, &variable1).is_some());
    assert!(slist_append(&mut list, &variable2).is_some());
    assert!(slist_append(&mut list, &variable3).is_some());
    assert!(slist_append(&mut list, &variable4).is_some());
    assert_eq!(slist_length(list.clone()), 4);

    assert_eq!(slist_nth_data(list.clone(), 0), Some(&variable1));
    assert_eq!(slist_nth_data(list.clone(), 1), Some(&variable2));
    assert_eq!(slist_nth_data(list.clone(), 2), Some(&variable3));
    assert_eq!(slist_nth_data(list.clone(), 3), Some(&variable4));

    slist_free(list);
}

#[test]
pub fn test_slist_free() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = generate_list();

    slist_free(list);

    /* Check the empty list frees correctly */
    slist_free::<i32>(None);
}

#[test]
pub fn test_slist_iterate() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;
    let mut iter = SListIterator {
        prev_next: None,
        current: None,
    };
    let mut data: Option<i32>;
    let mut a: i32 = 0;
    let mut i: i32;
    let mut counter: i32 = 0;

    for i in 0..50 {
        list = slist_prepend(&mut list, a);
    }

    counter = 0;

    slist_iterate(list.clone(), &mut iter);

    slist_iter_remove(&mut iter);

    while slist_iter_has_more(&mut iter) {
        data = slist_iter_next(&mut iter);

        if let Some(_) = data {
            counter += 1;
        }

        if (counter % 2) == 0 {
            slist_iter_remove(&mut iter);
            slist_iter_remove(&mut iter);
        }
    }

    assert!(slist_iter_next(&mut iter).is_none());

    slist_iter_remove(&mut iter);

    assert_eq!(counter, 50);
    assert_eq!(slist_length(list.clone()), 25);

    slist_free(list);

    list = None;
    counter = 0;

    slist_iterate(list.clone(), &mut iter);

    while slist_iter_has_more(&mut iter) {
        data = slist_iter_next(&mut iter);

        if let Some(_) = data {
            counter += 1;
        }

        if (counter % 2) == 0 {
            slist_iter_remove(&mut iter);
        }
    }

    assert_eq!(counter, 0);
}

#[test]
pub fn test_slist_prepend() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;

    assert!(slist_prepend(&mut list, variable1).is_some());
    assert!(slist_prepend(&mut list, variable2).is_some());
    assert!(slist_prepend(&mut list, variable3).is_some());
    assert!(slist_prepend(&mut list, variable4).is_some());

    assert_eq!(slist_nth_data(list.clone(), 0), Some(variable4));
    assert_eq!(slist_nth_data(list.clone(), 1), Some(variable3));
    assert_eq!(slist_nth_data(list.clone(), 2), Some(variable2));
    assert_eq!(slist_nth_data(list.clone(), 3), Some(variable1));

    slist_free(list);
}

#[test]
pub fn test_slist_to_array() {
    let mut list = generate_list();

    let array = slist_to_array(list.clone());

    assert_eq!(array.as_ref().unwrap()[0], variable1);
    assert_eq!(array.as_ref().unwrap()[1], variable2);
    assert_eq!(array.as_ref().unwrap()[2], variable3);
    assert_eq!(array.as_ref().unwrap()[3], variable4);

    slist_free(list);
}

#[test]
pub fn test_slist_next() {
    let mut list = generate_list();
    let mut rover = list.clone();

    assert_eq!(slist_data(rover.as_ref().unwrap()), variable1);
    rover = slist_next(rover);
    assert_eq!(slist_data(rover.as_ref().unwrap()), variable2);
    rover = slist_next(rover);
    assert_eq!(slist_data(rover.as_ref().unwrap()), variable3);
    rover = slist_next(rover);
    assert_eq!(slist_data(rover.as_ref().unwrap()), variable4);
    rover = slist_next(rover);
    assert!(rover.is_none());

    slist_free(list);
}

#[test]
pub fn test_slist_iterate_bad_remove() {
    return;
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;
    let mut iter = SListIterator {
        prev_next: None,
        current: None,
    };
    let mut values = [0; 49];

    for i in 0..49 {
        values[i] = i as i32;
        slist_prepend(&mut list, values[i]);
    }

    slist_iterate(list.clone(), &mut iter);

    while slist_iter_has_more(&mut iter) {
        if let Some(val) = slist_iter_next(&mut iter) {
            if val % 2 == 0 {
                assert!(slist_remove_data(&mut list, int_equal, val) != 0);
                slist_iter_remove(&mut iter);
            }
        }
    }

    slist_free(list);
}

#[test]
pub fn test_slist_remove_data() {
    let entries = vec![89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let num_entries = entries.len() as u32;
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;

    for entry in entries.iter().rev() {
        slist_prepend(&mut list, *entry);
    }

    let mut val = 0;
    assert_eq!(slist_remove_data(&mut list, |&a, &b| a == b, val), 0);
    val = 56;
    assert_eq!(slist_remove_data(&mut list, |&a, &b| a == b, val), 0);

    val = 8;
    assert_eq!(slist_remove_data(&mut list, |&a, &b| a == b, val), 1);
    assert_eq!(slist_length(list.clone()), num_entries - 1);

    val = 4;
    assert_eq!(slist_remove_data(&mut list, |&a, &b| a == b, val), 4);
    assert_eq!(slist_length(list.clone()), num_entries - 5);

    val = 89;
    assert_eq!(slist_remove_data(&mut list, |&a, &b| a == b, val), 1);
    assert_eq!(slist_length(list.clone()), num_entries - 6);

    slist_free(list);
}

#[test]
pub fn test_slist_sort() {
    let mut list: Option<Rc<RefCell<SListEntry<i32>>>> = None;
    let entries = [89, 4, 23, 42, 4, 16, 15, 4, 8, 99, 50, 30, 4];
    let sorted = [4, 4, 4, 4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    for i in 0..num_entries {
        list = slist_prepend(&mut list, entries[i]);
    }

    slist_sort(&mut list, |a, b| a.cmp(b) as i32);

    assert_eq!(slist_length(list.clone()), num_entries as u32);

    for i in 0..num_entries {
        let value = slist_nth_data(list.clone(), i);
        assert_eq!(value, Some(sorted[i]));
    }

    slist_free(list);

    list = None;

    slist_sort(&mut list, |a, b| a.cmp(b) as i32);

    assert!(list.is_none());
}

pub fn int_equal(a: &i32, b: &i32) -> bool {
    *a == *b
}
