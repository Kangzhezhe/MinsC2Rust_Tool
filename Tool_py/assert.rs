use std::sync::atomic::{AtomicUsize};
use std::sync::{Once, Mutex};

// 定义全局计数器
static ASSERT_COUNT: AtomicUsize = AtomicUsize::new(0);

// 初始化一次性的打印钩子
static INIT: Once = Once::new();
static PRINT_ON_EXIT: Mutex<Option<PrintOnExit>> = Mutex::new(None);

fn initialize() {
    INIT.call_once(|| {
        // 注册退出时打印的钩子
        *PRINT_ON_EXIT.lock().unwrap() = Some(PrintOnExit);
        // 在 panic 时也打印统计信息
        std::panic::set_hook(Box::new(|_| {
            print_assert_counts();
        }));
    });
}

// 打印断言统计信息
fn print_assert_counts() {
    println!(
        "Total assertions made: {}",
        ASSERT_COUNT.load(std::sync::atomic::Ordering::Relaxed)
    );
}

// 自定义退出打印器
struct PrintOnExit;

impl Drop for PrintOnExit {
    fn drop(&mut self) {
        print_assert_counts();
    }
}

// 自定义 assert! 宏
macro_rules! assert {
    ($cond:expr) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        if !$cond {
            panic!("assertion failed: {}", stringify!($cond));
        }
        print_assert_counts();
    }};
    ($cond:expr, $($arg:tt)+) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        if !$cond {
            panic!($($arg)+);
        }
        print_assert_counts();
    }};
}

// 自定义 assert_eq! 宏
macro_rules! assert_eq {
    ($left:expr, $right:expr) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left != *right {
            panic!(
                "assertion failed: (left == right)\n  left: {:?},\n right: {:?}",
                left, right
            );
        }
        print_assert_counts();
    }};
    ($left:expr, $right:expr, $($arg:tt)+) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left != *right {
            panic!(
                "assertion failed: (left == right)\n  left: {:?},\n right: {:?}: {}",
                left, right, format!($($arg)+)
            );
        }
        print_assert_counts();
    }};
}

// 自定义 assert_ne! 宏
macro_rules! assert_ne {
    ($left:expr, $right:expr) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left == *right {
            panic!(
                "assertion failed: (left != right)\n  left: {:?},\n right: {:?}",
                left, right
            );
        }
        print_assert_counts();
    }};
    ($left:expr, $right:expr, $($arg:tt)+) => {{
        initialize();
        ASSERT_COUNT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let left_val = $left; // 将左侧表达式的值存储在局部变量中
        let right_val = $right; // 将右侧表达式的值存储在局部变量中
        let left = &left_val; // 创建对局部变量的引用
        let right = &right_val; // 创建对局部变量的引用
        if *left == *right {
            panic!(
                "assertion failed: (left != right)\n  left: {:?},\n right: {:?}: {}",
                left, right, format!($($arg)+)
            );
        }
        print_assert_counts();
    }};
}