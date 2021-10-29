
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re
import json
from helper import run_command

results_path = Path('results/test-2')


all_results = []
for log in results_path.glob('*.txt'):
    with open(log, 'r') as f:
        results = defaultdict(int)
        submit_time = None
        finish_time = None
        for line in f.readlines():

            if line.startswith('Submitted At:'):
                submit_time = datetime.strptime(re.search("\d+:\d+:\d+", line).group(0), '%H:%M:%S')

            if line.startswith('Finished At:'):
                finish_time = datetime.strptime(re.search("\d+:\d+:\d+", line).group(0), '%H:%M:%S')

            cells = [c.strip() for c in line.split('|')]
            if len(cells) > 2 and cells[2] == 'Launched map tasks':
                results['map_count'] = int(cells[-1])

            if len(cells) > 2 and cells[2] == 'Rack-local map tasks':
                results['rack_local_count'] = int(cells[-1])

            if len(cells) > 2 and cells[2] == 'Other local map tasks':
                results['data_local_count'] = int(cells[-1])

            if len(cells) > 2 and cells[2] == 'Data-local map tasks':
                results['data_local_count'] += int(cells[-1])

        results["run_time"] = (finish_time - submit_time).total_seconds()
        all_results.append(results)


run_command(f'rm -rf {results_path}/*')
with open(results_path / 'processed.json', 'w') as f:
    json.dump(all_results, f, indent=2)
