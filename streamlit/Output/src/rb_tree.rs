use std::rc::Rc;
use std::cell::RefCell;
pub enum RBTreeNodeColor {
    Red,
    Black,
}

impl PartialEq for RBTreeNodeColor {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (RBTreeNodeColor::Red, RBTreeNodeColor::Red) => true,
            (RBTreeNodeColor::Black, RBTreeNodeColor::Black) => true,
            _ => false,
        }
    }
}

impl Clone for RBTreeNodeColor {
    fn clone(&self) -> Self {
        match self {
            RBTreeNodeColor::Red => RBTreeNodeColor::Red,
            RBTreeNodeColor::Black => RBTreeNodeColor::Black,
        }
    }
}

pub enum RBTreeNodeSide {
    Left,
    Right,
}

impl PartialEq for RBTreeNodeSide {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (RBTreeNodeSide::Left, RBTreeNodeSide::Left) => true,
            (RBTreeNodeSide::Right, RBTreeNodeSide::Right) => true,
            _ => false,
        }
    }
}

pub struct RBTreeNode<T: Clone + PartialEq> {
    pub color: RBTreeNodeColor,
    pub key: T,
    pub value: T,
    pub parent: Option<Rc<RefCell<RBTreeNode<T>>>>,
    pub children: [Option<Rc<RefCell<RBTreeNode<T>>>>; 2],
}

impl<T: Clone + PartialEq> Clone for RBTreeNode<T> {
    fn clone(&self) -> Self {
        RBTreeNode {
            color: self.color.clone(),
            key: self.key.clone(),
            value: self.value.clone(),
            parent: self.parent.clone(),
            children: self.children.clone(),
        }
    }
}

pub struct RBTree<T: Clone + PartialEq> {
    pub root_node: Option<Rc<RefCell<RBTreeNode<T>>>>,
    pub compare_func: fn(&T, &T) -> i32,
    pub num_nodes: i32,
}

pub const NUM_TEST_VALUES: usize = 1000;
pub static mut test_array: [i32; NUM_TEST_VALUES] = [0; NUM_TEST_VALUES];
pub fn rb_tree_node_uncle<T: Clone + PartialEq>(node: Rc<RefCell<RBTreeNode<T>>>) -> Option<Rc<RefCell<RBTreeNode<T>>>> {
    rb_tree_node_sibling(node.clone())
}

pub fn rb_tree_node_sibling<T: Clone + PartialEq>(node: Rc<RefCell<RBTreeNode<T>>>) -> Option<Rc<RefCell<RBTreeNode<T>>>> {
    let side = rb_tree_node_side(node.clone());

    match side {
        RBTreeNodeSide::Left => node.borrow().parent.as_ref().and_then(|parent| parent.borrow().children[1].clone()),
        RBTreeNodeSide::Right => node.borrow().parent.as_ref().and_then(|parent| parent.borrow().children[0].clone()),
    }
}

pub fn rb_tree_node_side<T: Clone + PartialEq>(node: Rc<RefCell<RBTreeNode<T>>>) -> RBTreeNodeSide {
    if let Some(parent) = node.borrow().parent.clone() {
        if parent.borrow().children[0].as_ref().map_or(false, |left_child| Rc::ptr_eq(&left_child, &node)) {
            return RBTreeNodeSide::Left;
        } else {
            return RBTreeNodeSide::Right;
        }
    }
    panic!("Node does not have a parent");
}

pub fn rb_tree_insert_case4<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Rc<RefCell<RBTreeNode<T>>>) {
    let mut next_node = node.clone();
    let side = rb_tree_node_side(node.clone());

    if side != rb_tree_node_side(node.borrow().parent.as_ref().unwrap().clone()) {
        next_node = node.borrow().parent.as_ref().unwrap().clone();
        rb_tree_rotate(tree, next_node.clone(), 1 - side as usize);
    }

    rb_tree_insert_case5(tree, next_node);
}

pub fn rb_tree_rotate<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Rc<RefCell<RBTreeNode<T>>>, direction: usize) -> Rc<RefCell<RBTreeNode<T>>> {
    let new_root = node.borrow().children[1 - direction].as_ref().unwrap().clone();

    rb_tree_node_replace(tree, node.clone(), Some(new_root.clone()));

    node.borrow_mut().children[1 - direction] = new_root.borrow().children[direction].clone();
    new_root.borrow_mut().children[direction] = Some(node.clone());

    node.borrow_mut().parent = Some(new_root.clone());

    if let Some(ref mut child) = node.borrow_mut().children[1 - direction] {
        child.borrow_mut().parent = Some(node.clone());
    }

    new_root
}

pub fn rb_tree_node_replace<T: Clone + PartialEq>(tree: &mut RBTree<T>, node1: Rc<RefCell<RBTreeNode<T>>>, node2: Option<Rc<RefCell<RBTreeNode<T>>>>) {
    if let Some(ref node2) = node2 {
        node2.borrow_mut().parent = node1.borrow().parent.clone();
    }

    if node1.borrow().parent.is_none() {
        tree.root_node = node2;
    } else {
        let side = rb_tree_node_side(node1.clone());
        node1.borrow().parent.as_ref().unwrap().borrow_mut().children[side as usize] = node2;
    }
}

pub fn rb_tree_insert_case5<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Rc<RefCell<RBTreeNode<T>>>) {
    let parent = node.borrow().parent.as_ref().unwrap().clone();
    let grandparent = parent.borrow().parent.as_ref().unwrap().clone();
    let side = rb_tree_node_side(node.clone());

    rb_tree_rotate(tree, grandparent.clone(), 1 - side as usize);

    parent.borrow_mut().color = RBTreeNodeColor::Black;
    grandparent.borrow_mut().color = RBTreeNodeColor::Red;
}

pub fn rb_tree_node_child<T: Clone + PartialEq>(node: &RBTreeNode<T>, side: RBTreeNodeSide) -> Option<Rc<RefCell<RBTreeNode<T>>>> {
    if side == RBTreeNodeSide::Left || side == RBTreeNodeSide::Right {
        return node.children[side as usize].clone();
    } else {
        return None;
    }
}

pub fn rb_tree_free_subtree<T: Clone + PartialEq>(node: Option<Rc<RefCell<RBTreeNode<T>>>>) {
    if let Some(n) = node {
        rb_tree_free_subtree(n.borrow().children[RBTreeNodeSide::Left as usize].clone());
        rb_tree_free_subtree(n.borrow().children[RBTreeNodeSide::Right as usize].clone());
    }
}

pub fn rb_tree_insert_case3<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Rc<RefCell<RBTreeNode<T>>>) {
    let grandparent = node.borrow().parent.as_ref().unwrap().borrow().parent.as_ref().unwrap().clone();
    let uncle = rb_tree_node_uncle(node.clone());

    if let Some(uncle) = uncle {
        if uncle.borrow().color == RBTreeNodeColor::Red {
            node.borrow_mut().parent.as_ref().unwrap().borrow_mut().color = RBTreeNodeColor::Black;
            uncle.borrow_mut().color = RBTreeNodeColor::Black;
            grandparent.borrow_mut().color = RBTreeNodeColor::Red;

            rb_tree_insert_case1(tree, grandparent);
        } else {
            rb_tree_insert_case4(tree, node);
        }
    } else {
        rb_tree_insert_case4(tree, node);
    }
}

pub fn rb_tree_insert_case2<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Rc<RefCell<RBTreeNode<T>>>) {
    if node.borrow().parent.as_ref().unwrap().borrow().color != RBTreeNodeColor::Black {
        rb_tree_insert_case3(tree, node);
    }
}

pub fn rb_tree_insert_case1<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: Rc<RefCell<RBTreeNode<T>>>) {
    if node.borrow().parent.is_none() {
        node.borrow_mut().color = RBTreeNodeColor::Black;
    } else {
        rb_tree_insert_case2(tree, node);
    }
}

pub fn rb_tree_new<T: Clone + PartialEq>(compare_func: fn(&T, &T) -> i32) -> Option<RBTree<T>> {
    let new_tree = RBTree {
        root_node: None,
        compare_func,
        num_nodes: 0,
    };

    Some(new_tree)
}

pub fn rb_tree_insert<T: Clone + PartialEq>(tree: &mut RBTree<T>, key: T, value: T) -> Option<Rc<RefCell<RBTreeNode<T>>>> {
    let node = Rc::new(RefCell::new(RBTreeNode {
        color: RBTreeNodeColor::Red,
        key: key.clone(),
        value: value.clone(),
        parent: None,
        children: [None, None],
    }));

    let mut parent = None;
    let mut rover = tree.root_node.clone();

    while let Some(current_node) = rover {
        parent = Some(current_node.clone());
        let side = if (tree.compare_func)(&value, &current_node.borrow().value) < 0 {
            RBTreeNodeSide::Left
        } else {
            RBTreeNodeSide::Right
        };
        rover = current_node.borrow().children[side as usize].clone();
    }

    if let Some(parent_node) = parent {
        node.borrow_mut().parent = Some(parent_node.clone());
        parent_node.borrow_mut().children[rb_tree_node_side(node.clone()) as usize] = Some(node.clone());
    } else {
        tree.root_node = Some(node.clone());
    }

    rb_tree_insert_case1(tree, node.clone());

    tree.num_nodes += 1;

    Some(node)
}

pub fn rb_tree_lookup_node<T: Clone + PartialEq>(tree: &RBTree<T>, key: T) -> Option<Rc<RefCell<RBTreeNode<T>>>> {
    let mut node = tree.root_node.clone();
    let mut diff: i32;

    while let Some(current_node) = node {
        let current_node_borrow = current_node.borrow();
        diff = (tree.compare_func)(&key, &current_node_borrow.key);

        if diff == 0 {
            return Some(current_node.clone());
        } else if diff < 0 {
            node = current_node_borrow.children[0].clone();
        } else {
            node = current_node_borrow.children[1].clone();
        }
    }

    None
}

pub fn rb_tree_remove_node<T: Clone + PartialEq>(tree: &mut RBTree<T>, node: &Rc<RefCell<RBTreeNode<T>>>) {
    if let Some(ref mut root) = tree.root_node {
        if Rc::ptr_eq(root, node) {
            tree.root_node = None;
        } else {
            let mut parent = node.borrow().parent.clone();
            if let Some(ref mut parent) = parent {
                let mut parent_borrowed = parent.borrow_mut();
                let side = if parent_borrowed.children[0].as_ref().map_or(false, |child| Rc::ptr_eq(child, node)) {
                    RBTreeNodeSide::Left
                } else {
                    RBTreeNodeSide::Right
                };
                parent_borrowed.children[side as usize] = None;
            }
        }
    }
    tree.num_nodes -= 1;
}

pub fn rb_tree_num_entries<T: Clone + PartialEq>(tree: &RBTree<T>) -> i32 {
    tree.num_nodes
}

pub fn rb_tree_root_node<T: Clone + PartialEq>(tree: &RBTree<T>) -> Option<Rc<RefCell<RBTreeNode<T>>>> {
    tree.root_node.clone()
}

pub fn rb_tree_node_key<T: Clone + PartialEq>(node: &RBTreeNode<T>) -> T {
    node.key.clone()
}

pub fn rb_tree_node_value<T: Clone + PartialEq>(node: Rc<RefCell<RBTreeNode<T>>>) -> T {
    node.borrow().value.clone()
}

pub fn rb_tree_free<T: Clone + PartialEq>(tree: &mut RBTree<T>) {
    rb_tree_free_subtree(tree.root_node.take());
}

pub fn rb_tree_lookup<T: Clone + PartialEq>(tree: &RBTree<T>, key: T) -> Option<T> {
    let node = rb_tree_lookup_node(tree, key);
    node.map(|n| n.borrow().value.clone())
}

fn in_order_traversal<T: Clone + PartialEq>(node: Rc<RefCell<RBTreeNode<T>>>, result: &mut Vec<T>) {
    if let Some(left) = node.borrow().children[0].clone() {
        in_order_traversal(left, result);
    }
    result.push(node.borrow().value.clone());
    if let Some(right) = node.borrow().children[1].clone() {
        in_order_traversal(right, result);
    }
}
 pub fn rb_tree_to_array<T: Clone + PartialEq>(tree: &RBTree<T>) -> Vec<T> {
    let mut result = Vec::new();
    if let Some(root) = &tree.root_node {
        in_order_traversal(root.clone(), &mut result);
    }
    result
}

pub fn rb_tree_remove<T: Clone + PartialEq>(tree: &mut RBTree<T>, key: T) -> i32 {
    let node = rb_tree_lookup_node(tree, key);

    if let Some(node) = node {
        rb_tree_remove_node(tree, &node);
        1
    } else {
        0
    }
}

