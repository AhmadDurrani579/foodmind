FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Fix NumPy version first
RUN pip install --no-cache-dir "numpy<2.0"

# PyTorch 2.1 CPU
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# transformers 4.40 works with torch 2.1
RUN pip install --no-cache-dir \
    "transformers==4.40.0" \
    accelerate

# Verify torch works
RUN python -c "import torch; print('Torch OK:', torch.__version__)"

# Install all other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

RUN mkdir -p /app/uploads /app/cache

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
