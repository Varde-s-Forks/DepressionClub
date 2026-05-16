# macOS-specific ONNX Runtime cache variables.

set(CMAKE_BUILD_TYPE Release CACHE STRING "")

set(onnxruntime_ENABLE_CPU_FP16_OPS ON CACHE BOOL "")
set(onnxruntime_USE_COREML ON CACHE BOOL "")
set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "")
