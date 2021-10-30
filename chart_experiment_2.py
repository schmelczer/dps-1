import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st

fifo = [
    Path("results/test-6"),
    Path("results/test-7"),
    Path("results/test-8"),
]
fair = [
    Path("results/test-12"),
    Path("results/test-13"),
    Path("results/test-14"),
]
delay = [
    Path("results/test-15"),
    Path("results/test-16"),
    Path("results/test-17"),
]


limits = [1, 2, 10, 50, 100, 200, 400, 1200]


def get_bin_averages(path):
    with open(path / "processed.json") as f:
        all = json.load(f)
    bin_averages = []
    for start, end in zip(limits, [*limits[1:], 100000]):
        bin = [v for v in all if v["map_count"] >= start and v["map_count"] < end]
        bin_averages.append(sum(b["run_time"] for b in bin) / len(bin))
    return bin_averages


delay_bin_avgs = [get_bin_averages(f) for f in delay]

plt.rc("font", size=16)


def chart(bin_avgs, name):
    speedup = [
        [f / d for f, d in zip(fs, ds)] for fs, ds in zip(bin_avgs, delay_bin_avgs)
    ]
    speedup = zip(*speedup)

    def mean_confidence_interval(data, confidence=0.95):
        return st.t.interval(
            confidence, len(data) - 1, loc=np.mean(data), scale=st.sem(data)
        )

    lu_bars = []
    lu_cis = []
    for d in speedup:
        f, t = mean_confidence_interval(d)
        mean = np.mean(d)
        lu_bars.append(mean)
        ci = np.std(d)
        lu_cis.append(ci)

    # width of the bars
    barWidth = 0.8

    # The x position of bars
    r1 = np.arange(len(lu_bars))
    [x + barWidth for x in r1]

    plt.bar(r1, lu_bars, width=barWidth, color="#555555", yerr=lu_cis, capsize=7)

    plt.xticks(range(len(lu_bars)))
    plt.ylabel("Speedup")
    plt.xlabel("Bin")
    plt.ylim(ymin=0)

    fig = plt.gcf()
    fig.set_size_inches(15, 5)

    plt.savefig(f"figures/{name}", bbox_inches="tight", dpi=400)
    plt.close()


fifo_bin_avgs = [get_bin_averages(f) for f in fifo]
fair_bin_avgs = [get_bin_averages(f) for f in fair]
chart(fifo_bin_avgs, "delay-fifo-speedup")
chart(fair_bin_avgs, "delay-fair-speedup")
