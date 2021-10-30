import random
from pathlib import Path
from sys import argv
from time import sleep

from helper import execute_on_host, parallel_map, run_command

random.seed(42)


id_offset = 2150
job_sizes = [
    *[1] * 19,
    *[2] * 8,
    *[10] * 7,
    *[50] * 4,
    *[100] * 3,
    *[200] * 2,
    *[400] * 2,
    *[1200] * 2,
]
submit_sleep = 14

random.shuffle(job_sizes)


def generate_data(master, job_id, map_count):
    run_command(
    f"""
        cd benchmark/source_code/datagen/teragen
        perl teragen.pl {job_id} {map_count}
        cd -
    """
    )

    execute_on_host(
        master,
        f"""
            export JAVA_HOME=/usr
            export HADOOP_HOME=/local/s3052249/hadoop
            export HIVE_HOME=/local/s3052249/hive
            export DERBY_HOME=/local/s3052249/derby

            export PATH=$PATH:$HADOOP_HOME/bin
            export PATH=$PATH:$HADOOP_HOME/sbin
            export PATH=$PATH:$HIVE_HOME/bin

            $HIVE_HOME/bin/hive -e \
                "CREATE TABLE grep_{job_id} ( key STRING, field STRING ) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE;\
                LOAD DATA INPATH '/data/grep-{job_id}/*' INTO TABLE grep_{job_id}; \
                CREATE TABLE grep_{job_id}_select ( key STRING, field STRING );" 
        """,
    )


def run_benchmark(master, job_id, index):
    sleep(submit_sleep * index)
    execute_on_host(
        master,
        f"""
            export JAVA_HOME=/usr
            export HADOOP_HOME=/local/s3052249/hadoop
            export HIVE_HOME=/local/s3052249/hive
            export DERBY_HOME=/local/s3052249/derby

            export PATH=$PATH:$HADOOP_HOME/bin
            export PATH=$PATH:$HADOOP_HOME/sbin
            export PATH=$PATH:$HIVE_HOME/bin

            $HIVE_HOME/bin/hive -e \
                "INSERT OVERWRITE TABLE grep_{job_id}_select SELECT * FROM grep_{job_id} WHERE field LIKE '%XYZ%';"
        """,
    )

    # $HIVE_HOME/bin/hive -e "INSERT OVERWRITE TABLE grep_1010_select SELECT * FROM grep_1010 WHERE field LIKE '%XYZ%';"


if __name__ == "__main__":
    _, nodes_start, nodes_end = argv
    master = f"node{nodes_start}"

    cwd = run_command("pwd")

    # run_command(
    #     '''
    #         cd /home/aschmelc/dps1/benchmark/source_code/mapreduce
    #         ant clean
    #         ant jars
    #         mkdir ../datagen/teragen/lib
    #         cp ./jars/* ../datagen/teragen/lib
    #         cd ../datagen/teragen/
    #         ant clean
    #         ant teragen
    #         cp jars/teragen.jar ./
    #     '''
    # )

    # ''' cd benchmark/source_code/datagen/htmlgen
    #     python2 generateData.py {nodes_start},{nodes_end}
    #     cd -'''

    parallel_map(
        lambda v: generate_data(master, id_offset + v[0], v[1]),
        list(enumerate(job_sizes)),
        chunk_size=1,
        concurrency=len(job_sizes),
    )
    parallel_map(
        lambda v: run_benchmark(master, id_offset + v, v),
        range(len(job_sizes)),
        chunk_size=1,
        concurrency=len(job_sizes),
    )

    jobs = run_command(
    """
        export JAVA_HOME=/usr
        export HADOOP_HOME=hadoop
        export HIVE_HOME=hive
        export DERBY_HOME=derby
        
        export PATH=$PATH:$HADOOP_HOME/bin
        export PATH=$PATH:$HADOOP_HOME/sbin
        export PATH=$PATH:$HIVE_HOME/bin

        mapred job -list all
    """
    )

    ids = [l.split()[0] for l in jobs.split("\n")[2:] if l and l.split()[1] == "INSERT"]

    results = Path("results/test-5")
    results.mkdir(exist_ok=True, parents=True)
    for i in ids:
        r = execute_on_host(
            master,
            f"""
                export JAVA_HOME=/usr
                export HADOOP_HOME=/local/s3052249/hadoop
                export HIVE_HOME=/local/s3052249/hive
                export DERBY_HOME=/local/s3052249/derby

                export PATH=$PATH:$HADOOP_HOME/bin
                export PATH=$PATH:$HADOOP_HOME/sbin
                export PATH=$PATH:$HIVE_HOME/bin

                mapred job -history {i}
            """,
        )
        with open(results / (i + ".txt"), "w+") as f:
            f.write(r)

    print(ids)
