// config_loader.hpp
#pragma once
#include <string>
#include <map>

struct Config {
    std::string source_dir;
    std::map<std::string, std::string> dest_dirs;
};

Config load_config(const std::string& path);
