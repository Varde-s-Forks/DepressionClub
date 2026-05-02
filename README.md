# VSWheels

Our custom index here https://jaded-encoding-haumaturgy.github.io/vs-wheels

## BM3DCPU

- 2.16: Yanked
- 2.16.1: Yanked
- 2.16.2: Yanked
- 2.16.3: Matches upstream R2.16

## BM3DCUDA

- 2.16: Matches upstream R2.16
  - Windows: Compiled with CUDA 13.0.1 and Visual Studio 2022
  - Linux: Compiled with CUDA 12.8
- 2.17.dev1
  - Windows: Compiled with CUDA 13.2.1 and Visual Studio 2026
  - Linux: Compiled with CUDA 13.2

## BM3DHIP

## DFTTEST2

## VS-MLRT

## FMTCONV / FMTC

Builds for all platforms are available on our custom index.

```bash
uv add --index https://jaded-encoding-haumaturgy.github.io/vs-wheels/simple vapoursynth-fmtconv
```

```bash
pip install vapoursynth-fmtconv --extra-index-url https://jaded-encoding-haumaturgy.github.io/vs-wheels/simple
```

- 31: Matches upstream R31
  - Windows: Compiled with Visual Studio 2026
