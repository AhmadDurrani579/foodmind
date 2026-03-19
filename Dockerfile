FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# PyTorch 2.1 CPU
RUN pip install --no-cache-dir \
    torch==2.1.0+cpu \
    torchvision==0.16.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# transformers 4.40 works with torch 2.1
RUN pip install --no-cache-dir \
    "transformers==4.40.0" \
    accelerate

# Verify torch + numpy work together
RUN python -c "import torch; import numpy; print('Torch:', torch.__version__, 'NumPy:', numpy.__version__)"

# Install all other dependencies
# numpy<2.0 is pinned inside requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/uploads /app/cache
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]