# Windows-specific ONNX Runtime cache variables.

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded" CACHE STRING "Static CRT (/MT)")

# ONNX / Abseil static runtime flags
set(ONNX_USE_MSVC_STATIC_RUNTIME ON CACHE BOOL "")
set(protobuf_MSVC_STATIC_RUNTIME ON CACHE BOOL "")
set(ABSL_MSVC_STATIC_RUNTIME ON CACHE BOOL "")

# MSVC 14.44+ STL errors on <ciso646> in C++20; suppress it.
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /D_SILENCE_CXX20_CISO646_REMOVED_WARNING" CACHE STRING "")

set(onnxruntime_USE_DML ON CACHE BOOL "")
