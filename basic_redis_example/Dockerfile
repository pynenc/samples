# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install uv using the official installer script
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy only dependency files first to leverage Docker caching
COPY pyproject.toml ./
# If you have a lockfile, uncomment the line below:
# COPY uv.lock ./

# Install dependencies globally from pyproject.toml
RUN uv pip install --system .

# Copy the rest of the application code
COPY . .

# Set PYTHONPATH to include the directory of your package
ENV PYTHONPATH /usr/src/app

# Run app.py when the container launches
CMD ["pynenc", "runner", "start"]
