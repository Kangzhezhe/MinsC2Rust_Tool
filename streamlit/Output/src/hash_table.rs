use std::cell::{Cell, RefCell};

thread_local! {
    pub static ALLOCATED_KEYS: Cell<usize> = Cell::new(0);
}

pub struct AllocatedValues {
    pub count: usize,
}

impl Clone for AllocatedValues {
    fn clone(&self) -> Self {
        AllocatedValues {
            count: self.count,
        }
    }
}

thread_local! {
    pub static ALLOCATED_VALUES: RefCell<AllocatedValues> = RefCell::new(AllocatedValues { count: 0 });
}

pub struct HashTableEntry {
    pub pair: HashTablePair,
    pub next: Option<Box<HashTableEntry>>,
}

impl Clone for HashTableEntry {
    fn clone(&self) -> Self {
        HashTableEntry {
            pair: self.pair.clone(),
            next: self.next.clone(),
        }
    }
}

pub struct HashTableIterator {
    pub hash_table: Option<Box<HashTable>>,
    pub next_entry: Option<Box<HashTableEntry>>,
    pub next_chain: u32,
}

impl Clone for HashTableIterator {
    fn clone(&self) -> Self {
        HashTableIterator {
            hash_table: self.hash_table.clone(),
            next_entry: self.next_entry.clone(),
            next_chain: self.next_chain,
        }
    }
}

pub struct HashTable {
    pub table: Vec<Option<Box<HashTableEntry>>>,
    pub table_size: u32,
    pub hash_func: HashTableHashFunc,
    pub equal_func: HashTableEqualFunc,
    pub key_free_func: Option<HashTableKeyFreeFunc>,
    pub value_free_func: Option<HashTableValueFreeFunc>,
    pub entries: u32,
    pub prime_index: u32,
}

impl Clone for HashTable {
    fn clone(&self) -> Self {
        HashTable {
            table: self.table.iter().cloned().collect(),
            table_size: self.table_size,
            hash_func: self.hash_func,
            equal_func: self.equal_func,
            key_free_func: self.key_free_func,
            value_free_func: self.value_free_func,
            entries: self.entries,
            prime_index: self.prime_index,
        }
    }
}

pub type HashTableHashFunc = fn(value: HashTableKey) -> u32;
pub type HashTableKeyFreeFunc = fn(value: HashTableKey);
pub type HashTableValueFreeFunc = fn(value: HashTableValue);
pub type HashTableKey = *const std::ffi::c_void;
pub type HashTableValue = *const std::ffi::c_void;
pub type HashTableEqualFunc = fn(value1: HashTableKey, value2: HashTableKey) -> i32;
pub type HashTablePair = (HashTableKey, HashTableValue);

pub const HASH_TABLE_PRIMES: [u32; 24] = [
    193, 389, 769, 1543, 3079, 6151, 12289, 24593, 49157, 98317,
    196613, 393241, 786433, 1572869, 3145739, 6291469,
    12582917, 25165843, 50331653, 100663319, 201326611,
    402653189, 805306457, 1610612741,
];

pub const HASH_TABLE_NUM_PRIMES: u32 = HASH_TABLE_PRIMES.len() as u32;

pub const NUM_TEST_VALUES: u32 = 10000;

pub fn hash_table_allocate_table(hash_table: &mut HashTable) -> bool {
    let new_table_size: u32;

    if hash_table.prime_index < HASH_TABLE_NUM_PRIMES {
        new_table_size = HASH_TABLE_PRIMES[hash_table.prime_index as usize];
    } else {
        new_table_size = hash_table.entries * 10;
    }

    hash_table.table_size = new_table_size;

    hash_table.table = vec![None; new_table_size as usize];

    !hash_table.table.is_empty()
}

pub fn hash_table_enlarge(hash_table: &mut HashTable) -> bool {
    let mut old_table = std::mem::replace(&mut hash_table.table, Vec::new());
    let old_table_size = hash_table.table_size;
    let old_prime_index = hash_table.prime_index;

    hash_table.prime_index += 1;

    if !hash_table_allocate_table(hash_table) {
        hash_table.table = old_table;
        hash_table.table_size = old_table_size;
        hash_table.prime_index = old_prime_index;
        return false;
    }

    for i in 0..old_table_size {
        let mut rover = old_table[i as usize].take();
        while let Some(mut entry) = rover {
            let next = entry.next.take();
            let pair = entry.pair;
            let index = (hash_table.hash_func)(pair.0) % hash_table.table_size;
            entry.next = hash_table.table[index as usize].take();
            hash_table.table[index as usize] = Some(entry);
            rover = next;
        }
    }

    true
}

pub fn hash_table_new(hash_func: HashTableHashFunc, equal_func: HashTableEqualFunc) -> Option<Box<HashTable>> {
    let mut hash_table = Box::new(HashTable {
        table: Vec::new(),
        table_size: 0,
        hash_func,
        equal_func,
        key_free_func: None,
        value_free_func: None,
        entries: 0,
        prime_index: 0,
    });

    if !hash_table_allocate_table(&mut hash_table) {
        return None;
    }

    Some(hash_table)
}

pub fn hash_table_insert(hash_table: &mut HashTable, key: HashTableKey, value: HashTableValue) -> i32 {
    let mut index = (hash_table.hash_func)(key) % hash_table.table_size;
    let mut rover = hash_table.table[index as usize].clone();

    if (hash_table.entries * 3) / hash_table.table_size > 0 {
        if !hash_table_enlarge(hash_table) {
            return 0;
        }

        index = (hash_table.hash_func)(key) % hash_table.table_size;
        rover = hash_table.table[index as usize].clone();
    }

    while let Some(mut entry) = rover {
        let pair = &mut entry.pair;

        if (hash_table.equal_func)(pair.0, key) != 0 {
            if let Some(value_free_func) = hash_table.value_free_func {
                value_free_func(pair.1);
            }

            if let Some(key_free_func) = hash_table.key_free_func {
                key_free_func(pair.0);
            }

            pair.0 = key;
            pair.1 = value;

            return 1;
        }

        rover = entry.next.clone();
    }

    let mut newentry = Box::new(HashTableEntry {
        pair: (key, value),
        next: None,
    });

    newentry.next = hash_table.table[index as usize].take();
    hash_table.table[index as usize] = Some(newentry);

    hash_table.entries += 1;

    1
}

pub fn hash_table_register_free_functions(hash_table: &mut HashTable, key_free_func: Option<HashTableKeyFreeFunc>, value_free_func: Option<HashTableValueFreeFunc>) {
    hash_table.key_free_func = key_free_func;
    hash_table.value_free_func = value_free_func;
}

pub fn hash_table_free_entry(hash_table: &mut HashTable, entry: Box<HashTableEntry>) {
    let pair = entry.pair;

    if let Some(key_free_func) = hash_table.key_free_func {
        key_free_func(pair.0);
    }

    if let Some(value_free_func) = hash_table.value_free_func {
        value_free_func(pair.1);
    }
}

pub fn hash_table_iterate(hash_table: &mut HashTable, iterator: &mut HashTableIterator) {
    let mut chain = 0;

    iterator.hash_table = Some(Box::new(hash_table.clone()));

    // Default value of next if no entries are found.
    iterator.next_entry = None;

    // Find the first entry
    while chain < hash_table.table_size {
        if let Some(entry) = hash_table.table[chain as usize].clone() {
            iterator.next_entry = Some(entry);
            iterator.next_chain = chain;
            break;
        }
        chain += 1;
    }
}

pub fn hash_table_iter_has_more(iterator: &mut HashTableIterator) -> bool {
    iterator.next_entry.is_some()
}

pub fn hash_table_iter_next(iterator: &mut HashTableIterator) -> HashTablePair {
    let current_entry = iterator.next_entry.take();
    let hash_table = iterator.hash_table.as_mut();
    let mut pair = (std::ptr::null(), std::ptr::null());
    let mut chain = iterator.next_chain;

    if current_entry.is_none() {
        return pair;
    }

    let current_entry_unwrapped = current_entry.unwrap();
    pair = current_entry_unwrapped.pair;

    if current_entry_unwrapped.next.is_some() {
        iterator.next_entry = current_entry_unwrapped.next;
    } else {
        chain += 1;
        iterator.next_entry = None;

        while chain < hash_table.as_ref().unwrap().table_size {
            if hash_table.as_ref().unwrap().table[chain as usize].is_some() {
                iterator.next_entry = hash_table.as_ref().unwrap().table[chain as usize].clone();
                break;
            }
            chain += 1;
        }

        iterator.next_chain = chain;
    }

    pair
}

pub fn hash_table_free(mut hash_table: Box<HashTable>) {
    let mut entries = hash_table.table.drain(..).filter_map(|entry| entry).collect::<Vec<_>>();
    while let Some(mut current) = entries.pop() {
        while let Some(next) = current.next.take() {
            hash_table_free_entry(&mut hash_table, current);
            current = next;
        }
        hash_table_free_entry(&mut hash_table, current);
    }
}

pub fn hash_table_remove(hash_table: &mut HashTable, key: HashTableKey) -> i32 {
    let index = (hash_table.hash_func)(key) % hash_table.table_size;

    let mut rover = &mut hash_table.table[index as usize];
    let mut result = 0;

    while let Some(entry) = rover.take() {
        let pair = &entry.pair;

        if (hash_table.equal_func)(key, pair.0) != 0 {
            hash_table_free_entry(hash_table, entry);
            hash_table.entries -= 1;
            result = 1;
            break;
        } else {
            *rover = entry.next;
            rover = &mut rover.as_mut().unwrap().next;
        }
    }

    result
}

pub fn hash_table_num_entries(hash_table: &HashTable) -> u32 {
    hash_table.entries
}

pub fn hash_table_lookup(hash_table: &HashTable, key: HashTableKey) -> Option<HashTableValue> {
    let index = (hash_table.hash_func)(key) % hash_table.table_size;
    let mut rover = hash_table.table.get(index as usize)?.as_ref();

    while let Some(entry) = rover {
        if (hash_table.equal_func)(key, entry.pair.0) != 0 {
            return Some(entry.pair.1);
        }
        rover = entry.next.as_ref();
    }

    None
}

