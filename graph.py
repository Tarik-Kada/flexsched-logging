import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Reading data from CSV file
file_path = 'results/experiment_4_results.csv'  # Change this path to your CSV file location
df = pd.read_csv(file_path, skipinitialspace=True)

plt.style.use('seaborn-whitegrid')
plt.rcParams.update({
    "font.family": "serif",
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "axes.prop_cycle": plt.cycler('color', plt.cm.tab10(np.linspace(0, 1, 10)))
})

# Plotting Bar Chart
setups = df['setup'].unique()
instances = df['instances'].unique()

fig, ax = plt.subplots(figsize=(14, 8))

bar_width = 0.15
index = np.arange(len(instances))

# labels = {"base": "Stock Knative Serving", "default_custom": "Extended Knative Serving w/o Ext. Algorithm", "ext_custom": "Extended Knative Serving with Ext. Algorithm"}
# labels = {"rr_sleep_0s": "Round Robin (Sleep 0s)", "rr_sleep_1s": "Round Robin (Sleep 1s)", "rr_sleep_5s": "Round Robin (Sleep 5s)"}
labels = {"1_worker": "1 Worker Node", "2_worker": "2 Worker Nodes", "3_worker": "3 Worker Nodes", "4_worker": "4 Worker Nodes", "5_worker": "5 Worker Nodes"}

for i, setup in enumerate(setups):
    setup_data = df[df['setup'] == setup]
    print(setup_data)
    if setup == '1_worker':
        index = np.arange(len(instances) - 1)
    else:
        index = np.arange(len(instances))
    ax.bar(index + i * bar_width, setup_data['average start-up time'], bar_width,
           yerr=setup_data['start-up time std dev'], label=f'{labels[setup]}', capsize=5)

ax.set_xlabel('Number of Instances', fontsize=12)
ax.set_ylabel('Average Start-up Time (seconds)', fontsize=12)
# ax.set_title('Average Start-up Time with Standard Deviation for Different Setups', fontsize=14)
ax.set_xticks(index + bar_width)
ax.set_xticklabels(instances)
ax.legend()

plt.grid(True)
plt.tight_layout()
plt.show()
fig.savefig('images/4_average_start_up_time.png')

# Plotting Line Chart
fig, ax = plt.subplots(figsize=(14, 8))

line_styles = {'average start-up time': 'solid', 'average queue time': 'dashdot', 'scheduling latency': 'dashed'}
cmap = plt.get_cmap('tab10').colors
# line_colors = {'base': cmap[0], 'default_custom': cmap[2], 'ext_custom': cmap[3]}
# line_colors = {'rr_sleep_0s': cmap[0], 'rr_sleep_1s': cmap[2], 'rr_sleep_5s': cmap[3]}
line_colors = {'1_worker': cmap[0], '2_worker': cmap[2], '3_worker': cmap[3], '4_worker': cmap[4], '5_worker': cmap[5]}

for setup in setups:
    setup_data = df[df['setup'] == setup]
    for metric in ['average start-up time', 'average queue time', 'scheduling latency']:
        # ax.plot(np.array(setup_data['instances']), np.array(setup_data[metric]))
        ax.plot(np.array(setup_data['instances']), np.array(setup_data[metric]), label=f'{labels[setup]} - {metric.replace("_", " ").title()}', linestyle=line_styles[metric], linewidth=2 if metric == 'average start-up time' else 1, color=line_colors[setup])

ax.set_xlabel('Number of Instances', fontsize=12)
ax.set_ylabel('Time (seconds)', fontsize=12)
# ax.set_title('Performance Metrics for Different Setups', fontsize=14)
ax.legend()

plt.grid(True)
plt.tight_layout()
plt.show()
fig.savefig('images/4_performance_metrics.png')
