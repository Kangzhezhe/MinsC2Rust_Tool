cmake_minimum_required(VERSION 3.10)

# 项目名称和版本
project(UnitTestFramework VERSION 1.0)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# add_definitions(-DALLOC_TESTING)

set(SOURCE_DIR ${PROJECT_SOURCE_DIR}/c-algorithms)

# 包含头文件目录
include_directories(${SOURCE_DIR}/src)
include_directories(${SOURCE_DIR}/test)

# 查找所有源文件
file(GLOB SOURCES "${SOURCE_DIR}/src/*.c")

# 添加测试
enable_testing()


# 查找所有测试文件
file(GLOB TEST_SOURCES "${SOURCE_DIR}/test/*.c")

# 分离以test-开头和不以test-开头的文件
set(TEST_FILES "")
set(NON_TEST_FILES "")

foreach(TEST_SOURCE ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SOURCE} NAME)
    if(TEST_NAME MATCHES "^test-")
        list(APPEND TEST_FILES ${TEST_SOURCE})
    else()
        list(APPEND NON_TEST_FILES ${TEST_SOURCE})
    endif()
endforeach()

message(STATUS "TEST_FILES: ${TEST_FILES}")
message(STATUS "NON_TEST_FILES: ${NON_TEST_FILES}")


# add_executable(test-arraylist ${SOURCE_DIR}/test/test-arraylist.c ${NON_TEST_FILES} ${SOURCES})

# 为每个测试文件创建一个可执行文件并添加到测试中
foreach(TEST_FILE ${TEST_FILES})
    get_filename_component(TEST_NAME ${TEST_FILE} NAME_WE)
    add_executable(${TEST_NAME} ${TEST_FILE} ${NON_TEST_FILES} ${SOURCES})
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
endforeach()
