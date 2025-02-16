use test_project::hash_int::{int_hash, IntLocation};
use test_project::hash_pointer::pointer_hash;
use test_project::hash_string::{string_hash, string_nocase_hash};

pub const NUM_TEST_VALUES: usize = 200;
#[test]
pub fn test_int_hash() {
    let mut array = vec![0; NUM_TEST_VALUES];

    /* Initialise all entries in the array */
    for i in 0..NUM_TEST_VALUES {
        array[i] = i as i32;
    }

    /* Check hashes are never the same */
    for i in 0..NUM_TEST_VALUES {
        for j in i + 1..NUM_TEST_VALUES {
            assert!(int_hash(IntLocation(array[i])) != int_hash(IntLocation(array[j])));
        }
    }

    /* Hashes of two variables containing the same value are the same */
    let mut i = 5000;
    let mut j = 5000;

    assert!(int_hash(IntLocation(i)) == int_hash(IntLocation(j)));
}

#[test]
pub fn test_pointer_hash() {
    let mut array: Vec<std::rc::Rc<i32>> = vec![std::rc::Rc::new(0); NUM_TEST_VALUES];

    for i in 0..NUM_TEST_VALUES {
        array[i] = std::rc::Rc::new(0);
    }

    for i in 0..NUM_TEST_VALUES {
        for j in (i + 1)..NUM_TEST_VALUES {
            assert!(pointer_hash(array[i].clone()) != pointer_hash(array[j].clone()));
        }
    }
}

#[test]
pub fn test_string_hash() {
    let test1: &str = "this is a test";
    let test2: &str = "this is a tesu";
    let test3: &str = "this is a test ";
    let test4: &str = "this is a test";
    let test5: &str = "This is a test";

    assert!(string_hash(test1) != string_hash(test2));
    assert!(string_hash(test1) != string_hash(test3));
    assert!(string_hash(test1) != string_hash(test5));
    assert!(string_hash(test1) == string_hash(test4));
}

#[test]
pub fn test_string_nocase_hash() {
    let test1: String = String::from("this is a test");
    let test2: String = String::from("this is a tesu");
    let test3: String = String::from("this is a test ");
    let test4: String = String::from("this is a test");
    let test5: String = String::from("This is a test");

    assert!(string_nocase_hash(&test1) != string_nocase_hash(&test2));
    assert!(string_nocase_hash(&test1) != string_nocase_hash(&test3));
    assert!(string_nocase_hash(&test1) == string_nocase_hash(&test5));
    assert!(string_nocase_hash(&test1) == string_nocase_hash(&test4));
}
