#!/bin/bash

# Define the namespace where the pod-event-logger is running
NAMESPACE="default" # Change this to the correct namespace if needed

# Define the pod label selector to find the pod-event-logger pod
POD_LABEL="app=pod-event-logger" # Change this to the correct label selector if needed

# Define the output file
OUTPUT_FILE="pod_event_logs_rr_sleep_0s-1-100.txt"

# Find the pod-event-logger pod
POD_NAME=$(kubectl get pods -n $NAMESPACE -l $POD_LABEL -o jsonpath="{.items[0].metadata.name}")

if [ -z "$POD_NAME" ]; then
  echo "Error: Could not find a pod with label $POD_LABEL in namespace $NAMESPACE"
  exit 1
fi

echo "Found pod-event-logger pod: $POD_NAME"

# Fetch the logs and write them to the output file
echo "Fetching logs from $POD_NAME and writing to $OUTPUT_FILE"
kubectl logs -n $NAMESPACE $POD_NAME >> log-outputs/$OUTPUT_FILE

if [ $? -eq 0 ]; then
  echo "Logs successfully written to $OUTPUT_FILE"
else
  echo "Error: Failed to fetch logs from $POD_NAME"
  exit 1
fi
