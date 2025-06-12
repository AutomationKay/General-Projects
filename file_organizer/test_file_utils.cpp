// tests/test_file_utils.cpp
#include "file_utils.hpp"
#include <gtest/gtest.h>
#include <filesystem>

namespace fs = std::filesystem;

TEST(FileUtils, UniqueNameCreatesNew) {
    const std::string dest = "testdir";
    fs::create_directory(dest);
    std::ofstream(dest + "/file.txt");
    auto name = unique_name(dest, "file.txt");
    EXPECT_EQ(name, "file(1).txt");
    fs::remove_all(dest);
}
