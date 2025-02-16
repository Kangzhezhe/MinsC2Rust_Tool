pub struct _BinaryHeap<T> {
    pub heap_type: BinaryHeapType,
    pub values: Vec<T>,
    pub num_values: usize,
    pub alloced_size: usize,
    pub compare_func: BinaryHeapCompareFunc<T>,
}

#[derive(PartialEq)]
pub enum BinaryHeapType {
    Min,
    Max,
}

pub type BinaryHeapCompareFunc<T> = fn(&T, &T) -> i32;

pub const NUM_TEST_VALUES: usize = 100;
pub fn binary_heap_cmp<T>(heap: &_BinaryHeap<T>, data1: &T, data2: &T) -> i32 {
    if heap.heap_type == BinaryHeapType::Min {
        (heap.compare_func)(data1, data2)
    } else {
        -(heap.compare_func)(data1, data2)
    }
}

pub fn binary_heap_new<T>(heap_type: BinaryHeapType, compare_func: BinaryHeapCompareFunc<T>) -> Option<_BinaryHeap<T>> {
    let heap = _BinaryHeap {
        heap_type,
        values: Vec::with_capacity(16),
        num_values: 0,
        alloced_size: 16,
        compare_func,
    };

    if heap.values.capacity() < 16 {
        return None;
    }

    Some(heap)
}

pub fn binary_heap_insert<T: Clone>(heap: &mut _BinaryHeap<T>, value: T) -> i32 {
    if heap.num_values >= heap.alloced_size {
        let new_size = heap.alloced_size * 2;
        let mut new_values = Vec::with_capacity(new_size);
        new_values.extend_from_slice(&heap.values);
        heap.alloced_size = new_size;
        heap.values = new_values;
    }

    let mut index = heap.num_values;
    heap.num_values += 1;

    while index > 0 {
        let parent = (index - 1) / 2;

        if binary_heap_cmp(heap, &heap.values[parent], &value) < 0 {
            break;
        } else {
            heap.values[index] = heap.values[parent].clone();
            index = parent;
        }
    }

    heap.values[index] = value;

    1
}

pub fn binary_heap_num_entries<T>(heap: &_BinaryHeap<T>) -> usize {
    heap.num_values
}

pub fn binary_heap_free<T>(heap: _BinaryHeap<T>) {
    drop(heap.values);
}

pub fn binary_heap_pop<T: Clone>(heap: &mut _BinaryHeap<T>) -> Option<T> {
    if heap.num_values == 0 {
        return None;
    }

    let result = heap.values[0].clone();
    let new_value = heap.values[heap.num_values - 1].clone();
    heap.num_values -= 1;

    let mut index = 0;

    loop {
        let child1 = index * 2 + 1;
        let child2 = index * 2 + 2;

        let mut next_index = index;

        if child1 < heap.num_values && binary_heap_cmp(heap, &new_value, &heap.values[child1]) > 0 {
            if child2 < heap.num_values && binary_heap_cmp(heap, &heap.values[child1], &heap.values[child2]) > 0 {
                next_index = child2;
            } else {
                next_index = child1;
            }
        } else if child2 < heap.num_values && binary_heap_cmp(heap, &new_value, &heap.values[child2]) > 0 {
            next_index = child2;
        } else {
            heap.values[index] = new_value;
            break;
        }

        heap.values[index] = heap.values[next_index].clone();
        index = next_index;
    }

    Some(result)
}

