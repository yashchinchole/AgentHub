FROM python:3.12.3-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv and dependencies
RUN pip install --no-cache-dir uv
RUN uv sync --frozen --only-group client

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app/src

CMD ["streamlit", "run", "src/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
