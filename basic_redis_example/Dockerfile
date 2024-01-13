# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Set PYTHONPATH to include the directory of your package
ENV PYTHONPATH /usr/src/app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir pynenc

# Run app.py when the container launches
CMD ["pynenc", "--app=app.app", "runner", "start"]
