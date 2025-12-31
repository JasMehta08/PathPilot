"""
PathPilot Converter Package
---------------------------
This package implements the pipeline to convert raw video footage into 
Semantic Gaussian Splat representations.

Modules:
- preprocess: Extracts frames from video.
- sfm: Runs Colmap to get sparse point cloud and camera poses.
- semantics: Extracts semantic features using CLIP.
- training: Runs the simplified Gaussian Splatting optimization loop.
- pipeline: Orchestrates the entire flow.
"""

# Expose main classes for easier import
# from .pipeline import ConverterPipeline (Will implement later)
