pub static variable1: i32 = 50;
pub static variable2: i32 = 0;
pub static variable3: i32 = 0;
pub static variable4: i32 = 0;

use std::cell::RefCell;
use std::rc::Rc;

#[derive(Debug, PartialEq, Clone)]
pub struct ListEntry<T: Clone> {
    pub data: T,
    pub prev: Option<Rc<RefCell<ListEntry<T>>>>,
    pub next: Option<Rc<RefCell<ListEntry<T>>>>,
}

pub type ListEqualFunc<T> = fn(&T, &T) -> bool;

pub type ListCompareFunc<T> = Option<fn(&T, &T) -> i32>;

pub struct ListIterator<'a, T: Clone> {
    pub prev_next: &'a mut Option<Rc<RefCell<ListEntry<T>>>>,
    pub current: Option<Rc<RefCell<ListEntry<T>>>>,
}
pub fn list_append<T: Clone>(list: &mut Option<Rc<RefCell<ListEntry<T>>>>, data: T) -> Option<Rc<RefCell<ListEntry<T>>>> {
    if list.is_none() {
        return None;
    }

    let newentry = Rc::new(RefCell::new(ListEntry {
        data,
        prev: None,
        next: None,
    }));

    if list.as_ref().unwrap().borrow().next.is_none() {
        list.as_mut().unwrap().borrow_mut().next = Some(Rc::clone(&newentry));
        newentry.borrow_mut().prev = list.clone();
    } else {
        let mut rover = list.as_ref().unwrap().clone();
        while rover.borrow().next.is_some() {
            let next_rover = rover.borrow().next.as_ref().unwrap().clone();
            rover = next_rover;
        }
        rover.borrow_mut().next = Some(Rc::clone(&newentry));
        newentry.borrow_mut().prev = Some(rover);
    }

    Some(newentry)
}

pub fn list_next<T: Clone>(listentry: Option<Rc<RefCell<ListEntry<T>>>>) -> Option<Rc<RefCell<ListEntry<T>>>> {
    if let Some(entry) = listentry {
        entry.borrow().next.clone()
    } else {
        None
    }
}

pub fn list_nth_entry<T: Clone>(list: Option<Rc<RefCell<ListEntry<T>>>>, n: usize) -> Option<Rc<RefCell<ListEntry<T>>>> {
    let mut current_entry = list;
    let mut i = 0;

    while i < n {
        if let Some(e) = current_entry {
            current_entry = e.borrow().next.clone();
        } else {
            return None;
        }
        i += 1;
    }

    current_entry
}

pub fn list_length<T: Clone>(list: Option<Rc<RefCell<ListEntry<T>>>>) -> usize {
    let mut length = 0;
    let mut entry = list;

    while let Some(current_entry) = entry.take() {
        length += 1;
        entry = current_entry.borrow().next.clone();
    }

    length
}

pub fn list_prev<T: Clone>(listentry: &Option<Rc<RefCell<ListEntry<T>>>>) -> Option<Rc<RefCell<ListEntry<T>>>> {
    if let Some(entry) = listentry {
        entry.borrow().prev.clone()
    } else {
        None
    }
}

pub fn list_data<T: Clone>(listentry: Option<Rc<RefCell<ListEntry<T>>>>) -> Option<T> {
    if let Some(entry) = listentry {
        Some(entry.borrow().data.clone())
    } else {
        None
    }
}

pub fn list_free<T: Clone>(list: Option<Rc<RefCell<ListEntry<T>>>>) {
    let mut entry = list;

    while let Some(current_entry) = entry {
        let next = current_entry.borrow().next.clone();
        drop(current_entry);
        entry = next;
    }
}

pub fn list_remove_entry<T: Clone + PartialEq>(list: &mut Option<Rc<RefCell<ListEntry<T>>>>, entry: &Rc<RefCell<ListEntry<T>>>) -> i32 {
    if list.is_none() || entry.borrow().prev.is_none() && list.as_ref().unwrap().as_ptr() != entry.as_ptr() {
        return 0;
    }

    if entry.borrow().prev.is_none() {
        *list = entry.borrow().next.clone();

        if let Some(next_entry) = entry.borrow().next.as_ref() {
            next_entry.borrow_mut().prev = None;
        }
    } else {
        if let Some(prev_entry) = entry.borrow().prev.as_ref() {
            prev_entry.borrow_mut().next = entry.borrow().next.clone();
        }

        if let Some(next_entry) = entry.borrow().next.as_ref() {
            next_entry.borrow_mut().prev = entry.borrow().prev.clone();
        }
    }

    1
}

pub fn list_prepend<T: Clone>(list: &mut Option<Rc<RefCell<ListEntry<T>>>>, data: T) -> Option<Rc<RefCell<ListEntry<T>>>> {
    let new_entry = Rc::new(RefCell::new(ListEntry {
        data,
        prev: None,
        next: list.clone(),
    }));

    if let Some(old_head) = list.as_ref() {
        old_head.borrow_mut().prev = Some(new_entry.clone());
    }

    *list = Some(new_entry.clone());

    Some(new_entry)
}

pub fn list_remove_data<T: PartialEq + Clone>(list: &mut Option<Rc<RefCell<ListEntry<T>>>>, callback: ListEqualFunc<T>, data: &T) -> usize {
    let mut entries_removed = 0;
    let mut rover = list.clone();

    while let Some(current) = rover {
        let next = current.borrow().next.clone();

        if callback(&current.borrow().data, data) {
            if let Some(prev) = current.borrow().prev.clone() {
                prev.borrow_mut().next = current.borrow().next.clone();
            } else {
                *list = current.borrow().next.clone();
            }

            if let Some(next) = current.borrow().next.clone() {
                next.borrow_mut().prev = current.borrow().prev.clone();
            }

            entries_removed += 1;
        }

        rover = next;
    }

    entries_removed
}

pub fn list_nth_data<T: Clone>(list: Option<Rc<RefCell<ListEntry<T>>>>, n: usize) -> Option<T> {
    let entry = list_nth_entry(list, n);

    entry.map(|e| e.borrow().data.clone())
}

pub fn list_sort_internal<T: Clone + PartialEq>(list: &mut Option<Rc<RefCell<ListEntry<T>>>>, compare_func: ListCompareFunc<T>) -> Option<Rc<RefCell<ListEntry<T>>>> {
    if list.is_none() || compare_func.is_none() {
        return None;
    }

    if list.as_ref().unwrap().borrow().next.is_none() {
        return list.clone();
    }

    let pivot = list.take().unwrap();
    let mut less_list: Option<Rc<RefCell<ListEntry<T>>>> = None;
    let mut more_list: Option<Rc<RefCell<ListEntry<T>>>> = None;
    let mut rover = pivot.borrow().next.clone();

    while let Some(mut node) = rover {
        let next = node.borrow().next.clone();
        if compare_func.unwrap()(&node.borrow().data, &pivot.borrow().data) < 0 {
            node.borrow_mut().prev = None;
            node.borrow_mut().next = less_list.clone();
            if let Some(ref mut less_head) = less_list {
                less_head.borrow_mut().prev = Some(node.clone());
            }
            less_list = Some(node);
        } else {
            node.borrow_mut().prev = None;
            node.borrow_mut().next = more_list.clone();
            if let Some(ref mut more_head) = more_list {
                more_head.borrow_mut().prev = Some(node.clone());
            }
            more_list = Some(node);
        }
        rover = next;
    }

    let less_list_end = list_sort_internal(&mut less_list, compare_func);
    let more_list_end = list_sort_internal(&mut more_list, compare_func);

    *list = less_list.clone();

    if less_list.is_none() {
        pivot.borrow_mut().prev = None;
        *list = Some(pivot.clone());
    } else {
        pivot.borrow_mut().prev = less_list_end.clone();
        less_list_end.unwrap().borrow_mut().next = Some(pivot.clone());
    }

    pivot.borrow_mut().next = more_list.clone();
    if let Some(ref mut more_head) = more_list {
        more_head.borrow_mut().prev = Some(pivot.clone());
    }

    if more_list.is_none() {
        Some(pivot)
    } else {
        more_list_end
    }
}

pub fn list_sort<T: Clone + PartialEq>(list: &mut Option<Rc<RefCell<ListEntry<T>>>>, compare_func: ListCompareFunc<T>) {
    *list = list_sort_internal(list, compare_func);
}

pub fn list_find_data<T: Clone>(list: &Option<Rc<RefCell<ListEntry<T>>>>, callback: ListEqualFunc<T>, data: &T) -> Option<Rc<RefCell<ListEntry<T>>>> {
    let mut rover = list.clone();

    while let Some(entry) = rover {
        if callback(&entry.borrow().data, data) {
            return Some(entry);
        }
        rover = entry.borrow().next.clone();
    }

    None
}

pub fn list_iterate<'a, T: Clone>(list: &'a mut Option<Rc<RefCell<ListEntry<T>>>>, iter: &mut ListIterator<'a, T>) {
    /* Start iterating from the beginning of the list. */
    iter.prev_next = list;

    /* We have not yet read the first item. */
    iter.current = None;
}

pub fn list_iter_has_more<T: Clone>(iter: &mut ListIterator<T>) -> bool {
    if iter.current.is_none() || iter.current.as_ref().unwrap().as_ptr() != iter.prev_next.as_ref().unwrap().as_ptr() {
        iter.prev_next.is_some()
    } else {
        iter.current.as_ref().unwrap().borrow().next.is_some()
    }
}

pub fn list_iter_next<T: Clone>(iter: &mut ListIterator<T>) -> Option<T> {
    if iter.current.is_none() || iter.current.as_ref().map(|c| c as *const _) != iter.prev_next.as_ref().map(|p| p as *const _) {
        iter.current = iter.prev_next.clone();
    } else {
        if let Some(current) = iter.current.take() {
            *iter.prev_next = current.borrow().next.clone();
            iter.current = current.borrow().next.clone();
        }
    }

    iter.current.as_ref().map(|entry| entry.borrow().data.clone())
}

pub fn list_iter_remove<T: Clone>(iter: &mut ListIterator<T>) {
    if iter.current.is_none() || iter.current.as_ref().map(|c| Rc::ptr_eq(c, iter.prev_next.as_ref().unwrap())) == Some(false) {
        // Do nothing
    } else {
        let current = iter.current.take().unwrap();
        *iter.prev_next = current.borrow().next.clone();

        if let Some(next) = current.borrow().next.as_ref() {
            next.borrow_mut().prev = current.borrow().prev.clone();
        }

        // Drop current automatically when it goes out of scope
        iter.current = None;
    }
}

pub fn list_to_array<T: Clone>(list: Option<Rc<RefCell<ListEntry<T>>>>) -> Option<Vec<T>> {
    let length = list_length(list.clone());

    if length == 0 {
        return None;
    }

    let mut array = Vec::with_capacity(length);
    let mut rover = list;

    for _ in 0..length {
        if let Some(current_entry) = rover {
            array.push(current_entry.borrow().data.clone());
            rover = current_entry.borrow().next.clone();
        } else {
            break;
        }
    }

    Some(array)
}

