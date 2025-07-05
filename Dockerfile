# Use an official Python runtime as a parent image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

RUN pip install --upgrade pip

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Application Code ---
# Copy the rest of the application files into the working directory.
COPY . .

# Expose the port the Flask app runs on
EXPOSE 5000

# Run database initialization then start the Flask app
CMD ["python", "app.py"]
