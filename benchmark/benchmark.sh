#!/usr/bin/env bash

# set up configurations
source benchmark.conf;

# set up the execution log file
if [ -e "$LOG_FILE" ]; then
	timestamp=`date "+%F-%R" --reference=$LOG_FILE`
	backupFile="$LOG_FILE.$timestamp"
	mv $LOG_FILE $backupFile
fi

# set up the timing log file
if [ -e "$TIMING_FILE" ]; then
	timestamp=`date "+%F-%R" --reference=$TIMING_FILE`
	backupFile="$TIMING_FILE.$timestamp"
	mv $TIMING_FILE $backupFile
fi

# output the timing headers
echo 'Timings, grep select, rankings select, uservisits aggregation, uservisits-rankings join' >> $TIMING_FILE

trial=0
while [ $trial -lt $NUM_OF_TRIALS ]; do
	trial=`expr $trial + 1`
	echo "Executing Trial #$trial of $NUM_OF_TRIALS trial(s)..."
   	echo "Trial $trial" >> $TIMING_FILE
    
	# Hive queries
	echo -n "Hive," >> $TIMING_FILE
	for query in ${HIVE_BENCHMARKS[@]}; do
		echo "Running Hive query: $query" | tee -a $LOG_FILE
		timemsg=$($TIME_CMD $HIVE_CMD -f $BASE_DIR/$query 2>&1 | tee -a $LOG_FILE | grep '^Time:')
		echo $timemsg
		echo -n "${timemsg:5}," >> $TIMING_FILE 
	done
    echo  " " >> $TIMING_FILE	
	
	# PIG queries
	echo -n "PIG," >> $TIMING_FILE
	for query in ${PIG_BENCHMARKS[@]}; do
		echo "Running PIG query: $query" | tee -a $LOG_FILE
		timemsg=$($TIME_CMD $PIG_CMD $BASE_DIR/$query 2>&1 | tee -a $LOG_FILE | grep '^Time:')
		echo $timemsg
		echo -n "${timemsg:5}," >> $TIMING_FILE 
	done
    echo " " >> $TIMING_FILE	

	# hadoop queries
	echo -n "Hadoop," >> $TIMING_FILE
	for query in ${!HADOOP_BENCHMARKS[*]}; do
		$HADOOP_CMD ${HADOOP_DATA_PREPARE[$query]} 2>&1 | tee -a $LOG_FILE > /dev/null 
		echo "Running hadoop query: ${HADOOP_BENCHMARKS[$query]}" | tee -a $LOG_FILE
		timemsg=$($TIME_CMD $HADOOP_CMD ${HADOOP_BENCHMARKS[$query]} 2>&1 | tee -a $LOG_FILE | grep '^Time:')
		echo $timemsg
		echo -n "${timemsg:5}," >> $TIMING_FILE 
	done
    echo " " >> $TIMING_FILE	

done # TRIAL

