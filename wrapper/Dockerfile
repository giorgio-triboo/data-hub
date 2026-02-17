FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    curl \
    postgresql-client \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application files
COPY . .

# Supervisor configuration
COPY supervisor.conf /etc/supervisor/conf.d/supervisor.conf

# Create logs directory
RUN mkdir -p /app/logs

# Make app.py and entrypoint executable
RUN chmod +x /app/app.py /app/entrypoint.sh

# Expose supervisor control socket (optional)
EXPOSE 9001

ENTRYPOINT ["/app/entrypoint.sh"]
