# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for database and credentials
RUN mkdir -p /app/data /app/credentials

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/sake_recipe_db.sqlite

# Expose port for GUI (if needed for web interface)
EXPOSE 8080

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting SakeMonkey Recipe Database..."\n\
echo "Database location: $DATABASE_PATH"\n\
echo "Available commands:"\n\
echo "  python gui_app.py          - Start GUI application"\n\
echo "  python database_interface.py - Start CLI interface"\n\
echo "  python setup_database.py    - Initialize database"\n\
echo "  python import_excel_data.py - Import from Excel"\n\
echo "  python setup_google_sheets.py - Setup Google Sheets sync"\n\
echo ""\n\
echo "Starting GUI application..."\n\
exec python gui_app.py' > /app/start.sh && chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]
