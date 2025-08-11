from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Create a new FastAPI app for serving images
image_app = FastAPI()

# Define the directory for images
images_dir = Path("/home/xk/Software/6_bohr_agent/src/images")  # Update with your images directory

# Mount the static files directory
image_app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(image_app, host="0.0.0.0", port=50002)  # Serve on a different port