use std::cell::RefCell;
use std::rc::Rc;

pub const NUM_TEST_VALUES: usize = 1000;
pub static mut test_array: [i32; NUM_TEST_VALUES] = [0; NUM_TEST_VALUES];
pub static mut counter: i32 = 0;

pub enum AVLTreeNodeSide {
    AvlTreeNodeLeft,
    AvlTreeNodeRight,
}

impl Clone for AVLTreeNodeSide {
    fn clone(&self) -> Self {
        match self {
            AVLTreeNodeSide::AvlTreeNodeLeft => AVLTreeNodeSide::AvlTreeNodeLeft,
            AVLTreeNodeSide::AvlTreeNodeRight => AVLTreeNodeSide::AvlTreeNodeRight,
        }
    }
}

pub struct AVLTreeNode<T: Clone> {
    pub children: [Option<Box<AVLTreeNode<T>>>; 2],
    pub parent: Option<Rc<RefCell<AVLTreeNode<T>>>>,
    pub key: T,
    pub value: T,
    pub height: i32,
}

impl<T: Clone> Clone for AVLTreeNode<T> {
    fn clone(&self) -> Self {
        AVLTreeNode {
            children: self.children.clone(),
            parent: self.parent.clone(),
            key: self.key.clone(),
            value: self.value.clone(),
            height: self.height,
        }
    }
}

pub struct AVLTree<T: Clone> {
    pub root_node: Option<Box<AVLTreeNode<T>>>,
    pub compare_func: fn(T, T) -> i32,
    pub num_nodes: u32,
}

pub fn avl_tree_node_child<T: Clone>(
    node: &AVLTreeNode<T>,
    side: AVLTreeNodeSide,
) -> Option<&Box<AVLTreeNode<T>>> {
    match side {
        AVLTreeNodeSide::AvlTreeNodeLeft | AVLTreeNodeSide::AvlTreeNodeRight => {
            node.children[side as usize].as_ref()
        }
    }
}

pub fn avl_tree_free_subtree<T: Clone>(node: Option<Box<AVLTreeNode<T>>>) {
    if let Some(mut n) = node {
        avl_tree_free_subtree(n.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize].take());
        avl_tree_free_subtree(n.children[AVLTreeNodeSide::AvlTreeNodeRight as usize].take());
    }
}

pub fn avl_tree_subtree_height<T: Clone>(node: &Option<Box<AVLTreeNode<T>>>) -> i32 {
    if let Some(n) = node {
        n.height
    } else {
        0
    }
}

pub fn avl_tree_node_parent<T: Clone>(
    node: &AVLTreeNode<T>,
) -> Option<Rc<RefCell<AVLTreeNode<T>>>> {
    node.parent.clone()
}

pub fn avl_tree_node_key<T: Clone>(node: &AVLTreeNode<T>) -> &T {
    &node.key
}

pub fn avl_tree_to_array_add_subtree<T: Clone>(
    subtree: &Option<Box<AVLTreeNode<T>>>,
    array: &mut [T],
    index: &mut usize,
) {
    if let Some(node) = subtree {
        avl_tree_to_array_add_subtree(&node.children[0], array, index);
        array[*index] = node.key.clone();
        *index += 1;
        avl_tree_to_array_add_subtree(&node.children[1], array, index);
    }
}

pub fn avl_tree_node_parent_side<T: Clone>(node: &AVLTreeNode<T>) -> AVLTreeNodeSide {
    if let Some(parent) = &node.parent {
        let parent_borrowed = parent.borrow();
        if parent_borrowed.children[0].as_ref().map_or(false, |child| {
            child.as_ref() as *const AVLTreeNode<T> == node
        }) {
            return AVLTreeNodeSide::AvlTreeNodeLeft;
        } else if parent_borrowed.children[1].as_ref().map_or(false, |child| {
            child.as_ref() as *const AVLTreeNode<T> == node
        }) {
            return AVLTreeNodeSide::AvlTreeNodeRight;
        }
    }
    panic!("Node does not have a valid parent or is not a child of its parent");
}

pub fn avl_tree_update_height<T: Clone>(node: &mut AVLTreeNode<T>) {
    let left_height =
        avl_tree_subtree_height(&node.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize]);
    let right_height =
        avl_tree_subtree_height(&node.children[AVLTreeNodeSide::AvlTreeNodeRight as usize]);

    if left_height > right_height {
        node.height = left_height + 1;
    } else {
        node.height = right_height + 1;
    }
}

pub fn avl_tree_node_replace<T: Clone>(
    tree: &mut AVLTree<T>,
    node1: &mut AVLTreeNode<T>,
    node2: Option<&AVLTreeNode<T>>,
) {
    let side;

    if let Some(node2) = node2 {
        let node2_clone = node2.clone();
        if let Some(parent) = node1.parent.clone() {
            let mut parent_borrowed = parent.borrow_mut();
            side = avl_tree_node_parent_side(node1);
            parent_borrowed.children[side as usize] = Some(Box::new(node2_clone));

            avl_tree_update_height(&mut *parent_borrowed);
        }
    }

    if node1.parent.is_none() {
        tree.root_node = node2.cloned().map(|n| Box::new(n));
    }
}

pub fn avl_tree_rotate<T: Clone>(
    tree: &mut AVLTree<T>,
    node: &mut AVLTreeNode<T>,
    direction: AVLTreeNodeSide,
) -> Option<Box<AVLTreeNode<T>>> {
    let direction_index = direction as usize;
    let new_root = node.children[1 - direction_index].take();

    if let Some(mut new_root) = new_root {
        avl_tree_node_replace(tree, node, Some(&*new_root));

        node.children[1 - direction_index] = new_root.children[direction_index].take();
        new_root.children[direction_index] = Some(Box::new(node.clone()));

        let node_clone = node.clone();
        node.parent = new_root.parent.take();
        new_root.parent = Some(Rc::new(RefCell::new(*new_root.clone())));

        if let Some(child) = node.children[1 - direction_index].as_mut() {
            child.parent = Some(Rc::new(RefCell::new(node_clone)));
        }

        avl_tree_update_height(&mut *new_root);
        avl_tree_update_height(node);

        Some(new_root)
    } else {
        None
    }
}

pub fn avl_tree_node_balance<'a, T: Clone>(
    tree: &'a mut AVLTree<T>,
    node: &'a mut AVLTreeNode<T>,
) -> &'a mut AVLTreeNode<T> {
    let left_subtree = &node.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize];
    let right_subtree = &node.children[AVLTreeNodeSide::AvlTreeNodeRight as usize];
    let diff = avl_tree_subtree_height(right_subtree) - avl_tree_subtree_height(left_subtree);

    if diff >= 2 {
        let child = node.children[AVLTreeNodeSide::AvlTreeNodeRight as usize]
            .as_mut()
            .unwrap();

        if avl_tree_subtree_height(&child.children[AVLTreeNodeSide::AvlTreeNodeRight as usize])
            < avl_tree_subtree_height(&child.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize])
        {
            avl_tree_rotate(tree, child, AVLTreeNodeSide::AvlTreeNodeRight);
        }

        let rotated_node = avl_tree_rotate(tree, node, AVLTreeNodeSide::AvlTreeNodeLeft).unwrap();
        *node = *rotated_node;
    } else if diff <= -2 {
        let child = node.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize]
            .as_mut()
            .unwrap();

        if avl_tree_subtree_height(&child.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize])
            < avl_tree_subtree_height(&child.children[AVLTreeNodeSide::AvlTreeNodeRight as usize])
        {
            avl_tree_rotate(tree, child, AVLTreeNodeSide::AvlTreeNodeLeft);
        }

        let rotated_node = avl_tree_rotate(tree, node, AVLTreeNodeSide::AvlTreeNodeRight).unwrap();
        *node = *rotated_node;
    }

    avl_tree_update_height(node);
    node
}

pub fn avl_tree_balance_to_root<T: Clone>(tree: &mut AVLTree<T>, node: &mut AVLTreeNode<T>) {
    let mut rover = Some(Rc::new(RefCell::new(node.clone())));

    while let Some(current_rover) = rover {
        let mut current_rover_borrowed = current_rover.borrow_mut();

        // Balance this node if necessary
        let balanced_node = avl_tree_node_balance(tree, &mut *current_rover_borrowed);
        rover = balanced_node.parent.clone();

        // Go to this node's parent
        rover = rover.map(|parent| Rc::clone(&parent));
    }
}

pub fn avl_tree_new<T: Clone>(compare_func: fn(T, T) -> i32) -> Option<AVLTree<T>> {
    let new_tree = AVLTree {
        root_node: None,
        compare_func,
        num_nodes: 0,
    };

    Some(new_tree)
}

pub fn avl_tree_root_node<T: Clone>(tree: &AVLTree<T>) -> Option<&Box<AVLTreeNode<T>>> {
    tree.root_node.as_ref()
}

pub fn avl_tree_insert<T: Clone>(
    tree: &mut AVLTree<T>,
    key: T,
    value: T,
) -> Option<Box<AVLTreeNode<T>>> {
    let mut rover = &mut tree.root_node;
    let mut previous_node = None;

    while let Some(node) = rover {
        previous_node = Some(Rc::downgrade(&node.parent.as_ref().unwrap_or(&Rc::new(
            RefCell::new(AVLTreeNode {
                children: [None, None],
                parent: None,
                key: node.key.clone(),
                value: node.value.clone(),
                height: 1,
            }),
        ))));

        if (tree.compare_func)(key.clone(), node.key.clone()) < 0 {
            rover = &mut node.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize];
        } else {
            rover = &mut node.children[AVLTreeNodeSide::AvlTreeNodeRight as usize];
        }
    }

    let new_node = Box::new(AVLTreeNode {
        children: [None, None],
        parent: previous_node.map(|weak| weak.upgrade().unwrap()),
        key,
        value,
        height: 1,
    });

    *rover = Some(new_node.clone());

    if let Some(parent) = &new_node.parent {
        avl_tree_balance_to_root(tree, &mut *parent.borrow_mut());
    }

    tree.num_nodes += 1;

    Some(new_node)
}

pub fn avl_tree_lookup_node<T: Clone>(tree: &AVLTree<T>, key: T) -> Option<&AVLTreeNode<T>> {
    let mut node = tree.root_node.as_ref();

    while let Some(n) = node {
        let diff = (tree.compare_func)(key.clone(), n.key.clone());

        if diff == 0 {
            return Some(n);
        } else if diff < 0 {
            node = n.children[AVLTreeNodeSide::AvlTreeNodeLeft as usize].as_ref();
        } else {
            node = n.children[AVLTreeNodeSide::AvlTreeNodeRight as usize].as_ref();
        }
    }

    None
}

pub fn avl_tree_num_entries<T: Clone>(tree: &AVLTree<T>) -> u32 {
    tree.num_nodes
}

pub fn avl_tree_free<T: Clone>(tree: &mut AVLTree<T>) {
    avl_tree_free_subtree(tree.root_node.take());
}

pub fn avl_tree_node_value<T: Clone>(node: &AVLTreeNode<T>) -> &T {
    &node.value
}

pub fn avl_tree_lookup<T: Clone>(tree: &AVLTree<T>, key: T) -> Option<&T> {
    let node = avl_tree_lookup_node(tree, key);

    if let Some(n) = node {
        Some(&n.value)
    } else {
        None
    }
}

pub fn avl_tree_to_array<T: Clone>(tree: &AVLTree<T>) -> Vec<T> {
    let mut array = vec![tree.root_node.as_ref().unwrap().key.clone(); tree.num_nodes as usize];
    let mut index = 0;

    /* Add all keys */
    avl_tree_to_array_add_subtree(&tree.root_node, &mut array, &mut index);

    array
}

pub fn avl_tree_node_get_replacement<T: Clone>(
    tree: &mut AVLTree<T>,
    node: &mut AVLTreeNode<T>,
) -> Option<Rc<RefCell<AVLTreeNode<T>>>> {
    let mut left_subtree = node.children[0].clone();
    let mut right_subtree = node.children[1].clone();
    let mut result: Option<Rc<RefCell<AVLTreeNode<T>>>> = None;
    let mut child: Option<Box<AVLTreeNode<T>>> = None;
    let left_height;
    let right_height;
    let side;

    if left_subtree.is_none() && right_subtree.is_none() {
        return None;
    }

    left_height = avl_tree_subtree_height(&left_subtree);
    right_height = avl_tree_subtree_height(&right_subtree);

    if left_height < right_height {
        side = 1;
    } else {
        side = 0;
    }

    result = left_subtree
        .or(right_subtree)
        .map(|n| Rc::new(RefCell::new(*n)));

    while result.as_ref().unwrap().borrow().children[1 - side].is_some() {
        let next_result = result.as_ref().unwrap().borrow().children[1 - side].clone();
        result = next_result.map(|n| Rc::new(RefCell::new(*n)));
    }

    if let Some(res) = result.as_ref() {
        child = res.borrow().children[side].clone();
        avl_tree_node_replace(
            tree,
            &mut res.borrow_mut(),
            child.as_ref().map(|n| n.as_ref()),
        );
        if let Some(ref mut res_borrowed) = result {
            avl_tree_update_height(
                &mut res_borrowed
                    .borrow_mut()
                    .parent
                    .as_ref()
                    .unwrap()
                    .borrow_mut(),
            );
        }
    }

    result
}

pub fn int_compare(a: i32, b: i32) -> i32 {
    a.cmp(&b) as i32
}
