cmake_minimum_required(VERSION 3.10)
project(WhisperNetCore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(whispernet_core SHARED
    src/whisper_node.cpp
)

target_include_directories(whispernet_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
