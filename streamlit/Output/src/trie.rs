use std::clone::Clone;

pub struct TrieNode<T> {
    pub data: Option<T>,
    pub use_count: u32,
    pub next: [Option<Box<TrieNode<T>>>; 256],
}

impl<T: Clone> Clone for TrieNode<T> {
    fn clone(&self) -> Self {
        TrieNode {
            data: self.data.clone(),
            use_count: self.use_count,
            next: self.next.clone(),
        }
    }
}

pub struct Trie<T> {
    pub root_node: Option<Box<TrieNode<T>>>,
}

pub const bin_key4: [u8; 4] = [ b'z', 0, b'z', b'z' ];
pub const bin_key2: [u8; 8] = [ b'a', b'b', b'c', 0, 1, 2, 0xff, 0 ];
pub const bin_key3: [u8; 3] = [ b'a', b'b', b'c' ];
pub const bin_key: [u8; 7] = [ b'a', b'b', b'c', 0, 1, 2, 0xff ];
pub fn trie_find_end<'a, T>(trie: &'a Trie<T>, key: &str) -> Option<&'a Box<TrieNode<T>>> {
    let mut node = trie.root_node.as_ref();

    for c in key.bytes() {
        if let Some(n) = node {
            node = n.next[c as usize].as_ref();
        } else {
            return None;
        }
    }

    node
}

pub fn trie_find_end_binary<'a, T>(trie: &'a Trie<T>, key: &[u8], key_length: usize) -> Option<&'a TrieNode<T>> {
    let mut node = trie.root_node.as_ref();

    for j in 0..key_length {
        if node.is_none() {
            return None;
        }

        let c = key[j] as usize;

        node = node.and_then(|n| n.next[c].as_ref());
    }

    node.map(|n| &**n)
}

pub fn trie_new<T>() -> Option<Trie<T>> {
    let mut new_trie = Trie {
        root_node: None,
    };

    Some(new_trie)
}

pub fn trie_free_list_push<T>(list: &mut Option<Box<TrieNode<T>>>, mut node: Box<TrieNode<T>>) {
    node.data = None;
    *list = Some(node);
}

pub fn trie_free_list_pop<T>(list: &mut Option<Box<TrieNode<T>>>) -> Option<Box<TrieNode<T>>> {
    if let Some(mut result) = list.take() {
        *list = result.next[0].take();
        Some(result)
    } else {
        None
    }
}

pub fn trie_num_entries<T>(trie: &Trie<T>) -> u32 {
    if let Some(root_node) = &trie.root_node {
        root_node.use_count
    } else {
        0
    }
}

pub fn trie_lookup<'a, T>(trie: &'a Trie<T>, key: &str) -> Option<&'a T> {
    let node = trie_find_end(trie, key);

    if let Some(n) = node {
        n.data.as_ref()
    } else {
        None
    }
}

pub fn trie_remove<T>(trie: &mut Trie<T>, key: &str) -> bool {
    let node = trie_find_end(trie, key);

    if let Some(node) = node {
        if node.data.is_some() {
            if let Some(mut node_mut) = trie.root_node.as_deref_mut() {
                let mut current = &mut *node_mut;
                for c in key.bytes() {
                    current = current.next[c as usize].as_deref_mut().unwrap();
                }
                current.data = None;
            } else {
                return false;
            }
        } else {
            return false;
        }
    } else {
        return false;
    }

    let mut node = &mut trie.root_node;
    let mut last_next_ptr: *mut Option<Box<TrieNode<T>>> = std::ptr::null_mut();
    let mut p = key.as_bytes().iter();

    while let Some(&c) = p.next() {
        if let Some(n) = node.as_deref_mut() {
            n.use_count -= 1;

            if n.use_count <= 0 {
                if !last_next_ptr.is_null() {
                    unsafe {
                        *last_next_ptr = None;
                    }
                }
                break;
            }

            last_next_ptr = &mut n.next[c as usize];
            node = &mut n.next[c as usize];
        } else {
            break;
        }
    }

    true
}

pub fn trie_free<T>(trie: Trie<T>) {
    let mut free_list: Option<Box<TrieNode<T>>> = None;

    if let Some(root_node) = trie.root_node {
        trie_free_list_push(&mut free_list, root_node);
    }

    while let Some(mut node) = trie_free_list_pop(&mut free_list) {
        for i in 0..256 {
            if let Some(next_node) = node.next[i].take() {
                trie_free_list_push(&mut free_list, next_node);
            }
        }
    }
}

pub fn trie_lookup_binary<'a, T>(trie: &'a Trie<T>, key: &[u8], key_length: usize) -> Option<&'a T> {
    let node = trie_find_end_binary(trie, key, key_length);

    if let Some(n) = node {
        n.data.as_ref()
    } else {
        None
    }
}

pub fn trie_insert_rollback<T: Clone>(trie: &mut Trie<T>, key: &[u8]) {
    let mut node = trie.root_node.take();
    let mut prev_ptr = &mut trie.root_node;
    let mut p = key.iter();

    while let Some(mut current_node) = node {
        let next_index = *p.next().unwrap_or(&0) as usize;
        let next_node = current_node.next[next_index].take();

        current_node.use_count -= 1;

        if current_node.use_count == 0 {
            *prev_ptr = None;
        } else {
            *prev_ptr = Some(current_node);
        }

        node = next_node;
        if let Some(ref mut prev_node) = *prev_ptr {
            prev_ptr = &mut prev_node.next[next_index];
        }
    }
}

pub fn trie_insert_binary<T: Clone>(trie: &mut Trie<T>, key: &[u8], key_length: usize, value: Option<T>) -> i32 {
    if value.is_none() {
        return 0;
    }

    if let Some(node) = trie_find_end_binary(trie, key, key_length) {
        if node.data.is_some() {
            let mut node_mut = node.clone();
            node_mut.data = value;
            return 1;
        }
    }

    let mut rover = &mut trie.root_node;
    let mut p = 0;

    while p <= key_length {
        let node = rover.take();

        let mut new_node = match node {
            Some(n) => n,
            None => {
                let new_node = TrieNode {
                    data: None,
                    use_count: 0,
                    next: [(); 256].map(|_| None),
                };
                Box::new(new_node)
            }
        };

        new_node.use_count += 1;

        if p == key_length {
            new_node.data = value;
            *rover = Some(new_node);
            break;
        }

        let c = key[p] as usize;
        let next_node = new_node.next[c].take();
        *rover = Some(new_node);
        rover = &mut (*rover).as_mut().unwrap().next[c];
        *rover = next_node;
        p += 1;
    }

    1
}

pub fn trie_insert<T: Clone>(trie: &mut Trie<T>, key: &str, value: T) -> bool {
    let mut rover = &mut trie.root_node;
    let mut p = key.bytes();

    for c in p.by_ref() {
        if let Some(node) = rover {
            // Increase the node use count
            node.use_count += 1;

            // Advance to the next node in the chain
            rover = &mut node.next[c as usize];
        } else {
            // Node does not exist, so create it
            let mut new_node = Box::new(TrieNode {
                data: None,
                use_count: 1,
                next: [(); 256].map(|_| None),
            });

            // Link in to the trie
            *rover = Some(new_node);
            rover = &mut rover.as_mut().unwrap().next[c as usize];
        }
    }

    // Set the data at the node we have reached
    if let Some(node) = rover {
        node.data = Some(value);
    }

    true
}

pub fn trie_remove_binary<T: Clone>(trie: &mut Trie<T>, key: &[u8], key_length: usize) -> i32 {
    let mut node = trie_find_end_binary(trie, key, key_length).cloned();

    if let Some(mut node) = node {
        if node.data.is_some() {
            node.data = None;
        } else {
            return 0;
        }
    } else {
        return 0;
    }

    let mut node = trie.root_node.take();
    let mut last_next_ptr = &mut trie.root_node;
    let mut p = 0;

    while let Some(mut current_node) = node {
        let c = key[p] as usize;
        let next = current_node.next[c].take();

        current_node.use_count -= 1;

        if current_node.use_count == 0 {
            *last_next_ptr = None;
        } else {
            *last_next_ptr = Some(current_node);
        }

        if p == key_length {
            break;
        } else {
            p += 1;
        }

        if last_next_ptr.is_some() {
            last_next_ptr = &mut (*last_next_ptr).as_mut().unwrap().next[c];
        }

        node = next;
    }

    1
}

