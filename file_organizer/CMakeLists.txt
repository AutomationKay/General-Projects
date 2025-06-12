cmake_minimum_required(VERSION 3.10)
project(file_organizer VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find dependencies
find_package(nlohmann_json REQUIRED)
find_package(Threads REQUIRED)

# CLI parsing
add_subdirectory(external/CLI11)

# Add source and include dirs
include_directories(include)

add_executable(file_organizer
  src/main.cpp
  src/file_utils.cpp
  src/config_loader.cpp
)

target_link_libraries(file_organizer
  PRIVATE CLI11::CLI11
          nlohmann_json::nlohmann_json
          Threads::Threads
)

# Testing
enable_testing()
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

add_executable(tests
  tests/test_file_utils.cpp
  src/file_utils.cpp
)

target_link_libraries(tests PRIVATE GTest::GTest GTest::Main nlohmann_json::nlohmann_json)
add_test(NAME file_utils_test COMMAND tests)
