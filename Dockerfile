FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any) – keep minimal
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .
# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create persistence directory for SQLite DB and set permissions
RUN mkdir -p /carpediem_data && chown -R www-data:www-data /carpediem_data

# Create non‑root user and set ownership
RUN chown -R www-data:www-data /app
ENV HOME=/app
USER www-data

# Expose the port defined in .env (default 8001)
EXPOSE 8001

# Initialise DB then start gunicorn
ENTRYPOINT ["/entrypoint.sh"]
