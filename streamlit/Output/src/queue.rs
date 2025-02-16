#[derive(Clone)]
pub struct QueueEntry<T> {
    pub data: T,
    pub prev: Option<Box<QueueEntry<T>>>,
    pub next: Option<Box<QueueEntry<T>>>,
}

#[derive(Clone)]
pub struct Queue<T> {
    pub head: Option<Box<QueueEntry<T>>>,
    pub tail: Option<Box<QueueEntry<T>>>,
}
pub fn queue_is_empty<T>(queue: &Queue<T>) -> bool {
    queue.head.is_none()
}

pub fn queue_new<T>() -> Option<Queue<T>> {
    let queue = Queue {
        head: None,
        tail: None,
    };

    Some(queue)
}

pub fn queue_pop_head<T>(queue: &mut Queue<T>) -> Option<T> {
    if queue_is_empty(queue) {
        return None;
    }

    let mut entry = queue.head.take().unwrap();
    queue.head = entry.next.take();

    let result = entry.data;

    if queue.head.is_none() {
        queue.tail = None;
    } else {
        queue.head.as_mut().unwrap().prev = None;
    }

    Some(result)
}

pub fn queue_push_head<T: Clone>(queue: &mut Queue<T>, data: T) -> bool {
    let new_entry = QueueEntry {
        data,
        prev: None,
        next: queue.head.take(),
    };

    let new_entry = Box::new(new_entry);

    match queue.head {
        None => {
            queue.head = Some(new_entry.clone());
            queue.tail = Some(new_entry);
        }
        Some(ref mut head) => {
            head.prev = Some(new_entry.clone());
            queue.head = Some(new_entry);
        }
    }

    true
}

pub fn queue_pop_tail<T>(queue: &mut Queue<T>) -> Option<T> {
    if queue_is_empty(queue) {
        return None;
    }

    let entry = queue.tail.take().unwrap();
    let result = entry.data;

    if let Some(mut new_tail) = entry.prev {
        new_tail.next = None;
        queue.tail = Some(new_tail);
    } else {
        queue.head = None;
    }

    Some(result)
}

pub fn queue_free<T>(queue: &mut Queue<T>) {
    while !queue_is_empty(queue) {
        queue_pop_head(queue);
    }
}

pub fn queue_push_tail<T: Clone>(queue: &mut Queue<T>, data: T) -> i32 {
    let mut new_entry = Box::new(QueueEntry {
        data,
        prev: queue.tail.clone(),
        next: None,
    });

    if queue.tail.is_none() {
        queue.head = Some(new_entry.clone());
        queue.tail = Some(new_entry);
    } else {
        if let Some(tail) = queue.tail.as_mut() {
            tail.next = Some(new_entry.clone());
        }
        queue.tail = Some(new_entry);
    }

    1
}

pub fn queue_peek_head<T>(queue: &Queue<T>) -> Option<&T> {
    if queue_is_empty(queue) {
        None
    } else {
        Some(&queue.head.as_ref().unwrap().data)
    }
}

pub fn queue_peek_tail<T>(queue: &Queue<T>) -> Option<&T> {
    if queue_is_empty(queue) {
        None
    } else {
        Some(&queue.tail.as_ref().unwrap().data)
    }
}
