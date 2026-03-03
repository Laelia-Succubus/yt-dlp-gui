# Use the official Debian image as a base
FROM debian:bookworm

# Install Python, pip, yt-dlp with extras, Node.js, ffmpeg, and Bottle
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && pip3 install --break-system-packages yt-dlp bottle \
    && yt-dlp --update --no-check-certificates \
    && echo -e "--js-runtimes node\n--no-check-certificates" > /etc/yt-dlp.conf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the Python application files
COPY ../yt-dlp-gui-python/app.py /app/
COPY ../yt-dlp-gui-python/index.html /app/

# Create downloads directory
RUN mkdir -p /app/downloads

# Expose port 8080
EXPOSE 8080

# Start the application
CMD ["python3", "app.py"]
