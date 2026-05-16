# macOS-specific ONNX Runtime cache variables.

set(CMAKE_BUILD_TYPE Release CACHE STRING "")

set(onnxruntime_ENABLE_CPU_FP16_OPS ON CACHE BOOL "")
set(onnxruntime_USE_COREML ON CACHE BOOL "")
set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "")

# Compatibility with CMake 4.x for dependencies using old CMake versions
set(CMAKE_POLICY_VERSION_MINIMUM 3.5 CACHE STRING "")
