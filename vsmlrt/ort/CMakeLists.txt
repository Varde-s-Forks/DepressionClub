cmake_minimum_required(VERSION 3.22)
project(VSORT_Package)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Options
set(ENABLE_CUDA OFF CACHE BOOL "Enable CUDA backend")
set(ENABLE_DML OFF CACHE BOOL "Enable DirectML backend")
set(ENABLE_COREML OFF CACHE BOOL "Enable CoreML support")

set(
  VAPOURSYNTH_INCLUDE_DIRECTORY
  "${CMAKE_CURRENT_SOURCE_DIR}/vapoursynth/include"
  CACHE PATH
  "Path to VapourSynth headers"
)

find_package(Protobuf REQUIRED CONFIG)
find_package(ONNX REQUIRED)
find_package(onnxruntime REQUIRED)

add_library(
  vsort
  SHARED
  vs-mlrt/vsort/vs_onnxruntime.cpp
  vs-mlrt/vsort/win32.cpp
  vs-mlrt/common/onnx_utils.cpp
  vs-mlrt/common/convert_float_to_float16.cpp
)

target_include_directories(vsort PRIVATE "${VAPOURSYNTH_INCLUDE_DIRECTORY}" "vs-mlrt/vsort" "vs-mlrt/common")
target_link_libraries(vsort PRIVATE ONNX::onnx onnxruntime::onnxruntime)
set_target_properties(
  vsort
  PROPERTIES POSITION_INDEPENDENT_CODE ON CXX_EXTENSIONS OFF CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON
)

if(ENABLE_CUDA)
  find_package(CUDAToolkit REQUIRED)
  target_compile_definitions(vsort PRIVATE ENABLE_CUDA)
  target_include_directories(vsort PRIVATE ${CUDAToolkit_INCLUDE_DIRS})
  target_link_libraries(vsort PRIVATE CUDA::cudart_static)

  if(MSVC)
    target_link_options(vsort PRIVATE "/DELAYLOAD:onnxruntime.dll" "delayimp.lib")
  endif()
endif()

if(ENABLE_DML)
  target_compile_definitions(vsort PRIVATE ENABLE_DML)
endif()

# Repair
if(WIN32)
  # Copy ONNX Runtime
  get_filename_component(_ROOT "${onnxruntime_DIR}/../../.." ABSOLUTE)
  file(GLOB _DLLS "${_ROOT}/bin/*.dll")
  # Copy CUDA providers DLL if CUDA is enabled
  if(ENABLE_CUDA)
    file(GLOB _LIB_DLLS "${_ROOT}/lib/*.dll")
    list(APPEND _DLLS ${_LIB_DLLS})
  endif()

  if(_DLLS)
    install(FILES ${_DLLS} DESTINATION "vsort")
  else()
    message(WARNING "Could not find ONNX Runtime DLLs")
  endif()

  if(ENABLE_DML)
    if(NOT DML_DIR AND DEFINED ENV{DML_DIR})
      set(DML_DIR "$ENV{DML_DIR}")
    endif()

    if(DML_DIR)
      file(TO_CMAKE_PATH "${DML_DIR}" _DML_DIR)
      find_file(_DML NAMES DirectML.dll PATHS "${_DML_DIR}/bin/x64-win" NO_DEFAULT_PATH)
    endif()

    if(_DML)
      install(FILES "${_DML}" DESTINATION "vsort")
    else()
      message(WARNING "Could not find DirectML DLL. DML_DIR='${DML_DIR}'")
    endif()
  endif()
endif()

# Copy CUDA provider shared libraries on Linux (mirrors the Windows DLL bundling above).
# These are dlopen'd at runtime by libonnxruntime.so and invisible to auditwheel.
if(UNIX AND NOT APPLE AND ENABLE_CUDA)
  get_filename_component(_ROOT "${onnxruntime_DIR}/../../.." ABSOLUTE)
  file(
    GLOB _PROVIDER_LIBS
    "${_ROOT}/lib/libonnxruntime_providers_cuda.so"
    "${_ROOT}/lib/libonnxruntime_providers_shared.so"
    "${_ROOT}/lib64/libonnxruntime_providers_cuda.so"
    "${_ROOT}/lib64/libonnxruntime_providers_shared.so"
  )
  if(_PROVIDER_LIBS)
    install(FILES ${_PROVIDER_LIBS} DESTINATION .)
  else()
    message(WARNING "Could not find ONNX Runtime CUDA provider libraries in ${_ROOT}")
  endif()
endif()

if(ENABLE_COREML)
  target_compile_definitions(vsort PRIVATE ENABLE_COREML=1)
endif()

target_include_directories(vsort PUBLIC "${PROJECT_BINARY_DIR}")

if(SKBUILD_PROJECT_VERSION)
  set(VCS_TAG "v${SKBUILD_PROJECT_VERSION}" CACHE STRING "Version from scikit-build-core")
  set(CMAKE_DISABLE_FIND_PACKAGE_Git ON)
endif()

configure_file(vs-mlrt/vsort/config.h.in config.h)

install(TARGETS vsort LIBRARY DESTINATION . RUNTIME DESTINATION .)
if(WIN32)
  file(WRITE "manifest.vs" "[VapourSynth Manifest V1]\nbm3dcpu\n")
else()
  file(WRITE "manifest.vs" "[VapourSynth Manifest V1]\nlibbm3dcpu\n")
endif()
install(FILES "manifest.vs" DESTINATION .)
