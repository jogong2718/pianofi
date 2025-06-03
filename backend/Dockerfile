# Use Python 3.12 base image
FROM python:3.12.7-slim

ENV ENVIRONMENT="development"
ENV AWS_REGION=us-east-1

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your app files
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
