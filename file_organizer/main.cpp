/*
* File Sorter CLI Tool
* --------------------------------------------------
* This program reads a JSON config file that defines a source directory,
* destination directories, and file extensions per category. It scans the
* source directory and moves files to the appropriate destination folder
* based on their extension.
*/ 

#include <iostream>
#include <fstream>
#include <filesystem>
#include <unordered_map>
#include <vector>
#include <algorithm>
#include <regex>
#include <cstdlib>
#include <nlohmann/json.hpp>  // JSON library

namespace fs = std::filesystem;
using json = nlohmann::json;

// Configuration structure to hold source directory, destination directories,
// and file extension mappings.
struct Config {
    fs::path source_dir; // Where the files are scanned from
    std::unordered_map<std::string, fs::path> dest_dirs; // Map of category → destination path
    std::unordered_map<std::string, std::vector<std::string>> extension_map; // Map of category → allowed extensions
};

// Helper function to convert a string to lowercase for case-insensitive comparison
std::string to_lower(const std::string& str) {
    std::string lower_str = str;
    std::transform(lower_str.begin(), lower_str.end(), lower_str.begin(), ::tolower);
    return lower_str;
}

// Generates a unique file path to prevent overwriting existing files
// Adds (1), (2), etc., if a file with the same name already exists
fs::path unique_name(const fs::path& dest, const fs::path& filename) {
    fs::path new_path = dest / filename;
    int counter = 1;
    while (fs::exists(new_path)) {
        fs::path stem = filename.stem(); // Filename without extension
        fs::path extension = filename.extension(); // File extension
        new_path = dest / (stem.string() + "(" + std::to_string(counter) + ")" + extension.string());
        ++counter;
    }
    return new_path;
}

// Replaces ${VARNAME} with the corresponding environment variable value
std::string expand_env_vars(const std::string& path) {
    std::regex env_pattern(R"(\$\{([^}]+)\})");
    std::smatch match;
    std::string result = path;
    while (std::regex_search(result, match, env_pattern)) {
        const char* var = std::getenv(match[1].str().c_str());
        std::string value = var ? var : "";
        result.replace(match.position(0), match.length(0), value);
    }
    return result;
}

// Function to load configuration from a JSON file
Config load_config(const std::string& filepath) {
    std::ifstream in(filepath);
    json j;
    in >> j; // Read the JSON content into the `j` object

    Config config;

    // Expand environment variable in source_dir
    std::string source_raw = j["source_dir"].get<std::string>();
    config.source_dir = expand_env_vars(source_raw);

    // Expand env variables in dest_dirs
    for (const auto& [key, val] : j["dest_dirs"].items()) {
        std::string dest_raw = val.get<std::string>();
        config.dest_dirs[key] = expand_env_vars(dest_raw);
    }

    // No need to expand for extensions
    for (const auto& [key, val] : j["extensions"].items()) {
        config.extension_map[key] = val.get<std::vector<std::string>>();
    }

    return config;
}

// Main sorting function
void sort_files(const Config& config) {

    // Iterate over every file in the source directory
    for (const auto& entry : fs::directory_iterator(config.source_dir)) {
        if (!entry.is_regular_file()) continue; // Skip non-files

        fs::path file_path = entry.path();
        std::string ext = to_lower(file_path.extension().string()); // Get file extension in lowercase

        // Check which category the extension belongs to
        for (const auto& [category, extensions] : config.extension_map) {
            if (std::find(extensions.begin(), extensions.end(), ext) != extensions.end()) {
                
                // Get the destination directory path for this category
                fs::path dest_dir = config.dest_dirs.at(category);

                // Generate a destination filename (handles duplicates)
                fs::path dest_file = unique_name(dest_dir, file_path.filename());

                try {
                    fs::create_directories(dest_dir); // Ensure directory exists
                    fs::rename(file_path, dest_file); // Move the file
                    std::cout << "Moved " << file_path.filename() << " to " << dest_dir << "\n";
                }
                catch (const std::exception& e) {
                    std::cerr << "Error moving file: " << e.what() << "\n";
                }
                break; // File moved; no need to check other categories
            }
        }
    }
}

// Entry point of the program
int main() {
    try {
        Config config = load_config("config.json"); // Load config file
        sort_files(config); // Start sorting process
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl; // Catch and print any runtime errors
        return 1;
    }
    return 0;
}
