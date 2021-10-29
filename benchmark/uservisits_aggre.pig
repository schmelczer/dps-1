rmf output/PIG_bench/uservisits_aggre;
a = load '/data/uservisits/*' using PigStorage('|') as (sourceIP,destURL,visitDate,adRevenue,userAgent,countryCode,languageCode,searchWord,duration);
a1 = foreach a generate sourceIP, adRevenue;
b = group a1 by sourceIP parallel 60;
c = FOREACH b GENERATE group, SUM(a1. adRevenue);
store c into 'output/PIG_bench/uservisits_aggre';

