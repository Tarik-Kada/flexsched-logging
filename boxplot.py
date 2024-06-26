import sys
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

def parse_log_line(line):
    # split line by whitespace after removing all commas
    line = line.replace(",", "")
    parts = line.split()
    event_type = parts[4]
    pod_name = parts[6]
    node_name = parts[10] if event_type == "Scheduled" else None
    timestamp = parts[12]
    # change timestamp from utc timestamp to datetime object
    timestamp = datetime.utcfromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S.%f')
    return timestamp, event_type, pod_name, node_name


def get_metrics(log_file, instances):
    # Read the log file
    created = []
    scheduled = []

    pod_prefix = f"hello-{instances}-"
    with open(log_file, 'r') as f:
        # Define the dictionary to store the parsed data
        data = {}

        lines = f.readlines()
        for line in lines:
            if pod_prefix in line:
                timestamp, event_type, pod_name, node_name = parse_log_line(line)
                # put the parsed data into a dictionary
                if pod_name not in data:
                    if event_type == "Created" and pod_name not in created:
                        data[pod_name] = {'creation': timestamp, 'scheduled': None, 'node': None}
                        created.append(pod_name)
                    elif event_type == "Scheduled" and pod_name not in scheduled:
                        data[pod_name] = {'creation': None, 'scheduled': timestamp, 'node': node_name}
                        scheduled.append(pod_name)
                else:
                    if event_type == "Scheduled" and pod_name not in scheduled:
                        data[pod_name]['scheduled'] = timestamp
                        data[pod_name]['node'] = node_name
                        scheduled.append(pod_name)
                    elif event_type == "Created" and pod_name not in created:
                        data[pod_name]['creation'] = timestamp
                        created.append(pod_name)

    durations = []
    queue_times = []
    # For every pod in the dictionary, find the first created event and scheduled event and save the timestamps of both
    # Also determine the queue time for the pod: the queue time is equal to the startup-latency - (the time difference between the scheduling of a previous pod and the scheduling of the current pod)
    previous_scheduled_time = None
    for pod, timestamps in data.items():
        creation = timestamps['creation']
        scheduled = timestamps['scheduled']
        if creation and scheduled:
            creation_dt = datetime.strptime(creation, '%Y-%m-%d %H:%M:%S.%f')
            scheduled_dt = datetime.strptime(scheduled, '%Y-%m-%d %H:%M:%S.%f')
            startup_latency = (scheduled_dt - creation_dt).total_seconds()
            durations.append(startup_latency)
            if previous_scheduled_time:
                if creation_dt < previous_scheduled_time:
                    queue_time = startup_latency - (scheduled_dt - previous_scheduled_time).total_seconds()
                    queue_times.append(queue_time)
                else:
                    queue_times.append(0)
            previous_scheduled_time = scheduled_dt

    # Calculate the average time to schedule the pod
    average_time = sum(durations) / len(durations)

    # Calculate the standard deviation of the time to schedule the pod
    variance = sum([((x - average_time) ** 2) for x in durations]) / len(durations)
    std_dev = variance ** 0.5

    # Calculate the average queue time
    if len(queue_times) == 0:
        average_queue_time = 0
    else:
        average_queue_time = sum(queue_times) / len(queue_times)

    # Calculate the scheduling latency
    scheduling_latencies = []
    scheduling_latency = 0
    if len(durations) == 0 or len(queue_times) == 0:
        scheduling_latency = 0
    else:
        for i in range(1, len(durations)):
            scheduling_latencies.append(durations[i] - queue_times[i - 1])
        scheduling_latency = sum(scheduling_latencies) / len(scheduling_latencies)

    return durations, std_dev, queue_times, scheduling_latencies

if __name__ == '__main__':
    # labels = {"base": "Stock Knative Serving", "default_custom": "Extended Knative Serving w/o Ext. Algorithm", "ext_custom": "Extended Knative Serving with Ext. Algorithm"}
# labels = {"rr_sleep_0s": "Round Robin (Sleep 0s)", "rr_sleep_1s": "Round Robin (Sleep 1s)", "rr_sleep_5s": "Round Robin (Sleep 5s)"}

    experiment = 2

    match experiment:
        case 2:
            log_files = ["base", "default_custom", "ext_custom"]
            labels = ["Stock Knative Serving", "Extended Knative Serving w/o Ext. Algorithm", "Extended Knative Serving with Ext. Algorithm"]
        case 3:
            log_files = ["rr_sleep_0s", "rr_sleep_1s", "rr_sleep_5s"]
            labels = ["Round Robin (Sleep 0s)", "Round Robin (Sleep 1s)", "Round Robin (Sleep 5s)"]
        case 4:
            log_files = ["1_worker", "2_worker", "3_worker", "4_worker", "5_worker"]
            labels = ["1 Worker Node", "2 Worker Nodes", "3 Worker Nodes", "4 Worker Nodes", "5 Worker Nodes"]
        case _:
            print("Invalid experiment number")
            sys.exit(1)

    instances = [1, 5, 10, 25, 50, 100]

    # results = [["setup", "instances", "average start-up time", "start-up time std dev", "average queue time", "scheduling latency"]]
    boxplot_data = {}

    for log_file in log_files:
        path = f"./log-outputs/pod_event_logs_{log_file}-1-100.txt"
        if log_file == "1_worker":
            path = f"./log-outputs/pod_event_logs_{log_file}-1-50.txt"
        for instance in instances:
            if log_file == "1_worker" and instance == 100:
                continue
            times, std_dev, queue_times, scheduling_latencies = get_metrics(path, instance)
            if log_file not in boxplot_data:
                boxplot_data[log_file] = [{instance: scheduling_latencies}]
            else:
                boxplot_data[log_file].append({instance: scheduling_latencies})

    # Plotting grouped Box Plots
    fig, ax = plt.subplots(figsize=(14, 8))

    colors = plt.get_cmap('Set3', len(log_files)).colors
    positions = np.arange(len(instances)) * (len(log_files) + 1)

    boxes = []
    for setup_idx, (setup, data) in enumerate(boxplot_data.items()):
        for instance_idx, instance_data in enumerate(data):
            instance = list(instance_data.keys())[0]
            pos = positions[instance_idx]
            box = ax.boxplot(instance_data[instance], positions=[pos + setup_idx], patch_artist=True, widths=0.6, showfliers=False)
            boxes.append(box)
            for patch in box['boxes']:
                patch.set_facecolor(colors[setup_idx])
                patch.set_edgecolor('black')
            for median in box['medians']:
                median.set(color='black')

    # Customizing the plot
    ax.set_xlabel('Number of Instances Started at Once')
    ax.set_ylabel('Scheduling Latencies (seconds)')
    ax.set_xticks(positions + (len(log_files) - 1) / 2)
    ax.set_xticklabels(instances)

    legend_boxes = []
    seen_colors = []
    for box in boxes:
        if box["boxes"][0].get_facecolor() not in seen_colors:
            seen_colors.append(box["boxes"][0].get_facecolor())
            legend_boxes.append(box["boxes"][0])

    ax.legend(legend_boxes, labels, loc='upper left')

    plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.show()

    fig.savefig(f'images/{experiment}_boxplot_scheduling_latencies.png')
