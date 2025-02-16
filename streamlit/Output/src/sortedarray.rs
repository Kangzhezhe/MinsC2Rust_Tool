pub struct SortedArrayValue;
pub type SortedArrayCompareFunc<T> = fn(&T, &T) -> i32;
pub type SortedArrayEqualFunc<T> = fn(&T, &T) -> bool;
pub struct SortedArray<T> {
    pub data: Vec<T>,
    pub length: usize,
    _alloced: usize,
    pub equ_func: SortedArrayEqualFunc<T>,
    pub cmp_func: SortedArrayCompareFunc<T>,
}
impl<T: Clone> SortedArray<T> {
    pub fn new(
        length: usize,
        equ_func: SortedArrayEqualFunc<T>,
        cmp_func: SortedArrayCompareFunc<T>,
    ) -> Option<Box<Self>> {
        if equ_func as *const () == std::ptr::null() || cmp_func as *const () == std::ptr::null() {
            return None;
        }

        let mut len = length;
        if len == 0 {
            len = 16;
        }

        let array = vec![unsafe { std::mem::zeroed() }; len];

        Some(Box::new(Self {
            data: array,
            length: 0,
            _alloced: len,
            equ_func,
            cmp_func,
        }))
    }
}
impl<T> Drop for SortedArray<T> {
    fn drop(&mut self) {
        self.data.clear();
    }
}

pub fn sortedarray_new<T: Clone>(
    length: usize,
    equ_func: SortedArrayEqualFunc<T>,
    cmp_func: SortedArrayCompareFunc<T>,
) -> Option<Box<SortedArray<T>>> {
    if equ_func as *const () == std::ptr::null() || cmp_func as *const () == std::ptr::null() {
        return None;
    }

    let mut len = length;
    if len == 0 {
        len = 16;
    }

    let array = vec![unsafe { std::mem::zeroed() }; len];

    Some(Box::new(SortedArray {
        data: array,
        length: 0,
        _alloced: len,
        equ_func,
        cmp_func,
    }))
}

pub fn sortedarray_insert<T: Clone>(sortedarray: &mut SortedArray<T>, data: T) -> i32 {
    let mut left = 0;
    let mut right = sortedarray.length;
    let mut index = 0;

    right = if right > 1 { right } else { 0 };

    while left != right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(&data, &sortedarray.data[index]);
        if order < 0 {
            right = index;
        } else if order > 0 {
            left = index + 1;
        } else {
            break;
        }
    }

    if sortedarray.length > 0 && (sortedarray.cmp_func)(&data, &sortedarray.data[index]) > 0 {
        index += 1;
    }

    if sortedarray.length + 1 > sortedarray._alloced {
        let newsize = sortedarray._alloced * 2;
        let mut new_data = vec![unsafe { std::mem::zeroed() }; newsize];
        new_data[..sortedarray.length].clone_from_slice(&sortedarray.data);
        sortedarray.data = new_data;
        sortedarray._alloced = newsize;
    }

    sortedarray.data.insert(index, data);
    sortedarray.length += 1;

    1
}

pub fn sortedarray_first_index<T>(
    sortedarray: &SortedArray<T>,
    data: &T,
    mut left: usize,
    mut right: usize,
) -> usize {
    let mut index = left;

    while left < right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(data, &sortedarray.data[index]);
        if order > 0 {
            left = index + 1;
        } else {
            right = index;
        }
    }

    index
}

pub fn sortedarray_last_index<T>(
    sortedarray: &SortedArray<T>,
    data: &T,
    mut left: usize,
    mut right: usize,
) -> usize {
    let mut index = right;

    while left < right {
        index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(data, &sortedarray.data[index]);
        if order <= 0 {
            left = index + 1;
        } else {
            right = index;
        }
    }

    index
}

pub fn sortedarray_get<T>(array: Option<&SortedArray<T>>, i: usize) -> Option<&T> {
    if let Some(array) = array {
        if i < array.length {
            return Some(&array.data[i]);
        }
    }
    None
}

pub fn sortedarray_length<T>(array: &SortedArray<T>) -> usize {
    array.length
}

pub fn sortedarray_free<T>(sortedarray: Option<Box<SortedArray<T>>>) {
    if let Some(mut sa) = sortedarray {
        sa.data.clear();
    }
}

pub fn sortedarray_remove_range<T>(sortedarray: &mut SortedArray<T>, index: usize, length: usize) {
    if index > sortedarray.length || index + length > sortedarray.length {
        return;
    }

    let start = index + length;
    let end = sortedarray.length;
    let drain_range = start..end;
    let mut moved_elements = sortedarray.data.drain(drain_range).collect::<Vec<T>>();

    sortedarray.data.truncate(index);
    sortedarray.data.append(&mut moved_elements);

    sortedarray.length -= length;
}

pub fn sortedarray_index_of<T>(sortedarray: &SortedArray<T>, data: &T) -> i32 {
    if sortedarray.length == 0 {
        return -1;
    }

    let mut left = 0;
    let mut right = sortedarray.length;
    right = if right > 1 { right } else { 0 };

    while left != right {
        let index = (left + right) / 2;

        let order = (sortedarray.cmp_func)(data, &sortedarray.data[index]);
        if order < 0 {
            right = index;
        } else if order > 0 {
            left = index + 1;
        } else {
            left = sortedarray_first_index(sortedarray, data, left, index);
            right = sortedarray_last_index(sortedarray, data, index, right);

            for index in left..=right {
                if (sortedarray.equ_func)(data, &sortedarray.data[index]) {
                    return index as i32;
                }
            }

            return -1;
        }
    }

    -1
}

pub fn sortedarray_remove<T>(sortedarray: &mut SortedArray<T>, index: usize) {
    sortedarray_remove_range(sortedarray, index, 1);
}
