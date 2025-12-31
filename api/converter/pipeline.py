import os
import shutil
from pathlib import Path
from .preprocess import FrameExtractor
from .sfm import SfMWrapper
from .semantics import SemanticEncoder
from .training import GaussianTrainer

class ConverterPipeline:
    """
    Orchestrates the Video-to-Splat pipeline.
    """
    def __init__(self, base_dir: str = "temp_process"):
        self.base_dir = Path(base_dir)
        self.frames_dir = self.base_dir / "frames"
        self.sfm_dir = self.base_dir / "sfm"
        self.model_dir = self.base_dir / "models"
        
        # Initialize modules
        self.extractor = FrameExtractor(output_dir=str(self.frames_dir))
        self.sfm = SfMWrapper(output_dir=str(self.sfm_dir))
        # Lazy load semantics to save memory if not used immediately
        self.encoder = None 
        self.trainer = GaussianTrainer(output_dir=str(self.model_dir))
        
    def run(self, video_path: str, use_semantics: bool = False):
        try:
            # Clean start
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
            self.base_dir.mkdir(parents=True)
            
            # 1. Preprocess
            print("--- Step 1: Extracting Frames ---")
            frame_paths = self.extractor.extract(video_path, fps=2)
            
            # 2. SfM
            print("--- Step 2: Running Structure from Motion ---")
            point_cloud = self.sfm.run(str(self.frames_dir))
            
            # 3. Semantics (Optional)
            semantic_features = None
            if use_semantics:
                print("--- Step 3: Extracting Semantics ---")
                if not self.encoder:
                    self.encoder = SemanticEncoder()
                semantic_features = self.encoder.extract(frame_paths)
            
            # 4. Training
            print("--- Step 4: Training Gaussian Splat ---")
            output_ply = self.trainer.train(point_cloud, frame_paths, semantic_features)
            
            print(f"--- Pipeline Complete. Output at {output_ply} ---")
            return output_ply
            
        except Exception as e:
            print(f"Pipeline Failed: {e}")
            raise e
