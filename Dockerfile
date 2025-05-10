FROM python:3.10-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY streamlit_app.py .
COPY README.md .
COPY src/ ./src/
COPY .env.example .

# Install UV and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    uv pip install --system --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose the port Streamlit runs on
EXPOSE 8501

# Set up a volume for persistent data and configurations
VOLUME ["/app/data"]

# Command to run the Streamlit app with UV
CMD ["python", "-m", "uv", "run", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"] 