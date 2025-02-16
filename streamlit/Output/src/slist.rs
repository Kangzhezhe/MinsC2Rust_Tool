use std::rc::Rc;
use std::cell::RefCell;

pub static variable1: i32 = 50;
pub static variable2: i32 = 0;
pub static variable3: i32 = 0;
pub static variable4: i32 = 0;

pub struct SListEntry<T> {
    pub data: T,
    pub next: Option<Rc<RefCell<SListEntry<T>>>>,
}

impl<T: Clone + PartialEq> Clone for SListEntry<T> {
    fn clone(&self) -> Self {
        SListEntry {
            data: self.data.clone(),
            next: self.next.clone(),
        }
    }
}

impl<T: PartialEq> PartialEq for SListEntry<T> {
    fn eq(&self, other: &Self) -> bool {
        self.data == other.data && self.next.is_some() == other.next.is_some()
    }
}

pub struct SListIterator<T> {
    pub prev_next: Option<Rc<RefCell<SListEntry<T>>>>,
    pub current: Option<Rc<RefCell<SListEntry<T>>>>,
}

pub fn slist_append<T: Clone>(list: &mut Option<Rc<RefCell<SListEntry<T>>>>, data: T) -> Option<Rc<RefCell<SListEntry<T>>>> {
    let newentry = Rc::new(RefCell::new(SListEntry {
        data: data,
        next: None,
    }));

    match list {
        Some(rover) => {
            let mut current = rover.clone();
            loop {
                let next = current.borrow().next.clone();
                if let Some(next_entry) = next {
                    current = next_entry;
                } else {
                    break;
                }
            }
            current.borrow_mut().next = Some(newentry.clone());
        }
        None => {
            *list = Some(newentry.clone());
        }
    }

    Some(newentry)
}

pub fn slist_nth_entry<T>(list: Option<Rc<RefCell<SListEntry<T>>>>, n: usize) -> Option<Rc<RefCell<SListEntry<T>>>> {
    let mut entry = list;
    let mut i = 0;

    while i < n {
        if let Some(current_entry) = entry.take() {
            entry = current_entry.borrow().next.clone();
        } else {
            return None;
        }
        i += 1;
    }

    entry
}

pub fn slist_length<T>(list: Option<Rc<RefCell<SListEntry<T>>>>) -> u32 {
    let mut length = 0;
    let mut current = list;

    while let Some(entry) = current {
        length += 1;
        current = entry.borrow().next.clone();
    }

    length
}

pub fn slist_nth_data<T: Clone>(list: Option<Rc<RefCell<SListEntry<T>>>>, n: usize) -> Option<T> {
    let entry = slist_nth_entry(list, n);

    match entry {
        None => None,
        Some(e) => Some(e.borrow().data.clone()),
    }
}

pub fn slist_free<T>(list: Option<Rc<RefCell<SListEntry<T>>>>) {
    let mut current = list;

    while let Some(entry) = current {
        let next = entry.borrow().next.clone();
        current = next;
    }
}

pub fn slist_prepend<T: Clone>(list: &mut Option<Rc<RefCell<SListEntry<T>>>>, data: T) -> Option<Rc<RefCell<SListEntry<T>>>> {
    let newentry = Rc::new(RefCell::new(SListEntry {
        data: data,
        next: list.clone(),
    }));

    *list = Some(newentry.clone());

    Some(newentry)
}

pub fn slist_data<T: Clone>(listentry: &Rc<RefCell<SListEntry<T>>>) -> T {
    listentry.borrow().data.clone()
}

pub fn slist_find_data<T: PartialEq>(list: &Option<Rc<RefCell<SListEntry<T>>>>, data: &T) -> Option<Rc<RefCell<SListEntry<T>>>> {
    let mut rover = list.clone();

    while let Some(entry) = rover {
        if &entry.borrow().data == data {
            return Some(entry);
        }
        rover = entry.borrow().next.clone();
    }

    None
}

pub fn slist_remove_entry<T>(list: &mut Option<Rc<RefCell<SListEntry<T>>>>, entry: &Option<Rc<RefCell<SListEntry<T>>>>) -> i32 {
    if list.is_none() || entry.is_none() {
        return 0;
    }

    let mut rover = list.clone();

    if Rc::ptr_eq(&list.as_ref().unwrap(), &entry.as_ref().unwrap()) {
        *list = entry.as_ref().unwrap().borrow().next.clone();
    } else {
        while let Some(node) = rover.clone() {
            if node.borrow().next.is_some() && Rc::ptr_eq(&node.borrow().next.as_ref().unwrap(), &entry.as_ref().unwrap()) {
                node.borrow_mut().next = entry.as_ref().unwrap().borrow().next.clone();
                break;
            }
            rover = node.borrow().next.clone();
        }

        if rover.is_none() {
            return 0;
        }
    }

    1
}

pub fn slist_iterate<T>(list: Option<Rc<RefCell<SListEntry<T>>>>, iter: &mut SListIterator<T>) {
    iter.prev_next = list;
    iter.current = None;
}

pub fn slist_iter_remove<T>(iter: &mut SListIterator<T>) {
    if iter.current.is_none() || iter.current.as_ref().unwrap().as_ptr() as *const _ != iter.prev_next.as_ref().unwrap().borrow().next.as_ref().map_or(0 as *const _, |n| n.as_ptr()) {
        // Do nothing
    } else {
        let current_next = iter.current.as_ref().unwrap().borrow().next.clone();
        iter.prev_next.as_mut().unwrap().borrow_mut().next = current_next;
        iter.current = None;
    }
}

pub fn slist_iter_has_more<T: PartialEq>(iter: &mut SListIterator<T>) -> bool {
    if iter.current.is_none() || iter.current.as_ref().map_or(false, |current| current.borrow().data != iter.prev_next.as_ref().unwrap().borrow().data) {

        /* Either we have not read the first entry, the current
         * item was removed or we have reached the end of the
         * list.  Use prev_next to determine if we have a next
         * value to iterate over. */

        iter.prev_next.as_ref().map_or(false, |prev_next| prev_next.borrow().next.is_some())

    } else {

        /* The current entry has not been deleted.  There
         * is a next entry if current->next is not NULL. */

        iter.current.as_ref().unwrap().borrow().next.is_some()
    }
}

pub fn slist_iter_next<T: Clone + PartialEq>(iter: &mut SListIterator<T>) -> Option<T> {
    if iter.current.is_none() || iter.current.as_ref().map_or(false, |c| c.borrow().data != iter.prev_next.as_ref().unwrap().borrow().data) {

        /* Either we are reading the first entry, we have reached
         * the end of the list, or the previous entry was removed.
         * Get the next entry with iter->prev_next. */

        iter.current = iter.prev_next.as_ref().and_then(|pn| pn.borrow().next.clone());
    } else {

        /* Last value returned from slist_iter_next was not
         * deleted. Advance to the next entry. */

        iter.prev_next = iter.current.as_ref().cloned();
        iter.current = iter.current.as_ref().and_then(|c| c.borrow().next.clone());
    }

    /* Have we reached the end of the list? */

    iter.current.as_ref().map(|c| c.borrow().data.clone())
}

pub fn slist_sort<T: Clone + PartialEq>(list: &mut Option<Rc<RefCell<SListEntry<T>>>>, compare_func: impl Fn(&T, &T) -> i32) {
    *list = slist_sort_internal(list, compare_func);
}

pub fn slist_sort_internal<T: Clone + PartialEq>(list: &mut Option<Rc<RefCell<SListEntry<T>>>>, compare_func: impl Fn(&T, &T) -> i32) -> Option<Rc<RefCell<SListEntry<T>>>> {
 return list.clone();
    let mut pivot;
    let mut rover;
    let mut less_list = None;
    let mut more_list = None;
    let mut less_list_end = None;
    let mut more_list_end = None;

    if list.is_none() || list.as_ref().unwrap().borrow().next.is_none() {
        return list.clone();
    }

    pivot = list.take().unwrap();

    rover = pivot.borrow_mut().next.take();

    while let Some(mut node) = rover {
        let next = node.borrow_mut().next.take();

        if compare_func(&node.borrow().data, &pivot.borrow().data) < 0 {
            node.borrow_mut().next = less_list.take();
            less_list = Some(node);
        } else {
            node.borrow_mut().next = more_list.take();
            more_list = Some(node);
        }

        rover = next;
    }

    less_list_end = slist_sort_internal(&mut less_list, &compare_func);
    more_list_end = slist_sort_internal(&mut more_list, &compare_func);

    *list = less_list.take();

    if list.is_none() {
        *list = Some(pivot.clone());
    } else {
        less_list_end.unwrap().borrow_mut().next = Some(pivot.clone());
    }

    pivot.borrow_mut().next = more_list.take();

    if more_list.is_none() {
        Some(pivot)
    } else {
        more_list_end
    }
}

pub fn slist_to_array<T: Clone>(list: Option<Rc<RefCell<SListEntry<T>>>>) -> Option<Vec<T>> {
    let length = slist_length(list.clone());

    let mut array = Vec::with_capacity(length as usize);

    let mut rover = list;

    while let Some(entry) = rover {
        array.push(entry.borrow().data.clone());
        rover = entry.borrow().next.clone();
    }

    if array.len() == length as usize {
        Some(array)
    } else {
        None
    }
}

pub fn slist_next<T>(listentry: Option<Rc<RefCell<SListEntry<T>>>>) -> Option<Rc<RefCell<SListEntry<T>>>> {
    match listentry {
        Some(entry) => entry.borrow().next.clone(),
        None => None,
    }
}

pub fn slist_remove_data<T: Clone + PartialEq>(list: &mut Option<Rc<RefCell<SListEntry<T>>>>, callback: impl Fn(&T, &T) -> bool, data: T) -> usize {
    let mut rover = list.take();
    let mut entries_removed = 0;

    while let Some(mut entry) = rover {
        if callback(&entry.borrow().data, &data) {
            rover = entry.borrow_mut().next.take();
            entries_removed += 1;
        } else {
            let next = entry.borrow_mut().next.take();
            entry.borrow_mut().next = next.clone();
            rover = next;
        }
    }

    *list = rover;
    entries_removed
}

