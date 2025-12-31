import cv2
import os
from pathlib import Path

class FrameExtractor:
    """
    Module 1: Pre-processing
    Extracts frames from a video file at a specified interval.
    """
    def __init__(self, output_dir: str = "data/frames", output_format: str = "jpg"):
        self.output_dir = Path(output_dir)
        self.output_format = output_format
        
    def extract(self, video_path: str, fps: int = 2) -> list[str]:
        """
        Extracts frames from the video.
        
        Args:
            video_path: Path to the input video file.
            fps: Desired frames per second to extract. 
                 (e.g., if video is 30fps and we want 2fps, we take every 15th frame)
        
        Returns:
            List of absolute paths to the extracted image files.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file.")
            
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(video_fps / fps) if fps < video_fps else 1
        
        frame_paths = []
        frame_count = 0
        saved_count = 0
        
        print(f"Extracting frames from {video_path} at {fps} fps (every {frame_interval} frames)...")
        
        while True:
            success, frame = cap.read()
            if not success:
                break
                
            if frame_count % frame_interval == 0:
                # Resize for consistency/performance if needed (optional, keeping original for now)
                # frame = cv2.resize(frame, (1920, 1080))
                
                filename = f"frame_{saved_count:05d}.{self.output_format}"
                filepath = self.output_dir / filename
                cv2.imwrite(str(filepath), frame)
                frame_paths.append(str(filepath.absolute()))
                saved_count += 1
                
            frame_count += 1
            
        cap.release()
        print(f"Extracted {saved_count} frames to {self.output_dir}")
        return frame_paths

# Simple test block
if __name__ == "__main__":
    extractor = FrameExtractor(output_dir="temp_frames")
    # extractor.extract("path/to/video.mp4")
