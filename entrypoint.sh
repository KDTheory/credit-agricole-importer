#!/bin/bash

echo "Starting entrypoint script"

# Function to execute the Python script
run_script() {
    echo "Running main.py"
    python /app/main.py
    echo "main.py execution completed"
}

# Run the script immediately when the container starts
echo "Running initial script"
run_script

# Set up cron job to run at 8 AM every day and log output to Docker logs
echo "0 8 * * * /bin/bash -c 'python3 /app/main.py' >> /proc/1/fd/1 2>&1" | crontab -

# Confirm that cron has been set up correctly
echo "Cron job setup:"
crontab -l

# Start cron in the foreground (important for Docker)
echo "Starting cron service"
cron -f
