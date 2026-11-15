# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Command to run the FastAPI server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]