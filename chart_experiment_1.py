
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re
import json
from helper import run_command
from collections import defaultdict
import matplotlib.pyplot as plt

import logging

plt.rc('font', size=12)

logging.basicConfig(level=logging.ERROR)
fifo = [
    Path('results/test-6'),
    Path('results/test-7'),
    Path('results/test-8'),
]
fair = [
    Path('results/test-12'),
    Path('results/test-13'),
    Path('results/test-14'),
]
delay = [
    Path('results/test-15'),
    Path('results/test-16'),
    Path('results/test-17'),
]

def get_bins(paths):
    bin1 = []
    bin2 = []
    bin3 = []

    for p in paths:
        with open(p / 'processed.json', 'r') as f:
            all_results = json.load(f)

        bin3.extend([r['run_time'] for r in all_results if r['map_count'] >= 1200])
        bin2.extend([r['run_time'] for r in all_results if r['map_count'] < 1200 and r['map_count'] >= 10])
        bin1.extend([r['run_time'] for r in all_results if r['map_count'] < 10])

    bin3 = sorted(bin3)
    bin2 = sorted(bin2)
    bin1 = sorted(bin1)
    return [bin1, bin2, bin3]


fifo_bins = get_bins(fifo)
fair_bins = get_bins(fair)
delay_bins = get_bins(delay)

def get_cdf(bin):
    v = [(i+1) / len(bin) for i in range(len(bin))]
    return [0, *v]


fig, (ax1, ax2, ax3) = plt.subplots(ncols=3, sharey=True, subplot_kw=dict(box_aspect=1))

def chart_bin(i):
    plt.plot([fifo_bins[i][0], *fifo_bins[i]], get_cdf(fifo_bins[i]), 'k-', label='FIFO', linewidth=3)
    plt.plot([fair_bins[i][0], *fair_bins[i]], get_cdf(fair_bins[i]), 'k--', label='Naive Fair', linewidth=3)
    plt.plot([delay_bins[i][0], *delay_bins[i]], get_cdf(delay_bins[i]), 'k:', label='Fair + DS', linewidth=3)
   

plt.subplot(1, 3, 1)
chart_bin(0)
plt.xlim(xmin=0)
plt.ylim(ymin=0)
plt.ylabel('CDF')
plt.xlabel('Time (s)')
plt.title('CDF for job bins 1-3')
plt.legend(frameon=False)

plt.subplot(1, 3, 2)
chart_bin(1)
plt.xlim(xmin=0)
plt.xlabel('Time (s)')
plt.ylim(ymin=0)
plt.title('CDF for job bins 4-8')
plt.legend(frameon=False)


plt.subplot(1, 3, 3)
chart_bin(2)
plt.xlim(xmin=0)
plt.ylim(ymin=0)
plt.xlabel('Time (s)')
plt.title('CDF for job bin 9')
plt.legend(loc='lower left', frameon=False)

plt.show()
plt.close()
