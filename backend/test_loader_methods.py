import os
import sys

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.model_loader import ModelLoader

print("Loading model loader...")
ModelLoader.load_model()

print("ModelLoader._df is None:", ModelLoader._df is None)
if ModelLoader._df is not None:
    print("DataFrame shape:", ModelLoader._df.shape)
    print("Target index:", ModelLoader.get_target_idx())
    
    print("\nTimeline data (first 3 points):")
    timeline = ModelLoader.get_timeline_data()
    print("Timeline length:", len(timeline))
    for pt in timeline[:3]:
        print(pt)
        
    print("\nFuture forecast (first 3 points):")
    future = ModelLoader.get_future_forecast(168)
    print("Future length:", len(future))
    for pt in future[:3]:
        print(pt)
