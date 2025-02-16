use test_project::compare_int::{int_compare, int_equal, IntLocation};
use test_project::compare_pointer::{pointer_compare, pointer_equal};
use test_project::compare_string::{
    string_compare, string_equal, string_nocase_compare, string_nocase_equal,
};
#[test]
pub fn test_string_nocase_compare() {
    let test1 = String::from("Apple");
    let test2 = String::from("Orange");
    let test3 = String::from("Apple");
    let test4 = String::from("Alpha");
    let test5 = String::from("bravo");
    let test6 = String::from("Charlie");

    assert!(string_nocase_compare(&test1, &test2) < 0);
    assert!(string_nocase_compare(&test2, &test1) > 0);
    assert!(string_nocase_compare(&test1, &test3) == 0);
    assert!(string_nocase_compare(&test4, &test5) < 0);
    assert!(string_nocase_compare(&test5, &test6) < 0);
}

#[test]
pub fn test_string_nocase_equal() {
    let test1 = String::from("this is a test string");
    let test2 = String::from("this is a test string ");
    let test3 = String::from("this is a test strin");
    let test4 = String::from("this is a test strinG");
    let test5 = String::from("this is a test string");

    assert!(string_nocase_equal(&test1, &test5));

    assert_eq!(string_nocase_equal(&test1, &test2), false);
    assert_eq!(string_nocase_equal(&test1, &test3), false);

    assert!(string_nocase_equal(&test1, &test4));
}

#[test]
pub fn test_pointer_equal() {
    let mut a = 0;
    let mut b = 0;

    /* Non-zero (true) if the two pointers are equal */
    assert!(pointer_equal(&a, &a));

    /* Zero (false) if the two pointers are not equal */
    assert!(!pointer_equal(&a, &b));
}

#[test]
pub fn test_int_compare() {
    let mut a = 4;
    let mut b = 8;
    let mut c = 4;

    assert!(int_compare(&a, &b) < 0);

    assert!(int_compare(&b, &a) > 0);

    assert!(int_compare(&a, &c) == 0);
}

#[test]
pub fn test_string_compare() {
    let mut test1 = String::from("Apple");
    let mut test2 = String::from("Orange");
    let mut test3 = String::from("Apple");

    assert!(string_compare(&test1, &test2) < 0);

    assert!(string_compare(&test2, &test1) > 0);

    assert!(string_compare(&test1, &test3) == 0);
}

#[test]
pub fn test_string_equal() {
    let test1 = String::from("this is a test string");
    let test2 = String::from("this is a test string ");
    let test3 = String::from("this is a test strin");
    let test4 = String::from("this is a test strinG");
    let test5 = String::from("this is a test string");

    assert!(string_equal(&test1, &test5));

    assert!(!string_equal(&test1, &test2));
    assert!(!string_equal(&test1, &test3));

    assert!(!string_equal(&test1, &test4));
}

#[test]
pub fn test_pointer_compare() {
    let mut array = [0; 5];

    assert!(pointer_compare(&array[0], &array[4]) < 0);

    assert!(pointer_compare(&array[3], &array[2]) > 0);

    assert!(pointer_compare(&array[4], &array[4]) == 0);
}

#[test]
pub fn test_int_equal() {
    let a = IntLocation(4);
    let b = IntLocation(8);
    let c = IntLocation(4);

    assert!(int_equal(&a, &c));

    assert!(!int_equal(&a, &b));
}
