// config_loader.cpp
#include "config_loader.hpp"
#include <nlohmann/json.hpp>
#include <fstream>

Config load_config(const std::string& path) {
    nlohmann::json j;
    std::ifstream in(path);
    in >> j;

    Config cfg;
    cfg.source_dir = j.at("source_dir").get<std::string>();

    for (auto& [key, val] : j.at("dest_dirs").items()) {
        cfg.dest_dirs[key] = val.get<std::string>();
    }
    return cfg;
}
