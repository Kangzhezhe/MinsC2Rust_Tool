pub const TEST_VALUE: usize = 5000;
pub const NUM_TEST_VALUES: usize = 10000;
pub const BINOMIAL_HEAP_TYPE_MIN: BinomialHeapType = BinomialHeapType;
pub const BINOMIAL_HEAP_TYPE_MAX: BinomialHeapType = BinomialHeapType;
pub use std::rc::Rc;
pub use std::cell::RefCell;
#[derive(PartialEq, Eq, Clone, Debug)]
pub struct BinomialHeapType;
pub struct BinomialHeap {
    pub heap_type: BinomialHeapType,
    pub compare_func: BinomialHeapCompareFunc,
    pub num_values: u32,
    pub roots: Vec<Option<Rc<RefCell<BinomialTree>>>>,
    pub roots_length: u32,
}
pub struct BinomialTree {
    pub value: BinomialHeapValue,
    pub order: u16,
    pub refcount: u16,
    pub subtrees: Vec<Option<Rc<RefCell<BinomialTree>>>>,
}
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct BinomialHeapValue(pub i32);
pub type BinomialHeapCompareFunc = Rc<dyn Fn(BinomialHeapValue, BinomialHeapValue) -> i32>;
pub fn binomial_tree_unref(tree: Option<Rc<RefCell<BinomialTree>>>) {
    if let Some(tree_ref) = tree {
        let mut tree_borrowed = tree_ref.borrow_mut();
        tree_borrowed.refcount -= 1;

        if tree_borrowed.refcount == 0 {
            for subtree in &tree_borrowed.subtrees {
                binomial_tree_unref(subtree.clone());
            }
            tree_borrowed.subtrees.clear();
        }
    }
}

pub fn binomial_tree_ref(tree: &mut Option<Rc<RefCell<BinomialTree>>>) {
    if let Some(t) = tree {
        t.borrow_mut().refcount += 1;
    }
}

pub fn binomial_heap_cmp(heap: &BinomialHeap, data1: BinomialHeapValue, data2: BinomialHeapValue) -> i32 {
    if heap.heap_type == BinomialHeapType {
        return (heap.compare_func)(data1.clone(), data2.clone());
    } else {
        return -((heap.compare_func)(data1.clone(), data2.clone()));
    }
}

pub fn binomial_tree_merge(heap: &BinomialHeap, tree1: Rc<RefCell<BinomialTree>>, tree2: Rc<RefCell<BinomialTree>>) -> Option<Rc<RefCell<BinomialTree>>> {
    let mut tree1 = tree1;
    let mut tree2 = tree2;

    if binomial_heap_cmp(heap, tree1.borrow().value.clone(), tree2.borrow().value.clone()) > 0 {
        std::mem::swap(&mut tree1, &mut tree2);
    }

    let new_tree = Rc::new(RefCell::new(BinomialTree {
        value: tree1.borrow().value.clone(),
        order: tree1.borrow().order + 1,
        refcount: 0,
        subtrees: vec![None; tree1.borrow().order as usize + 1],
    }));

    for i in 0..tree1.borrow().order as usize {
        new_tree.borrow_mut().subtrees[i] = tree1.borrow().subtrees[i].clone();
    }
    new_tree.borrow_mut().subtrees[tree1.borrow().order as usize] = Some(tree2.clone());

    for subtree in new_tree.borrow().subtrees.iter() {
        if let Some(subtree) = subtree {
            binomial_tree_ref(&mut Some(subtree.clone()));
        }
    }

    Some(new_tree)
}

pub fn binomial_heap_merge_undo(new_roots: Vec<Option<Rc<RefCell<BinomialTree>>>>, count: usize) {
    for i in 0..count {
        binomial_tree_unref(new_roots.get(i).cloned().flatten());
    }
}

pub fn binomial_heap_merge(heap: &mut BinomialHeap, other: &BinomialHeap) -> i32 {
    let max = if heap.roots_length > other.roots_length {
        heap.roots_length + 1
    } else {
        other.roots_length + 1
    };

    let mut new_roots = vec![None; max as usize];
    let mut new_roots_length = 0;
    let mut carry: Option<Rc<RefCell<BinomialTree>>> = None;
    let mut new_carry: Option<Rc<RefCell<BinomialTree>>>;

    for i in 0..max {
        let mut vals = vec![None; 3];
        let mut num_vals = 0;

        if i < heap.roots_length && heap.roots[i as usize].is_some() {
            vals[num_vals] = heap.roots[i as usize].clone();
            num_vals += 1;
        }

        if i < other.roots_length && other.roots[i as usize].is_some() {
            vals[num_vals] = other.roots[i as usize].clone();
            num_vals += 1;
        }

        if carry.is_some() {
            vals[num_vals] = carry.clone();
            num_vals += 1;
        }

        if (num_vals & 1) != 0 {
            new_roots[i as usize] = vals[num_vals - 1].clone();
            if let Some(ref mut tree) = new_roots[i as usize] {
                binomial_tree_ref(&mut Some(tree.clone()));
            }
            new_roots_length = i + 1;
        } else {
            new_roots[i as usize] = None;
        }

        if (num_vals & 2) != 0 {
            new_carry = binomial_tree_merge(heap, vals[0].as_ref().unwrap().clone(), vals[1].as_ref().unwrap().clone());

            if new_carry.is_none() {
                binomial_heap_merge_undo(new_roots.clone(), i as usize);
                binomial_tree_unref(carry);
                return 0;
            }
        } else {
            new_carry = None;
        }

        binomial_tree_unref(carry);
        carry = new_carry;
        if let Some(ref mut tree) = carry {
            binomial_tree_ref(&mut Some(tree.clone()));
        }
    }

    for i in 0..heap.roots_length {
        if let Some(ref tree) = heap.roots[i as usize] {
            binomial_tree_unref(Some(tree.clone()));
        }
    }

    heap.roots = new_roots;
    heap.roots_length = new_roots_length as u32;

    1
}

pub fn binomial_heap_new(heap_type: BinomialHeapType, compare_func: BinomialHeapCompareFunc) -> Option<BinomialHeap> {
    let new_heap = BinomialHeap {
        heap_type,
        compare_func,
        num_values: 0,
        roots: Vec::new(),
        roots_length: 0,
    };

    Some(new_heap)
}

pub fn binomial_heap_num_entries(heap: &BinomialHeap) -> u32 {
    heap.num_values
}

pub fn binomial_heap_free(heap: BinomialHeap) {
    let mut heap = heap;
    for root in heap.roots.drain(..) {
        binomial_tree_unref(root);
    }
}

pub fn binomial_heap_pop(heap: &mut BinomialHeap) -> BinomialHeapValue {
    let mut fake_heap = BinomialHeap {
        heap_type: heap.heap_type.clone(),
        compare_func: heap.compare_func.clone(),
        num_values: 0,
        roots: vec![],
        roots_length: 0,
    };
    let mut least_index = u32::MAX;

    if heap.num_values == 0 {
        return BinomialHeapValue(0);
    }

    for i in 0..heap.roots_length as usize {
        if heap.roots[i].is_none() {
            continue;
        }

        if least_index == u32::MAX || binomial_heap_cmp(heap, heap.roots[i].as_ref().unwrap().borrow().value.clone(), heap.roots[least_index as usize].as_ref().unwrap().borrow().value.clone()) < 0 {
            least_index = i as u32;
        }
    }

    let least_tree = heap.roots[least_index as usize].take().unwrap();

    fake_heap.roots = std::mem::replace(&mut least_tree.borrow_mut().subtrees, vec![]);
    fake_heap.roots_length = least_tree.borrow().order as u32;

    if binomial_heap_merge(heap, &fake_heap) == 1 {
        let result = least_tree.borrow().value.clone();
        binomial_tree_unref(Some(least_tree));
        heap.num_values -= 1;
        result
    } else {
        heap.roots[least_index as usize] = Some(least_tree);
        BinomialHeapValue(0)
    }
}

pub fn binomial_heap_insert(heap: &mut BinomialHeap, value: BinomialHeapValue) -> i32 {
    let new_tree = Rc::new(RefCell::new(BinomialTree {
        value: value,
        order: 0,
        refcount: 1,
        subtrees: Vec::new(),
    }));

    // Build a fake heap structure for merging
    let fake_heap = BinomialHeap {
        heap_type: heap.heap_type.clone(),
        compare_func: heap.compare_func.clone(),
        num_values: 1,
        roots: vec![Some(new_tree.clone())],
        roots_length: 1,
    };

    // Perform the merge
    let result = binomial_heap_merge(heap, &fake_heap);

    if result != 0 {
        heap.num_values += 1;
    }

    // Remove reference to the new tree.
    binomial_tree_unref(Some(new_tree));

    result
}

