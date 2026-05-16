# macOS-specific ONNX Runtime cache variables.

set(CMAKE_BUILD_TYPE Release CACHE STRING "")

# Build options
set(onnxruntime_USE_COREML ON CACHE BOOL "")
set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "")
