from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer
from PIL import Image
import torch
import os
from pathlib import Path

class SemanticEncoder:
    """
    Module 3: Semantic Feature Extraction
    Uses OpenAI's CLIP model to extract semantic features from images.
    """
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        print(f"Loading CLIP model: {model_name}...")
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.tokenziers = CLIPTokenizer.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"Model loaded on {self.device}.")

    def extract(self, image_paths: list[str]):
        """
        Extracts feature vectors for a list of images.
        """
        if not image_paths:
            return None
            
        print(f"Extracting semanti features for {len(image_paths)} images...")
        features = []
        
        # Process in batches to avoid OOM
        batch_size = 4
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i+batch_size]
            images = [Image.open(p) for p in batch_paths]
            
            with torch.no_grad():
                inputs = self.processor(text=None, images=images, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                output = self.model.get_image_features(**inputs)
                
                # Normalize features
                output = output / output.norm(p=2, dim=-1, keepdim=True)
                features.append(output.cpu())
        
        return torch.cat(features)
        
    def encode_text(self, text: list[str]):
        """
        Encodes text queries to compare against image features.
        """
        with torch.no_grad():
            inputs = self.tokenziers(text, padding=True, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            text_features = self.model.get_text_features(**inputs)
            return text_features / text_features.norm(p=2, dim=-1, keepdim=True)
