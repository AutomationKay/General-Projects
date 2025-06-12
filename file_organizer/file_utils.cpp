// file_utils.cpp
#include "file_utils.hpp"
#include <filesystem>

namespace fs = std::filesystem;

std::string unique_name(const std::string& dest, const std::string& name) {
    fs::path p(dest);
    fs::path file(name);
    auto base = file.stem().string();
    auto ext = file.extension().string();

    int counter = 1;
    fs::path target = p / file;
    while (fs::exists(target)) {
        target = p / fs::path(base + "(" + std::to_string(counter++) + ")" + ext);
    }
    return target.filename().string();
}

void move_file(const std::string& dest, const std::string& src) {
    fs::path s(src);
    auto dest_path = fs::path(dest) / s.filename();
    auto new_name = unique_name(dest, s.filename().string());
    fs::rename(s, fs::path(dest) / new_name);
}
