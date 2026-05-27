cmake_minimum_required(VERSION 3.22)
project(VSTRT_Package)

# === C++ Standard & Options ===
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# === TensorRT Version Detection ===
find_path(
  TENSORRT_INCLUDE_DIR
  NvInferVersion.h
  HINTS "${TENSORRT_HOME}/include" "$ENV{TENSORRT_HOME}/include"
  PATHS "/usr/include" "/usr/local/include"
)

if(TENSORRT_INCLUDE_DIR)
  get_filename_component(_TENSORRT_HOME "${TENSORRT_INCLUDE_DIR}" DIRECTORY)
  file(READ "${TENSORRT_INCLUDE_DIR}/NvInferVersion.h" _VERSION_CONTENT)
  if(_VERSION_CONTENT MATCHES "#define TRT_MAJOR_ENTERPRISE ([0-9]+)")
    set(TRT_MAJOR "${CMAKE_MATCH_1}")
  endif()
  if(_VERSION_CONTENT MATCHES "#define TRT_MINOR_ENTERPRISE ([0-9]+)")
    set(TRT_MINOR "${CMAKE_MATCH_1}")
  endif()
endif()

if(NOT DEFINED TRT_MAJOR OR NOT DEFINED TRT_MINOR)
  message(
    FATAL_ERROR
    "Could not find or parse TensorRT version from NvInferVersion.h (TENSORRT_HOME: ${TENSORRT_HOME}, ENV: $ENV{TENSORRT_HOME})"
  )
endif()

message(STATUS "TensorRT Version inferred: ${TRT_MAJOR}.${TRT_MINOR}")

set(TENSORRT_LIBRARY_SUFFIX "" CACHE STRING "TensorRT library suffix")
if(WIN32 AND NOT TENSORRT_LIBRARY_SUFFIX)
  set(TENSORRT_LIBRARY_SUFFIX "_${TRT_MAJOR}")
endif()

set(
  VAPOURSYNTH_INCLUDE_DIRECTORY
  "${CMAKE_CURRENT_SOURCE_DIR}/vapoursynth/include"
  CACHE PATH
  "Path to VapourSynth headers"
)

if(SKBUILD_PROJECT_VERSION)
  set(VCS_TAG "v${SKBUILD_PROJECT_VERSION}" CACHE STRING "Version from scikit-build-core")
  set(CMAKE_DISABLE_FIND_PACKAGE_Git ON)
endif()

# === Dependencies ===
find_package(CUDAToolkit REQUIRED)

# === Target Definition & Configuration ===
add_library(vstrt SHARED vs-mlrt/vstrt/vs_tensorrt.cpp vs-mlrt/vstrt/win32.cpp)

set_target_properties(
  vstrt
  PROPERTIES POSITION_INDEPENDENT_CODE ON CXX_EXTENSIONS OFF CXX_STANDARD 20 CXX_STANDARD_REQUIRED ON
)

if(UNIX)
  if(APPLE)
    set_target_properties(vstrt PROPERTIES INSTALL_RPATH "@loader_path")
  else()
    set_target_properties(vstrt PROPERTIES INSTALL_RPATH "$ORIGIN")
  endif()
endif()

target_include_directories(
  vstrt
  PRIVATE "${VAPOURSYNTH_INCLUDE_DIRECTORY}" "vs-mlrt/vstrt" "vs-mlrt/common" ${CUDAToolkit_INCLUDE_DIRS}
  PUBLIC "${PROJECT_BINARY_DIR}"
)

target_compile_definitions(vstrt PRIVATE USE_NVINFER_PLUGIN)

configure_file(vs-mlrt/vstrt/config.h.in config.h)

# === Link Libraries Setup ===
target_link_libraries(vstrt PRIVATE "nvinfer${TENSORRT_LIBRARY_SUFFIX}" CUDA::cudart_static)

if(MSVC)
  target_link_options(vstrt PRIVATE "/DELAYLOAD:nvinfer${TENSORRT_LIBRARY_SUFFIX}.dll" "delayimp.lib")
endif()

# Configure TensorRT home directory & paths
if(DEFINED ENV{TENSORRT_HOME})
  file(TO_CMAKE_PATH "$ENV{TENSORRT_HOME}" _TENSORRT_HOME)
  target_include_directories(vstrt PRIVATE "${_TENSORRT_HOME}/include")
  target_link_directories(vstrt PRIVATE "${_TENSORRT_HOME}/lib")
  message(STATUS "Using TENSORRT_HOME: ${_TENSORRT_HOME}")
else()
  message(WARNING "TENSORRT_HOME not set")
endif()

target_link_libraries(vstrt PRIVATE "nvinfer_plugin${TENSORRT_LIBRARY_SUFFIX}")
if(MSVC)
  target_link_options(vstrt PRIVATE "/DELAYLOAD:nvinfer_plugin${TENSORRT_LIBRARY_SUFFIX}.dll")
endif()

# === Packaging & Installation ===
install(TARGETS vstrt LIBRARY DESTINATION . RUNTIME DESTINATION .)

# Helper runtime DLL/SO copying/installing logic
if(WIN32)
  file(
    GLOB _DLLS
    "${_TENSORRT_HOME}/bin/nvinfer${TENSORRT_LIBRARY_SUFFIX}.dll"
    "${_TENSORRT_HOME}/bin/nvinfer_plugin${TENSORRT_LIBRARY_SUFFIX}.dll"
    "${_TENSORRT_HOME}/bin/nvinfer_dispatch${TENSORRT_LIBRARY_SUFFIX}.dll"
    "${_TENSORRT_HOME}/bin/nvinfer_lean${TENSORRT_LIBRARY_SUFFIX}.dll"
  )

  if(_DLLS)
    install(FILES ${_DLLS} DESTINATION "vsmlrt-cuda")
  else()
    message(WARNING "Could not find TensorRT DLLs")
  endif()
else()
  # Copy TensorRT shared libraries on Linux
  # These are dlopen'd at runtime by libnvinfer.so and invisible to auditwheel.
  if(DEFINED ENV{TENSORRT_HOME})
    file(TO_CMAKE_PATH "$ENV{TENSORRT_HOME}" _TENSORRT_HOME)
    set(_TRT_LIB_PATHS "${_TENSORRT_HOME}/lib" "${_TENSORRT_HOME}/lib64")
  else()
    set(_TRT_LIB_PATHS "/usr/lib" "/usr/lib64" "/usr/lib/x86_64-linux-gnu" "/usr/lib/aarch64-linux-gnu")
  endif()

  set(_TRT_SEARCH_PATTERNS)
  foreach(_PATH IN LISTS _TRT_LIB_PATHS)
    list(
      APPEND _TRT_SEARCH_PATTERNS
      "${_PATH}/libnvinfer.so.10"
      "${_PATH}/libnvinfer_plugin.so.10"
      "${_PATH}/libnvinfer_dispatch.so.10"
      "${_PATH}/libnvinfer_lean.so.10"
    )
  endforeach()

  file(GLOB _LIBS ${_TRT_SEARCH_PATTERNS})
  if(_LIBS)
    foreach(_LIB IN LISTS _LIBS)
      file(REAL_PATH "${_LIB}" _REAL_LIB)
      get_filename_component(_LIB_NAME "${_LIB}" NAME)
      install(FILES "${_REAL_LIB}" DESTINATION . RENAME "${_LIB_NAME}")
    endforeach()
  else()
    message(WARNING "Could not find TensorRT libraries")
  endif()
endif()

# Write VapourSynth Manifest
if(WIN32)
  file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/manifest.vs" "[VapourSynth Manifest V1]\nvstrt\n")
else()
  file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/manifest.vs" "[VapourSynth Manifest V1]\nlibvstrt\n")
endif()
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/manifest.vs" DESTINATION .)
