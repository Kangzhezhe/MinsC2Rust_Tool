pub trait ArrayListComparable: PartialEq + std::fmt::Debug {
    fn compare(&self, other: &Self) -> i32;
}

#[derive(Clone, PartialEq, std::fmt::Debug)]
pub struct CustomInt(pub i32);

impl ArrayListComparable for CustomInt {
    fn compare(&self, other: &Self) -> i32 {
        self.0.cmp(&other.0) as i32
    }
}

pub struct ArrayList<T: ArrayListComparable + Clone> {
    pub data: Vec<T>,
    pub length: usize,
    _alloced: usize,
}

pub trait ArrayListEqualFunc<T: ArrayListComparable + Clone> {
    fn equal(&self, value1: &T, value2: &T) -> bool;
}

impl<F, T> ArrayListEqualFunc<T> for F where F: Fn(&T, &T) -> bool, T: ArrayListComparable + Clone {
    fn equal(&self, value1: &T, value2: &T) -> bool {
        self(value1, value2)
    }
}
pub fn arraylist_sort_internal<T: ArrayListComparable + Clone>(list_data: &mut [T]) {
    if list_data.len() <= 1 {
        return;
    }

    let pivot_index = list_data.len() - 1;
    let pivot = list_data[pivot_index].clone();
    let mut list1_length = 0;

    for i in 0..pivot_index {
        if list_data[i].compare(&pivot) < 0 {
            list_data.swap(i, list1_length);
            list1_length += 1;
        }
    }

    list_data.swap(list1_length, pivot_index);

    arraylist_sort_internal(&mut list_data[0..list1_length]);
    arraylist_sort_internal(&mut list_data[list1_length + 1..]);
}

pub fn arraylist_enlarge<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>) -> i32 {
    let newsize = arraylist._alloced * 2;
    let mut new_data = Vec::with_capacity(newsize);

    if new_data.capacity() < newsize {
        return 0;
    }

    new_data.extend_from_slice(&arraylist.data);
    arraylist.data = new_data;
    arraylist._alloced = newsize;

    1
}

pub fn arraylist_insert<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>, index: usize, data: T) -> i32 {
    if index > arraylist.length {
        return 0;
    }

    if arraylist.length + 1 > arraylist._alloced {
        if arraylist_enlarge(arraylist) == 0 {
            return 0;
        }
    }

    arraylist.data.insert(index, data);
    arraylist.length += 1;

    1
}

pub fn arraylist_new<T: ArrayListComparable + Clone>(length: usize) -> Option<ArrayList<T>> {
    let mut len = length;
    if len <= 0 {
        len = 16;
    }

    let data: Vec<T> = Vec::with_capacity(len);

    Some(ArrayList {
        data,
        length: 0,
        _alloced: len,
    })
}

pub fn arraylist_append<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>, data: T) -> i32 {
    arraylist_insert(arraylist, arraylist.length, data)
}

pub fn arraylist_remove_range<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>, index: usize, length: usize) {
    // Check this is a valid range
    if index > arraylist.length || index + length > arraylist.length {
        return;
    }

    // Move back the entries following the range to be removed
    let shift_end = arraylist.length;
    for i in index..shift_end - length {
        arraylist.data[i] = arraylist.data[i + length].clone();
    }

    // Decrease the counter
    arraylist.length -= length;
}

pub fn arraylist_free<T: ArrayListComparable + Clone>(arraylist: Option<Box<ArrayList<T>>>) {
    if let Some(mut list) = arraylist {
        list.data.clear();
    }
}

pub fn arraylist_clear<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>) {
    arraylist.length = 0;
}

pub fn arraylist_prepend<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>, data: T) -> i32 {
    arraylist_insert(arraylist, 0, data)
}

pub fn arraylist_remove<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>, index: usize) {
    arraylist_remove_range(arraylist, index, 1);
}

pub fn arraylist_sort<T: ArrayListComparable + Clone>(arraylist: &mut ArrayList<T>, compare_func: fn(&T, &T) -> i32) {
    arraylist_sort_internal(&mut arraylist.data[..arraylist.length]);
}

pub fn arraylist_index_of<T: ArrayListComparable + Clone, F: ArrayListEqualFunc<T>>(arraylist: &ArrayList<T>, callback: F, data: &T) -> i32 {
    for (i, item) in arraylist.data.iter().enumerate() {
        if callback.equal(item, data) {
            return i as i32;
        }
    }

    -1
}

