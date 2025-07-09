# Analyze logs of jobs

The scripts in this folder are used to extract joblists from HPC schedule logs from real systems and to simulate scheduling them in different configurations.

## Create list of jobs parsing scheduling jobs

The script used to extract the list of jobs from a log is `create_joblist_from_logs.py` with the following parameters:
```
$ python create_joblist_from_logs.py -h
usage: create_joblist_from_logs.py [-h] [-n NAME] [-l LOWLIMIT] [-u HIGHLIMIT] [-t TIMEDAYS] filename [filename ...]

positional arguments:
  filename              input CSV file with scheduler logs

options:
  -h, --help            show this help message and exit
  -n, --name NAME       system name
  -l, --lowlimit LOWLIMIT
                        Jobs with procs below this limit will be considered small
  -u, --uplimit HIGHLIMIT
                        Jobs with procs over this limit will be considered large
  -t, --time-granularity TIMEDAYS
                        Time granularity in days for splitting the log into sub-logs (default 7 days)
```

Example usage for the MIRA logs (downloaded from [here](https://reports.alcf.anl.gov/data/mira.html)):
```
$ python create_joblist_from_logs.py original_logs/mira/ANL-ALCF-DJC-MIRA_20200101_20201231.csv -n mira2020
READ original_logs/mira/ANL-ALCF-DJC-MIRA_20200101_20201231.csv df 6833
original_logs/mira/ANL-ALCF-DJC-MIRA_20200101_20201231.csv CORES to NODES requested: {16.0}
Small jobs size: 2048 512.0 49152.0
Small jobs: 4670 23.73694639700476
Large jobs size: 4096
Large jobs: 515 60.236410234241916
Dividing jobs based on (2048 4096) procs with a time granularity of 7 days
Total jobs: 6337 (low 4670 medium 1152 high 515)
Writing file mira2020_joblist_11.csv (1576696313 1577301113) for 17 low, 1 medium and 3 high jobs
Writing file mira2020_joblist_12.csv (1577301113 1577905913) for 9 low, 15 medium and 13 high jobs
Writing file mira2020_joblist_13.csv (1577905913 1578510713) for 470 low, 38 medium and 21 high jobs
Writing file mira2020_joblist_14.csv (1578510713 1579115513) for 290 low, 79 medium and 22 high jobs
Writing file mira2020_joblist_15.csv (1579115513 1579720313) for 240 low, 33 medium and 17 high jobs
Writing file mira2020_joblist_16.csv (1579720313 1580325113) for 295 low, 61 medium and 55 high jobs
Writing file mira2020_joblist_17.csv (1580325113 1580929913) for 399 low, 29 medium and 86 high jobs
Writing file mira2020_joblist_18.csv (1580929913 1581534713) for 522 low, 66 medium and 72 high jobs
Writing file mira2020_joblist_19.csv (1581534713 1582139513) for 621 low, 258 medium and 62 high jobs
Writing file mira2020_joblist_20.csv (1582139513 1582744313) for 356 low, 351 medium and 62 high jobs
Writing file mira2020_joblist_21.csv (1582744313 1583349113) for 860 low, 137 medium and 71 high jobs
Writing file mira2020_joblist_22.csv (1583349113 1583953913) for 591 low, 84 medium and 29 high jobs
```

Read 6833 jobs from the mira log file which are filtered to 6337 valid jobs using a max of 49,152 nodes (and a min of 512) and always 16 cores per node.

If no low or upper limit is used, the default behavior is to use the 80% percentile size in term of number of nodes for the lower limit and the 90% percentile for the higher limit.

In the example, the lower limit gives the jobs with low priority and they represent jobs using less than 2048 nodes.
- There are 4670 low priority jobs that make up 23.7% of the total core hours on Mira in 2020.
- There are 515 high priority jobs that make up 60.2% of the total core hours on Mira in 2020.
- The rest of 1152 jobs are medium priority jobs

By default, the code generates one file for a one week timeframe (7 days). There are logs for 84 days of Mira logs in 2020 that have more than 5 jobs and that have jobs with different priorities.
This means 12 files were be created in the root folder. Each output file has the following format:
```
,Priority,NodesRequested,Runtime,WallTimeRequested,QueuedTimestamp,TimeStart,TimeEnd
0,1,2048.0,8963.0,10800.0,0.0,1577888064.0,1577897027.0
1,0,16384.0,55011.0,86400.0,108062.0,1577920307.0,1577975318.0
2,0,16384.0,481.0,86400.0,108081.0,1578160693.0,1578161174.0
```

## Simulate a scheduling over a list of jobs

The script `simulateScheduling.py` is used to simulate a schduler using [ScheduleFlow](https://github.com/anagainaru/ScheduleFlow) and generate an execution log. `ScheduleFlow` needs to be downloaded and add in the `PYTHONPATH` variable.

`$ export PYTHONPATH=$PYTHONPATH:/path/to/ScheduleFlow`

The script uses the following parameters:
```
$ python simulateScheduling.py -h
usage: simulateScheduling.py [-h] [--disable-priority] [--scheduler {FCFS,LJF,SJF}] [--backfill {easy,conservative}] [-v VERBOSE] [-s START] [-e END] [-n NAME] [--stats-only]
                             [--generate-jpg]
                             filename procs

positional arguments:
  filename              csv file with jobs
  procs                 number of system procs

options:
  -h, --help            show this help message and exit
  --disable-priority    discard the priority provided in the list of jobs for scheduling
  --scheduler {FCFS,LJF,SJF}
  --backfill {easy,conservative}
  -v, --verbose VERBOSE
                        Verbose level 0-2, the higher the more messages (default 0)
  -s, --start START     End time for the stats
  -e, --end END         Start time for the stats
  -n, --name NAME       Name of the simulation (default test). Scheduling logs will be saved in {name}.schedule.csv. Figures will be saved in {name}.schedule.jpg
  --stats-only          DO NOT run simulation, only generate stats
  --generate-jpg        Generate a JPG of the schedule
```

Continuing the example above we can run the simulation script on the logs generated by
```
$ python simulateScheduling.py joblist_priority_logs/mira2020/mira2020_joblist_16.csv 49152 -n mira2022-16 --generate-jpg
 - Min procs for higherst priority:  8192.0
 - Procs range for medium priority: 2048.0 4096.0
 - Max procs for lowest priority: 1024.0
Scheduling simulation running ...
Scenario name : job failures : job response time : job stretch : job utilization : job wait time : system makespan : system utilization :
ScheduleFlow0 : 0.00 : 20881.54 : 18.66 : 0.48 : 9252.59 : 653263.00 : 0.45 :
 - Jobs with priority 1 count 61
 - Jobs with priority 2 count 294
 - Jobs with priority 0 count 55
Generating stats between timestamps 127131.0 and 603418.0
 - Duration: 132.30 hours
Generate stats for 340 jobs in timeframe 132.30 hours
Utilization:  0.5437771763663506
AvgResponsTime:  11608.720588235294
Priority 2 : Count 243 : AvgResponsTime 12703.21
Priority 0 : Count 50 : AvgResponsTime 5686.04
Priority 1 : Count 47 : AvgResponsTime 12250.72
```

The `csv` files created previously in the root folder have been moved to `joblist_priority_logs/mira2020`.

The script reads the csv file and runs the simulation (using the priorities or not using them if `--disable-priority` flag).
The stats are generated between the timeframes given as input paraemeters. If no limits are given,
 - the start time is the first moment when the submission time differs from the start time
 - the end time is the ending of the last job submitted

In our example this timeframe is between timestamps 127131 and 603418 (middle of the second day to the end of the 7th day for a total of 132.3 hours). The script gives stats of utilization and response time for each priority and creates two files:
 - the log file with the start time and end time for each job in {name}.schedule.log
 - A JPG file (if `--generate-jpg` is used) with the schedule generated ({name}.schedule.jpg) :

<img width="1232" alt="Screenshot 2025-02-25 at 3 52 55 PM" src="https://github.com/user-attachments/assets/defb2e7e-27d6-4f54-9179-bc9e6968ac42" />

Dark blue is high priority jobs, light blue are medium priority jobs and light green are low priority jobs.

Using `--disable-priority` the simulation in ScheduleFlow ignores the priorities but the stats will consider them. The last line in the output summaries the statistics:
```
Name	Analysis start	Analysis end	Utilization	AvgResponseTime	P0-Count 	P0-AvgResponseTime	P1-Count 	P1-AvgResponseTime	P2-Count 	P2-AvgResponseTime
mira2022-16 127131.0 603418.0 0.5437771763663506 11608.720588235294 50 5686.04 47 12250.72340425532 243 12703.205761316873
mira2022-noPriority-16 127131.0 603418.0 0.5437771763663506 5253.85294117647 50 7290.62 47 11113.531914893618 243 3701.411522633745
```

The output log has a similar format with the job list csv with updated times for the TimeStart and TimeEnd columns. This log can be used directly to generate the stats skipping the simulation:
```
$ head -n 4 mira2022-16.schedule.csv
,Unnamed: 0,Priority,NodesRequested,Runtime,WallTimeRequested,QueuedTimestamp,TimeStart,TimeEnd
0,0,1,2048.0,8963.0,10800.0,0.0,0.0,8963.0
1,1,0,16384.0,55011.0,86400.0,108062.0,108062.0,163073.0
2,2,0,16384.0,481.0,86400.0,108081.0,108081.0,108562.0

$ python simulateScheduling.py mira2022-16.schedule.csv 49152 --stats-only
SIMULATION DEACTIVATED ! Run only stats generation on the csv
Ignoring any other input arguments ...
 - Min procs for higherst priority:  8192.0
 - Procs range for medium priority: 2048.0 4096.0
 - Max procs for lowest priority: 1024.0
 - Jobs with priority 1 count 61
 - Jobs with priority 2 count 294
 - Jobs with priority 0 count 55
Generating stats between timestamps 127131.0 and 603418.0
 - Duration: 132.30 hours
Generate stats for 340 jobs in timeframe 132.30 hours
Utilization:  0.5437771763663506
AvgResponsTime:  11608.720588235294
Priority 2 : Count 243 : AvgResponsTime 12703.21
Priority 0 : Count 50 : AvgResponsTime 5686.04
Priority 1 : Count 47 : AvgResponsTime 12250.72
```

## Plot the statistics

Once the log with simulation is created (or the original log) containing the submission/start/end and procs fields, the `plot_stats.py` can be used to create the graphs of statistics.

```
$ python plot_stats.py procs.csv result-stats/*/*.csv -n all -m System -h
usage: plot_stats.py [-h] [-n NAME] [-m {SystemYear,System}] procsfile filename [filename ...]

positional arguments:
  procsfile             file with the procs used to simulate all the timeframes
  filename              csv files with jobs

options:
  -h, --help            show this help message and exit
  -n, --name NAME       the name of the output files
  -m, --metric {SystemYear,System}
                        the metric used for the horizontal ax
```

The script can be used to plot aggregated stats on each system or on each system-year. Example usage by aggregating the stats from the logs created across all the simulations:
```
python plot_stats.py procs.csv result-stats/*/*.csv -n all -m System
```
will create 4 jpg files, one with the Utilization given the metric and 3 with the response time for each priority.
```
all-Utilization-System.jpg
all-p0-ResponseTime-System.jpg
all-p1-ResponseTime-System.jpg
all-p2-ResponseTime-System.jpg
```
