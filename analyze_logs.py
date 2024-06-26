import sys
from datetime import datetime


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
                # print(line)
                timestamp, event_type, pod_name, node_name = parse_log_line(line)
                # print(f"Timestamp: {timestamp}, Event: {event_type}, Pod: {pod_name}, Node: {node_name}")
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
            # print(f"Creation: {creation_dt}")
            # print(f"Scheduled: {scheduled_dt}")
            # print(f"Previous scheduled time: {previous_scheduled_time}")
            # if previous_scheduled_time:
            #     print(f"{creation_dt < previous_scheduled_time}")
            # print("----------------")
            durations.append(startup_latency)
            if previous_scheduled_time:
                if creation_dt < previous_scheduled_time:
                # print(f"Previous scheduled time: {previous_scheduled_time}")
                # print(f"Scheduled time: {scheduled_dt}")
                # print(f"Difference: {(scheduled_dt - previous_scheduled_time).total_seconds()}")
                # print(f"Startup latency: {startup_latency}")
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

    return average_time, std_dev, average_queue_time, scheduling_latency

if __name__ == '__main__':
    # log_files = ["base", "default_custom", "ext_custom"]
    # log_files = ["rr_sleep_0s", "rr_sleep_1s", "rr_sleep_5s"]
    log_files = ["1_worker", "2_worker", "3_worker", "4_worker", "5_worker"]
    instances = [1, 5, 10, 25, 50, 100]

    results = [["setup", "instances", "average start-up time", "start-up time std dev", "average queue time", "scheduling latency"]]
    for log_file in log_files:
        path = f"./log-outputs/pod_event_logs_{log_file}-1-100.txt"
        if log_file == "1_worker":
            path = f"./log-outputs/pod_event_logs_{log_file}-1-50.txt"
        for instance in instances:
            if log_file == "1_worker" and instance == 100:
                continue
            average_time, std_dev, average_queue_time, scheduling_latency = get_metrics(path, instance)
            results.append([log_file, instance, average_time, std_dev, average_queue_time, scheduling_latency])
    with open(f"./results/experiment_4_results.csv", "w") as f:
        for r in results:
            f.write(", ".join(map(str, r)) + "\n")
        results = []
