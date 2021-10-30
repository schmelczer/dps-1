from pathlib import Path
from time import sleep
from typing import List, Optional

from helper import execute_on_host, parallel_map, run_command

node_count = 12


def replace_configuration_values(etc_root: Path, overrides: dict):
    for name in etc_root.glob("*"):
        with open(name, "r") as f:
            content = f.read()
        for k, v in overrides.items():
            content = content.replace(f"{{{k}}}", v)
        with open(name, "w") as f:
            f.write(content)


def stop_node(hostname: str):
    execute_on_host(
        hostname,
        f"""
            export JAVA_HOME=/usr
            export HADOOP_HOME=/local/s3052249/hadoop
            export HIVE_HOME=/local/s3052249/hive
            export DERBY_HOME=/local/s3052249/derby
            export HADOOP_CONF_DIR=/local/s3052249/hadoop/etc/hadoop

            $HADOOP_HOME/sbin/stop-dfs.sh
            rm -rf /local/s3052249
        """,
    )


def clean_up(master: Optional[str] = None, nodes: List[str] = []):
    if master:
        execute_on_host(
            master,
            f"""
                export JAVA_HOME=/usr
                export HADOOP_HOME=/local/s3052249/hadoop
                export HIVE_HOME=/local/s3052249/hive
                export DERBY_HOME=/local/s3052249/derby
                export HADOOP_CONF_DIR=/local/s3052249/hadoop/etc/hadoop

                $HADOOP_HOME/sbin/stop-yarn.sh
                $HADOOP_HOME/bin/mapred --daemon stop historyserver
                $DERBY_HOME/bin/stopNetworkServer
            """,
        )

    if nodes:
        parallel_map(stop_node, nodes, chunk_size=1, concurrency=len(nodes))

    run_command(
        "rm -rf current-etc-hadoop hadoop.tar.gz hadoop hive.tar.gz hive derby.tar.gz derby"
    )


if __name__ == "__main__":
    clean_up()

    run_command(
        "curl https://dlcdn.apache.org/hadoop/common/hadoop-3.3.1/hadoop-3.3.1.tar.gz  --output hadoop.tar.gz"
    )  # latest version
    run_command("tar -xf hadoop.tar.gz && mv hadoop-3.3.1 hadoop")

    run_command(
        "curl https://dlcdn.apache.org/hive/hive-3.1.2/apache-hive-3.1.2-bin.tar.gz  --output hive.tar.gz"
    )  # latest version
    run_command("tar -xf hive.tar.gz && mv apache-hive-3.1.2-bin hive")

    run_command(
        "curl https://dlcdn.apache.org//db/derby/db-derby-10.14.2.0/db-derby-10.14.2.0-bin.tar.gz  --output derby.tar.gz"
    )  # latest version supporting Java 8
    run_command("tar -xf derby.tar.gz && mv db-derby-10.14.2.0-bin derby")

    cwd = run_command("pwd")

    # run_command(f'preserve -# {node_count} -t 00:15:00')

    while True:
        result = "node107 node108 node109 node110 node111 node112 node113 node114 node115 node116 node117 node118\n"  # run_command('preserve -llist | grep $USER')
        cells = result.split()
        if cells[-1] != "-":
            nodes = cells[-node_count:]
            break
        sleep(2)

    print("Nodes: ", nodes)

    master = nodes[0]
    slaves = nodes[1:]

    with open("hadoop/workers", "w") as f:
        f.write("\n".join(slaves))

    run_command("cp -r etc-hadoop current-etc-hadoop")

    replace_configuration_values(
        Path("current-etc-hadoop"),
        {
            "dps1AssignmentMasterNode": "localhost",
            "dps1AssignmentMasterNodeAll": "0.0.0.0",
            "dps1HadoopPath": "/local/s3052249/hadoop",
        },
    )

    run_command("cp current-etc-hadoop/* hadoop/etc/hadoop/")
    run_command("cp etc-hive/* hive/conf/")

    execute_on_host(
        master,
        f"rm -rf /local/s3052249 && mkdir -p /local/s3052249 && cp -r {cwd}/hadoop /local/s3052249",
    )

    run_command("rm -rf current-etc-hadoop && cp -r etc-hadoop current-etc-hadoop")

    replace_configuration_values(
        Path("current-etc-hadoop"),
        {
            "dps1AssignmentMasterNode": master,
            "dps1AssignmentMasterNodeAll": master,
            "dps1HadoopPath": "/local/s3052249/hadoop",
        },
    )

    run_command("cp current-etc-hadoop/* hadoop/etc/hadoop/")

    def start_slaves(hostname: str):
        execute_on_host(
            hostname,
            f"""
                export JAVA_HOME=/usr
                export HADOOP_HOME=/local/s3052249/hadoop
                export HADOOP_CONF_DIR=/local/s3052249/hadoop/etc/hadoop
                export HIVE_HOME=/local/s3052249/hive

                rm -rf /local/s3052249
                mkdir -p /local/s3052249

                cp -r {cwd}/hadoop /local/s3052249
                cp -r {cwd}/hive /local/s3052249

                $HADOOP_HOME/sbin/start-dfs.sh
            """,
        )

    parallel_map(start_slaves, slaves, chunk_size=1, concurrency=len(nodes))

    run_command("rm -rf current-etc-hadoop && cp -r etc-hadoop current-etc-hadoop")
    replace_configuration_values(
        Path("current-etc-hadoop"),
        {
            "dps1AssignmentMasterNode": master,
            "dps1AssignmentMasterNodeAll": master,
            "dps1HadoopPath": f"{cwd}/hadoop",
        },
    )
    run_command("cp current-etc-hadoop/* hadoop/etc/hadoop/")

    try:
        print(nodes)
        execute_on_host(
            master,
            f"""
                export JAVA_HOME=/usr
                export HADOOP_HOME=/local/s3052249/hadoop
                export HADOOP_CONF_DIR=/local/s3052249/hadoop/etc/hadoop
                export HIVE_HOME=/local/s3052249/hive
                export DERBY_HOME=/local/s3052249/derby

                yes | $HADOOP_HOME/bin/hdfs namenode -format
                $HADOOP_HOME/sbin/start-dfs.sh

                cp -r {cwd}/hive /local/s3052249

                $HADOOP_HOME/bin/hadoop fs -mkdir       /tmp
                $HADOOP_HOME/bin/hadoop fs -mkdir -p    /user/hive/warehouse
                $HADOOP_HOME/bin/hadoop fs -chmod g+w   /tmp
                $HADOOP_HOME/bin/hadoop fs -chmod g+w   /user/hive/warehouse

                mkdir -p /local/s3052249/datanode
                mkdir -p /local/s3052249/namenode
                cp -r {cwd}/derby /local/s3052249
                $HADOOP_HOME/sbin/start-yarn.sh
                $HADOOP_HOME/bin/mapred --daemon start historyserver

                $DERBY_HOME/bin/startNetworkServer -h 0.0.0.0 &
                sleep 8

                tail -n +12 /local/s3052249/hive/scripts/metastore/upgrade/derby/hive-schema-3.1.0.derby.sql > /local/s3052249/hive/scripts/metastore/upgrade/derby/hive-schema-3.1.0.derby.sql  # fix NUCLEUS_ASCII bug

                $HIVE_HOME/bin/schematool -dbType derby -initSchema
                $HIVE_HOME/bin/hiveserver2
            """,
        )
    except KeyboardInterrupt:
        print("\nStopping beacuse of keyboard interrupt")

    clean_up(master, nodes)
