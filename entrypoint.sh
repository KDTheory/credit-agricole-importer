#!/bin/bash

echo "Starting entrypoint script"

run_script() {
    echo "Running main.py"
    python /app/main.py
    echo "main.py execution completed"
}

echo "Running initial script"
run_script

echo "Entering main loop"
while true; do
    echo "Waiting for next execution"
    sleep 3600
    echo "Running scheduled script"
    run_script
done
