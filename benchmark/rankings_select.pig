rmf output/PIG_bench/rankings_select;
a = load '/data/rankings/*' using PigStorage('|') as (pagerank,pageurl,aveduration);
b = filter a by pagerank > 10;
store b into 'output/PIG_bench/rankings_select';
