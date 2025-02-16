use test_project::avl_tree::{
    avl_tree_balance_to_root, avl_tree_free, avl_tree_free_subtree, avl_tree_insert,
    avl_tree_lookup, avl_tree_lookup_node, avl_tree_new, avl_tree_node_balance,
    avl_tree_node_child, avl_tree_node_key, avl_tree_node_parent, avl_tree_node_parent_side,
    avl_tree_node_replace, avl_tree_node_value, avl_tree_num_entries, avl_tree_root_node,
    avl_tree_rotate, avl_tree_subtree_height, avl_tree_to_array, avl_tree_to_array_add_subtree,
    avl_tree_update_height, counter, test_array, AVLTree, AVLTreeNode, AVLTreeNodeSide,
    NUM_TEST_VALUES,
};
#[test]
pub fn test_avl_tree_new() {
    let tree = avl_tree_new(int_compare).unwrap();

    assert!(avl_tree_root_node(&tree).is_none());
    assert_eq!(avl_tree_num_entries(&tree), 0);

    let mut tree = tree;
    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_lookup() {
    let mut tree = create_tree();

    for i in 0..NUM_TEST_VALUES {
        let value = avl_tree_lookup(&tree, i as i32);

        assert!(value.is_some());
        assert_eq!(*value.unwrap(), i as i32);
    }

    // Test invalid values
    let invalid_values = vec![-1, NUM_TEST_VALUES as i32 + 1, 8724897];
    for &i in &invalid_values {
        assert!(avl_tree_lookup(&tree, i).is_none());
    }

    avl_tree_free(&mut tree);
}

pub fn create_tree() -> AVLTree<i32> {
    let mut tree = avl_tree_new(int_compare).unwrap();

    for i in 0..NUM_TEST_VALUES {
        unsafe {
            test_array[i] = i as i32;
        }
        avl_tree_insert(&mut tree, unsafe { test_array[i] }, unsafe {
            test_array[i]
        });
    }

    tree
}

pub fn find_subtree_height<T: Clone>(node: &Option<Box<AVLTreeNode<T>>>) -> i32 {
    if let Some(node) = node {
        let left_height = find_subtree_height(&node.children[0]);
        let right_height = find_subtree_height(&node.children[1]);
        std::cmp::max(left_height, right_height) + 1
    } else {
        0
    }
}

pub fn validate_subtree(node: Option<&Box<AVLTreeNode<i32>>>) -> i32 {
    let mut left_height = 0;
    let mut right_height = 0;

    if let Some(node) = node {
        let left_node = avl_tree_node_child(node, AVLTreeNodeSide::AvlTreeNodeLeft);
        let right_node = avl_tree_node_child(node, AVLTreeNodeSide::AvlTreeNodeRight);

        if let Some(left_node) = left_node {
            assert_eq!(
                avl_tree_node_parent(left_node).unwrap().borrow().key,
                node.key
            );
        }

        if let Some(right_node) = right_node {
            assert_eq!(
                avl_tree_node_parent(right_node).unwrap().borrow().key,
                node.key
            );
        }

        left_height = validate_subtree(left_node);

        let key = avl_tree_node_key(node);
        assert!(*key > unsafe { counter });
        unsafe { counter = *key };

        right_height = validate_subtree(right_node);

        assert_eq!(
            avl_tree_subtree_height(&left_node.map(|n| n.clone())),
            left_height
        );
        assert_eq!(
            avl_tree_subtree_height(&right_node.map(|n| n.clone())),
            right_height
        );

        assert!(left_height - right_height < 2 && right_height - left_height < 2);
    }

    if left_height > right_height {
        left_height + 1
    } else {
        right_height + 1
    }
}

pub fn validate_tree(tree: &AVLTree<i32>) {
    let mut height = 0;
    let root_node = avl_tree_root_node(tree);

    if let Some(root_node) = root_node {
        height = find_subtree_height(&Some(root_node.clone()));
        assert_eq!(avl_tree_subtree_height(&Some(root_node.clone())), height);
    }

    unsafe {
        counter = -1;
    }
    validate_subtree(root_node);
}

#[test]
pub fn test_out_of_memory() {
    let mut tree = create_tree();

    // Simulate out-of-memory scenario by not allowing further allocations
    // In Rust, we don't have direct control over allocation limits like in C,
    // so we'll just attempt to insert and check for failure.

    for i in 10000..20000 {
        let node = avl_tree_insert(&mut tree, i, i);
        assert!(node.is_none());
        validate_tree(&tree);
    }

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_insert_lookup() {
    let mut tree = avl_tree_new(int_compare).unwrap();
    let mut local_test_array = [0; NUM_TEST_VALUES];

    /* Create a tree containing some values. Validate the
     * tree is consistent at all stages. */
    for i in 0..NUM_TEST_VALUES {
        local_test_array[i] = i as i32;
        avl_tree_insert(&mut tree, local_test_array[i], local_test_array[i]);

        assert_eq!(avl_tree_num_entries(&tree), (i + 1) as u32);
        validate_tree(&tree);
    }

    assert!(avl_tree_root_node(&tree).is_some());

    /* Check that all values can be read back again */
    for i in 0..NUM_TEST_VALUES {
        let node = avl_tree_lookup_node(&tree, i as i32).unwrap();
        let key = avl_tree_node_key(node);
        assert_eq!(*key, i as i32);
        let value = avl_tree_node_value(node);
        assert_eq!(*value, i as i32);
    }

    /* Check that invalid nodes are not found */
    let invalid_key = NUM_TEST_VALUES as i32 + 100;
    assert!(avl_tree_lookup_node(&tree, invalid_key).is_none());

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_to_array() {
    let mut tree = avl_tree_new(int_compare).unwrap();
    let entries = vec![89, 23, 42, 4, 16, 15, 8, 99, 50, 30];
    let sorted = vec![4, 8, 15, 16, 23, 30, 42, 50, 89, 99];

    for entry in entries.iter() {
        avl_tree_insert(&mut tree, entry.clone(), entry.clone());
    }

    assert_eq!(avl_tree_num_entries(&tree), entries.len() as u32);

    let array = avl_tree_to_array(&tree);

    for (i, item) in array.iter().enumerate() {
        assert_eq!(item, &sorted[i]);
    }

    avl_tree_free(&mut tree);
}

#[test]
pub fn test_avl_tree_free() {
    let mut tree = avl_tree_new(int_compare).unwrap();

    // Try freeing an empty tree
    avl_tree_free(&mut tree);

    // Create a big tree and free it
    let mut tree = create_tree();
    avl_tree_free(&mut tree);
}

pub fn int_compare(a: i32, b: i32) -> i32 {
    a.cmp(&b) as i32
}
