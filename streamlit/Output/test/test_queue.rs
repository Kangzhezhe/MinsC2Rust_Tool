use test_project::queue::{
    queue_free, queue_is_empty, queue_new, queue_peek_head, queue_peek_tail, queue_pop_head,
    queue_pop_tail, queue_push_head, queue_push_tail, Queue, QueueEntry,
};

pub static variable1: i32 = 0;
pub static variable2: i32 = 0;
pub static variable3: i32 = 0;
pub static variable4: i32 = 0;
pub fn generate_queue() -> Option<Queue<i32>> {
    let mut queue = queue_new::<i32>()?;

    for _ in 0..1000 {
        queue_push_head(&mut queue, 0);
        queue_push_head(&mut queue, 0);
        queue_push_head(&mut queue, 0);
        queue_push_head(&mut queue, 0);
    }

    Some(queue)
}

#[test]
pub fn test_queue_pop_tail() {
    let mut queue = queue_new::<i32>().unwrap();

    assert!(queue_pop_tail(&mut queue).is_none());

    queue_free(&mut queue);

    let mut queue = generate_queue().unwrap();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_pop_tail(&mut queue), Some(variable1));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable2));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable3));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable4));
    }

    assert!(queue_pop_tail(&mut queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_pop_head() {
    let mut queue = queue_new::<i32>().unwrap();

    // Check popping off an empty queue
    assert!(queue_pop_head(&mut queue).is_none());

    queue_free(&mut queue);

    // Pop off all the values from the queue
    let mut queue = generate_queue().unwrap();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_pop_head(&mut queue), Some(0));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
    }

    assert!(queue_pop_head(&mut queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_push_tail() {
    let mut queue = queue_new().unwrap();

    /* Add some values */
    for _ in 0..1000 {
        queue_push_tail(&mut queue, variable1);
        queue_push_tail(&mut queue, variable2);
        queue_push_tail(&mut queue, variable3);
        queue_push_tail(&mut queue, variable4);
    }

    assert!(!queue_is_empty(&queue));

    /* Check values come out of the head properly */
    assert_eq!(queue_pop_head(&mut queue), Some(variable1));
    assert_eq!(queue_pop_head(&mut queue), Some(variable2));
    assert_eq!(queue_pop_head(&mut queue), Some(variable3));
    assert_eq!(queue_pop_head(&mut queue), Some(variable4));

    /* Check values come back out of the tail properly */
    assert_eq!(queue_pop_tail(&mut queue), Some(variable4));
    assert_eq!(queue_pop_tail(&mut queue), Some(variable3));
    assert_eq!(queue_pop_tail(&mut queue), Some(variable2));
    assert_eq!(queue_pop_tail(&mut queue), Some(variable1));

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_push_head() {
    let mut queue = queue_new().unwrap();

    /* Add some values */
    for _ in 0..1000 {
        queue_push_head(&mut queue, variable1);
        queue_push_head(&mut queue, variable2);
        queue_push_head(&mut queue, variable3);
        queue_push_head(&mut queue, variable4);
    }

    assert!(!queue_is_empty(&queue));

    /* Check values come out of the tail properly */
    assert_eq!(queue_pop_tail(&mut queue), Some(variable1));
    assert_eq!(queue_pop_tail(&mut queue), Some(variable2));
    assert_eq!(queue_pop_tail(&mut queue), Some(variable3));
    assert_eq!(queue_pop_tail(&mut queue), Some(variable4));

    /* Check values come back out of the head properly */
    assert_eq!(queue_pop_head(&mut queue), Some(variable4));
    assert_eq!(queue_pop_head(&mut queue), Some(variable3));
    assert_eq!(queue_pop_head(&mut queue), Some(variable2));
    assert_eq!(queue_pop_head(&mut queue), Some(variable1));

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_is_empty() {
    let mut queue = queue_new().unwrap();

    assert!(queue_is_empty(&queue));

    queue_push_head(&mut queue, variable1);

    assert!(!queue_is_empty(&queue));

    queue_pop_head(&mut queue);

    assert!(queue_is_empty(&queue));

    queue_push_tail(&mut queue, variable1);

    assert!(!queue_is_empty(&queue));

    queue_pop_tail(&mut queue);

    assert!(queue_is_empty(&queue));

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_peek_head() {
    let queue: Option<Queue<i32>> = queue_new();

    // Check peeking into an empty queue
    assert!(queue_peek_head(&queue.as_ref().unwrap()).is_none());

    queue_free(&mut queue.clone().unwrap());

    // Pop off all the values from the queue, making sure that peek has the correct value beforehand
    let queue: Option<Queue<i32>> = generate_queue();

    let mut queue = queue.unwrap();
    while !queue_is_empty(&queue) {
        assert_eq!(queue_peek_head(&queue), Some(&variable4));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
        assert_eq!(queue_peek_head(&queue), Some(&variable4));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
        assert_eq!(queue_peek_head(&queue), Some(&variable4));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
        assert_eq!(queue_peek_head(&queue), Some(&variable4));
        assert_eq!(queue_pop_head(&mut queue), Some(0));
    }

    assert!(queue_peek_head(&queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_peek_tail() {
    let mut queue = queue_new::<i32>().unwrap();

    assert!(queue_peek_tail(&queue).is_none());

    queue_free(&mut queue);

    let mut queue = generate_queue().unwrap();

    while !queue_is_empty(&queue) {
        assert_eq!(queue_peek_tail(&queue), Some(&variable1));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable1));
        assert_eq!(queue_peek_tail(&queue), Some(&variable2));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable2));
        assert_eq!(queue_peek_tail(&queue), Some(&variable3));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable3));
        assert_eq!(queue_peek_tail(&queue), Some(&variable4));
        assert_eq!(queue_pop_tail(&mut queue), Some(variable4));
    }

    assert!(queue_peek_tail(&queue).is_none());

    queue_free(&mut queue);
}

#[test]
pub fn test_queue_new_free() {
    let mut _i: i32;

    /* Create and destroy a queue */
    let mut queue = queue_new::<&'static i32>().unwrap();
    queue_free(&mut queue);

    /* Add lots of values and then destroy */
    let mut queue = queue_new::<&'static i32>().unwrap();
    for _i in 0..1000 {
        queue_push_head(&mut queue, &variable1);
    }
    queue_free(&mut queue);
}
