use std::vec::Vec;

#[derive(Clone)]
pub struct SetEntry<T: Clone> {
    pub data: T,
    pub next: Option<Box<SetEntry<T>>>
}

#[derive(Clone)]
pub struct Set<T: Clone> {
    pub prime_index: usize,
    pub table_size: usize,
    pub entries: usize,
    pub table: Vec<Option<Box<SetEntry<T>>>>,
    pub hash_func: fn(&T) -> usize,
    pub equal_func: fn(&T, &T) -> bool,
    pub free_func: Option<fn(T)>
}

#[derive(Clone)]
pub struct SetIterator<T: Clone> {
    pub set: Option<Set<T>>, 
    pub next_entry: Option<Box<SetEntry<T>>>, 
    pub next_chain: usize
}

impl<T: Clone> Default for SetIterator<T> {
    fn default() -> Self {
        SetIterator {
            set: None,
            next_entry: None,
            next_chain: 0,
        }
    }
}

const SET_NUM_PRIMES: usize = 24;
const SET_PRIMES: [usize; SET_NUM_PRIMES] = [
    193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317, 196613, 393241, 786433, 1572869,
    3145739, 6291469, 12582917, 25165843, 50331653, 100663319, 201326611, 402653189, 805306457,
    1610612741
];

static mut ALLOCATED_VALUES: usize = 0;
pub fn set_allocate_table<T: Clone>(set: &mut Set<T>) -> bool {
    if set.prime_index < SET_NUM_PRIMES {
        set.table_size = SET_PRIMES[set.prime_index];
    } else {
        set.table_size = set.entries * 10;
    }

    set.table = vec![None; set.table_size];

    true
}

pub fn set_enlarge<T: Clone>(set: &mut Set<T>) -> bool {
    let mut old_table = Vec::new();
    std::mem::swap(&mut old_table, &mut set.table);
    let old_table_size = set.table_size;
    let old_prime_index = set.prime_index;

    set.prime_index += 1;

    if !set_allocate_table(set) {
        set.table = old_table;
        set.table_size = old_table_size;
        set.prime_index = old_prime_index;

        return false;
    }

    for i in 0..old_table_size {
        let mut rover = old_table[i].take();
        while let Some(mut entry) = rover {
            let next = entry.next.take();
            let index = (set.hash_func)(&entry.data) % set.table_size;
            entry.next = set.table[index].take();
            set.table[index] = Some(entry);
            rover = next;
        }
    }

    true
}

pub fn set_free_entry<T: Clone>(set: &mut Set<T>, entry: Box<SetEntry<T>>) {
    if let Some(free_func) = set.free_func {
        free_func(entry.data.clone());
    }
}

pub fn set_new<T: Clone>(hash_func: fn(&T) -> usize, equal_func: fn(&T, &T) -> bool) -> Option<Set<T>> {
    let mut new_set = Set {
        prime_index: 0,
        table_size: 0,
        entries: 0,
        table: Vec::new(),
        hash_func,
        equal_func,
        free_func: None,
    };

    if !set_allocate_table(&mut new_set) {
        return None;
    }

    Some(new_set)
}

pub fn set_register_free_function<T: Clone>(set: &mut Set<T>, free_func: Option<fn(T)>) {
    set.free_func = free_func;
}

pub fn set_insert<T: Clone + Eq>(set: &mut Set<T>, data: T) -> bool {
    let mut newentry = Box::new(SetEntry {
        data: data.clone(),
        next: None,
    });

    if (set.entries * 3) / set.table_size > 0 {
        if !set_enlarge(set) {
            return false;
        }
    }

    let index = (set.hash_func)(&data) % set.table_size;

    let mut rover = set.table[index].take();

    while let Some(entry) = rover {
        if (set.equal_func)(&data, &entry.data) {
            set.table[index] = Some(entry);
            return false;
        }
        newentry.next = Some(entry);
        rover = newentry.next.as_ref().unwrap().next.clone();
    }

    set.table[index] = Some(newentry);
    set.entries += 1;

    true
}

pub fn set_free<T: Clone>(set: &mut Set<T>) {
    let mut rover;
    let mut next;

    for i in 0..set.table_size {
        rover = set.table[i].take();

        while let Some(mut entry) = rover {
            next = entry.next.take();

            set_free_entry(set, entry);

            rover = next;
        }
    }
}

pub fn set_num_entries<T: Clone>(set: &Set<T>) -> usize {
    set.entries
}

pub fn set_query<T: Clone>(set: &Set<T>, data: T) -> i32 {
    let index = (set.hash_func)(&data) % set.table_size;
    let mut rover = set.table[index].as_ref();

    while let Some(entry) = rover {
        if (set.equal_func)(&data, &entry.data) {
            return 1;
        }
        rover = entry.next.as_ref();
    }

    0
}

pub fn set_iterate<T: Clone>(set: &Set<T>, iter: &mut SetIterator<T>) {
    let mut chain = 0;

    iter.set = Some(set.clone());
    iter.next_entry = None;

    /* Find the first entry */
    while chain < set.table_size {
        /* There is a value at the start of this chain */
        if let Some(entry) = &set.table[chain] {
            iter.next_entry = Some(entry.clone());
            break;
        }
        chain += 1;
    }

    iter.next_chain = chain;
}

pub fn set_iter_has_more<T: Clone>(iterator: &SetIterator<T>) -> bool {
    iterator.next_entry.is_some()
}

pub fn set_iter_next<T: Clone>(iterator: &mut SetIterator<T>) -> Option<T> {
    let set = iterator.set.as_ref()?;
    let current_entry = iterator.next_entry.take()?;

    let result = Some(current_entry.data.clone());

    if let Some(next_entry) = current_entry.next {
        iterator.next_entry = Some(next_entry);
    } else {
        let mut chain = iterator.next_chain + 1;

        while chain < set.table_size {
            if let Some(entry) = &set.table[chain] {
                iterator.next_entry = Some(entry.clone());
                break;
            }
            chain += 1;
        }

        iterator.next_chain = chain;
    }

    result
}

pub fn set_union<T: Clone + Eq>(set1: &Set<T>, set2: &Set<T>) -> Option<Set<T>> {
    let mut iterator = SetIterator {
        set: None,
        next_entry: None,
        next_chain: 0,
    };
    let mut new_set = set_new(set1.hash_func, set1.equal_func)?;

    set_iterate(set1, &mut iterator);

    while set_iter_has_more(&iterator) {
        if let Some(value) = set_iter_next(&mut iterator) {
            if !set_insert(&mut new_set, value) {
                set_free(&mut new_set);
                return None;
            }
        }
    }

    set_iterate(set2, &mut iterator);

    while set_iter_has_more(&iterator) {
        if let Some(value) = set_iter_next(&mut iterator) {
            if set_query(&new_set, value.clone()) == 0 {
                if !set_insert(&mut new_set, value) {
                    set_free(&mut new_set);
                    return None;
                }
            }
        }
    }

    Some(new_set)
}

pub fn set_to_array<T: Clone>(set: &Set<T>) -> Vec<T> {
    let mut array = Vec::with_capacity(set.entries);

    for i in 0..set.table_size {
        let mut rover = set.table[i].clone();

        while let Some(entry) = rover {
            array.push(entry.data.clone());
            rover = entry.next;
        }
    }

    array
}

pub fn set_intersection<T: Clone + Eq>(set1: &Set<T>, set2: &Set<T>) -> Option<Set<T>> {
    let mut new_set = match set_new(set1.hash_func, set2.equal_func) {
        Some(s) => s,
        None => return None,
    };

    let mut iterator = SetIterator {
        set: None,
        next_entry: None,
        next_chain: 0,
    };

    set_iterate(set1, &mut iterator);

    while set_iter_has_more(&iterator) {
        let value = set_iter_next(&mut iterator).unwrap();

        if set_query(set2, value.clone()) != 0 {
            if !set_insert(&mut new_set, value) {
                set_free(&mut new_set);
                return None;
            }
        }
    }

    Some(new_set)
}

pub fn set_remove<T: Clone>(set: &mut Set<T>, data: T) -> bool {
    let index = (set.hash_func)(&data) % set.table_size;
    let mut rover = &mut set.table[index];

    while let Some(entry) = rover {
        if (set.equal_func)(&data, &entry.data) {
            let next = entry.next.take();
            *rover = next;
            set.entries -= 1;
            return true;
        }
        rover = &mut rover.as_mut().unwrap().next;
    }

    false
}

