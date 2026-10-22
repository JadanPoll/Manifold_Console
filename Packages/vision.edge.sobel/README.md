# Axiom: Edge Detection (Sobel)

First independently buildable Manifold native capability. No Python, OpenCV,
or MediaPipe dependency. This package is intentionally not installed
automatically by the Console.

```sh
cd Packages/vision.edge.sobel
make
make test
```

Public C11 entrypoint: `mc_sobel_gray8` in `sobel.h`.

- Input: grayscale 8-bit pixels with explicit byte stride
- Output: caller-owned grayscale 8-bit pixels with explicit stride
- Border: zero
- Gradient: saturated L1 Sobel magnitude
- Input and output buffers must not overlap
- Function performs no allocations or device access

A successful package build is **not** evidence of Raspberry Pi validation.
The next integration step is connecting this kernel to a Kinect-owned frame
stream via a versioned native frame contract. The current package manifest
is metadata, not an installer or ABI promise.
