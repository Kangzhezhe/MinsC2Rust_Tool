use std::cell::RefCell;
use std::rc::Rc;
use test_project::rb_tree::{
    rb_tree_free, rb_tree_free_subtree, rb_tree_insert, rb_tree_insert_case1, rb_tree_insert_case2,
    rb_tree_insert_case3, rb_tree_insert_case4, rb_tree_insert_case5, rb_tree_lookup,
    rb_tree_lookup_node, rb_tree_new, rb_tree_node_child, rb_tree_node_replace,
    rb_tree_node_sibling, rb_tree_node_side, rb_tree_node_uncle, rb_tree_node_value,
    rb_tree_num_entries, rb_tree_remove, rb_tree_remove_node, rb_tree_root_node, rb_tree_rotate,
    rb_tree_to_array, test_array, RBTree, RBTreeNode, RBTreeNodeColor, RBTreeNodeSide,
    NUM_TEST_VALUES,
};
pub fn create_tree() -> Option<RBTree<i32>> {
    let int_compare = |a: &i32, b: &i32| a.cmp(b) as i32;
    let mut tree = rb_tree_new(int_compare)?;

    for i in 0..NUM_TEST_VALUES {
        unsafe {
            test_array[i] = i as i32;
        }
        rb_tree_insert(&mut tree, unsafe { test_array[i] }, unsafe {
            test_array[i]
        });
    }

    Some(tree)
}

pub fn validate_tree<T: Clone + PartialEq>(tree: &RBTree<T>) {}

pub fn find_subtree_height<T: Clone + PartialEq>(node: Option<Rc<RefCell<RBTreeNode<T>>>>) -> i32 {
    if let Some(n) = node {
        let left_subtree = rb_tree_node_child(&n.borrow(), RBTreeNodeSide::Left);
        let right_subtree = rb_tree_node_child(&n.borrow(), RBTreeNodeSide::Right);
        let left_height = find_subtree_height(left_subtree);
        let right_height = find_subtree_height(right_subtree);

        if left_height > right_height {
            return left_height + 1;
        } else {
            return right_height + 1;
        }
    } else {
        return 0;
    }
}

#[test]
pub fn test_rb_tree_free() {
    let mut tree: Option<RBTree<i32>>;

    /* Try freeing an empty tree */

    let int_compare = |a: &i32, b: &i32| a.cmp(b) as i32;
    tree = rb_tree_new(int_compare);
    if let Some(mut t) = tree {
        rb_tree_free(&mut t);
    }

    /* Create a big tree and free it */

    tree = create_tree();
    if let Some(mut t) = tree {
        rb_tree_free(&mut t);
    }
}

#[test]
pub fn test_rb_tree_lookup() {
    let mut tree = create_tree().expect("Failed to create tree");

    for i in 0..NUM_TEST_VALUES {
        let value = rb_tree_lookup(&tree, i as i32);

        assert!(value.is_some());
        assert_eq!(value.unwrap(), i as i32);
    }

    let invalid_values = vec![-1, NUM_TEST_VALUES as i32 + 1, 8724897];

    for &i in &invalid_values {
        let value = rb_tree_lookup(&tree, i);
        assert!(value.is_none());
    }

    rb_tree_free(&mut tree);
}

#[test]
pub fn test_rb_tree_new() {
    let mut tree: Option<RBTree<i32>>;

    tree = rb_tree_new(int_compare);

    assert!(tree.is_some());
    assert!(rb_tree_root_node(tree.as_ref().unwrap()).is_none());
    assert!(rb_tree_num_entries(tree.as_ref().unwrap()) == 0);

    rb_tree_free(tree.as_mut().unwrap());
}

#[test]
pub fn test_out_of_memory() {
    let mut tree = create_tree().expect("Failed to create tree");

    // Try to add some more nodes and verify that this fails.
    for i in 10000..20000 {
        let node = rb_tree_insert(&mut tree, i, i);
        assert!(node.is_none());
        validate_tree(&tree);
    }

    rb_tree_free(&mut tree);
}

#[test]
pub fn test_rb_tree_to_array() {
    let mut tree = rb_tree_new(int_compare).unwrap();
    let entries = vec![89, 23, 42, 4, 16, 15, 8, 99, 50, 30];
    let sorted = vec![4, 8, 15, 16, 23, 30, 42, 50, 89, 99];
    let num_entries = entries.len();

    for i in 0..num_entries {
        rb_tree_insert(&mut tree, entries[i], entries[i]);
    }

    assert_eq!(rb_tree_num_entries(&tree), num_entries as i32);

    let array = rb_tree_to_array(&tree);

    for i in 0..num_entries {
        assert_eq!(array[i], sorted[i]);
    }

    rb_tree_free(&mut tree);
}

#[test]
pub fn test_rb_tree_child() {
    let mut tree = rb_tree_new(int_compare).unwrap();
    let values = vec![1, 2, 3];

    for value in values.iter() {
        rb_tree_insert(&mut tree, *value, *value);
    }

    let root = rb_tree_root_node(&tree).unwrap();
    let p = rb_tree_node_value(root.clone());
    assert_eq!(p, 2);

    let left = rb_tree_node_child(&root.borrow(), RBTreeNodeSide::Left).unwrap();
    let p = rb_tree_node_value(left.clone());
    assert_eq!(p, 1);

    let right = rb_tree_node_child(&root.borrow(), RBTreeNodeSide::Right).unwrap();
    let p = rb_tree_node_value(right.clone());
    assert_eq!(p, 3);

    assert!(rb_tree_node_child(&root.borrow(), RBTreeNodeSide::Right).is_some());
    assert!(rb_tree_node_child(&root.borrow(), RBTreeNodeSide::Left).is_some());

    rb_tree_free(&mut tree);
}

#[test]
pub fn test_rb_tree_remove() {
    let mut tree = create_tree().expect("Failed to create tree");

    // Try removing invalid entries
    let mut i = NUM_TEST_VALUES + 100;
    assert!(rb_tree_remove(&mut tree, i as i32) == 0);
    i = 0;
    assert!(rb_tree_remove(&mut tree, i as i32) == 0);

    // Delete the nodes from the tree
    let mut expected_entries = NUM_TEST_VALUES as i32;

    // This looping arrangement causes nodes to be removed in a
    // randomish fashion from all over the tree.
    for x in 0..10 {
        for y in 0..10 {
            for z in 0..10 {
                let value = z * 100 + (9 - y) * 10 + x;
                assert!(rb_tree_remove(&mut tree, value as i32) != 0);
                validate_tree(&tree);
                expected_entries -= 1;
                assert!(rb_tree_num_entries(&tree) == expected_entries);
            }
        }
    }

    // All entries removed, should be empty now
    assert!(rb_tree_root_node(&tree).is_none());

    rb_tree_free(&mut tree);
}

pub fn int_compare(a: &i32, b: &i32) -> i32 {
    a.cmp(b) as i32
}
