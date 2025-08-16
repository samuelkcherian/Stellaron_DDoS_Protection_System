# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy the requirements file FIRST
COPY requirements.txt .

# Install the dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application code
COPY . .

CMD ["python", "app.py"]