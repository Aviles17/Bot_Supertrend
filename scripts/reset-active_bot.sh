#!/bin/bash

# Array of process names to search and kill
process_names=("python3 src/Bot_SuperTrend.py" "./Heartbeat_server")

for process_name in "${process_names[@]}"; do
  # Find the PID(s) of the process
  PIDs=$(ps -aux | grep "$process_name" | grep -v "grep" | awk '{print $2}')
  
  if [ -n "$PIDs" ]; then
    echo "Found process(es) for '$process_name' with PID(s): $PIDs"
    
    # Kill each PID
    for PID in $PIDs; do
      kill "$PID"
      
      if [ $? -eq 0 ]; then
        echo "Process $PID for '$process_name' terminated successfully."
      else
        echo "Failed to terminate process $PID for '$process_name'."
      fi
    done
  else
    echo "No matching process found for '$process_name'."
  fi
done
