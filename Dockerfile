FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first (before requirements.txt)
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install transformers + accelerate separately
# to ensure they use the torch already installed
RUN pip install --no-cache-dir \
    transformers>=4.35.0 \
    accelerate

# Install all other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Create runtime directories
RUN mkdir -p /app/uploads /app/cache

# Pre-download SegFormer model during build
# So first scan is fast not slow
RUN python -c "\
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation; \
SegformerImageProcessor.from_pretrained('LightDestory/segformer-b0-finetuned-segments-food-oct-24v2'); \
SegformerForSemanticSegmentation.from_pretrained('LightDestory/segformer-b0-finetuned-segments-food-oct-24v2'); \
print('SegFormer model cached')"

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
