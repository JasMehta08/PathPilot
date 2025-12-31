# 3D Converter Pipeline

This package implements an educational pipeline for converting video footage into semantic 3D Gaussian Splat representations.

## Architecture

The pipeline consists of four main stages:

### 1. Preprocessing (`preprocess.py`)
*   **Frame Extraction**: usage of OpenCV to extract individual frames from the input video.

### 2. Structure from Motion (`sfm.py`)
*   **Point Cloud Generation**: Wraps COLMAP (or a synthetic fallback) to generate a sparse point cloud from the extracted frames. This provides the initial geometry for the 3D model.

### 3. Semantic Encoding (`semantics.py`)
*   **Feature Extraction**: Uses OpenAI's CLIP model to extract semantic features from each frame. These features allow the system to "understand" the content of the scene.

### 4. Gaussian Splatting (`training.py`)
*   **Optimization Loop**: A simplified PyTorch implementation of the Gaussian Splatting training process. It initializes 3D Gaussians from the sparse point cloud and optimizes them to match the input images.

## Usage

This package is designed to be used by the main FastAPI application. The `ConverterPipeline` class in `pipeline.py` orchestrates the execution of these stages sequentially.
