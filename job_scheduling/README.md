# Workflow to create the simulation results

Each script usage and detailed information about the algorithm can be found in the README.md file. Here we show the steps taken to get the figures and data used in the experiments. The folder structure has the following format:
- `original_logs` contains a folder for each system with the original scheduler log files [downloaded]. Each folder stores one csv file for each year of execution.
- `joblist_priority_logs` contains a folder for each system-year pair. Each folder stores individual files for the jobs in each timeframe studied (default one file with job list for a 7 day period)
- `result-stats` contains a folder and a file for each system-year pair. Each folder stores individual files with the simulated schedule for each timeframe studied. The file stores summary results for each syste-year-scheduler tuple.
- `logs` contains two files for each system-year pair, one for the output of running the job creation script (joblist-\*.log) and one for the output of running the simulation script (sim-\*.log)
                    

The scripts used to run the simulations are the following:
```
|_ create_joblist_from_logs.py [Step 2]
   |_ traces_analysis.py [Used only inside the create_joblist_from_logs.py script]
|_ simulateScheduling.py [Step 3]
|_ plot_stats.py
|_ generate_simulation_logs.sh
```

_Details on how to run all the scripts and a description of all configuration options can be found in the `documentation` folder in the root of the repo._


### Steps

**1. Dowload log files** from: [https://reports.alcf.anl.gov/data/index.html](https://reports.alcf.anl.gov/data/index.html).
In our example, the files are stored in the `original_logs` folder.

**2. Split the jobs** in a 7 day timeframe and create a joblist for each timeframe.

```bash
$ python create_joblist_from_logs.py original_logs/mira/ANL-ALCF-DJC-MIRA_20160101_20161231.csv -n mira2016

original_logs/mira/ANL-ALCF-DJC-MIRA_20160101_20161231.csv CORES to NODES requested: {16.0}
number of jobs : 54907
submissions makespan : 428.09 days
execution makespan : 366.15 days
average number of cores : 37976.791301655525
average requested time : 12114.18 seconds
average execution time : 7183.36 seconds
average number of cores simultaniously used : 652560.2571865052
average wait time in the queue: 99948.02016136376
median wait time in the queue: 11270.0
Small jobs size: 2048 512.0 49152.0
Small jobs: 39322 12.463209075379108
Large jobs size: 4096
Large jobs: 5402 70.70141102657006
Dividing jobs based on (2048 4096) procs with a time granularity of 7 days
Total jobs: 54907 (low 39322 medium 10183 high 5402)
```

Statistic images are created in `stats_mira2016.jpg`. Example image with statistics:
![stats_mira2016](https://github.com/user-attachments/assets/9f8d27be-b302-4cb4-bb32-e3f7444e269c)

**3. Run simulations**

Using the `simulateScheduling.py` script, three types of scheduing strategies are going to be simulated.

- EasyBF using priorities (PriorityBF) and generate stats for this scheduling strategy
```
python simulateScheduling.py joblist_priority_logs/mira2019/mira2019_joblist_20.csv 49152 -n mira2019-20 --generate-jpg
```

- Classic EasyBF (no priority information is used to schedule jobs, the priorities are used to generate statistics)
```
python simulateScheduling.py joblist_priority_logs/mira2019/mira2019_joblist_20.csv 49152 -n mira2019-dp-20 --generate-jpg --disable-priority
```

- LJF with backfilling (no priority information is used to schedule jobs, the priorities are used to generate statistics)
```
python simulateScheduling.py joblist_priority_logs/mira2019/mira2019_joblist_20.csv 49152 -n mira2019-dp-20 --generate-jpg --disable-priority --scheduler LJF
```

Plots showing the scheduling from the original log runs (plotting only the jobs scheduled in a given timeframe -- not including jobs that started before and did not finish yet when the timeframe is plotted). E.g for timeframe 20 in the mira logs 2017 from Friday, April 7, 2017 7:59:46 PM to Saturday, April 15, 2017 11:55:43 PM:

<img width="2100" alt="Screenshot 2025-02-28 at 2 32 46 PM" src="https://github.com/user-attachments/assets/23a75360-fe5e-43a5-820c-ba419a3ca56e" />


If the figures were not created when the simulation was run, the `--stats-only` flag can be used to re-generate the statistics and figures for a schedule. E.g. to create the figure for the original schedule or to create a figure for one of the simulations:
```
# for the original schedule
python simulateScheduling.py joblist_priority_logs/mira2019/mira2019_joblist_20.csv 49152 -n mira2019-origin-21 --generate-jpg --stats-only

# for the classic simulation
python simulateScheduling.py result-stats/mira2017/mira2017-20.schedule.csv 49152 -n mira2019-20 --generate-jpg --stats-only
# for the easyBF simulation
python simulateScheduling.py result-stats/mira2017/mira2017-easyBF-20.schedule.csv 49152 -n mira2019-easyBF-20 --generate-jpg --stats-only
```

**4. Plot statistics across all systems and all years**

Regenerating the stats and the schedule jpgs can be done from the existing logs generated by the simulation. Example for mira simulation for 2017 week 20 when using easyBF:
```
python simulateScheduling.py result-stats/mira2017/mira2017-easyBF-20.schedule.csv 49152 -n mira2019-easyBF-20 --generate-jpg --stats-only
```

In order to plot the statistics, the ` plot_stats.py` is used. To generate stats across all systems:
```
python plot_stats.py procs.csv result-stats/*/*.schedule.csv -n all
```

This will create the following figures (`all-Utilization-System.jpg`, `all-p0-ResponseTime-System.jpg`, `all-p1-ResponseTime-System.jpg`, `all-p2-ResponseTime-System.jpg`):
<img width="757" alt="Screenshot 2025-03-02 at 10 07 58 AM" src="https://github.com/user-attachments/assets/0121b991-3393-4189-a109-c860a825eaba" />

Results per year for each system can be plotting using the following command:
```
$ python plot_stats.py procs.csv result-stats/theta-gpu202*/*.schedule.csv -n theta-gpu
```

## Batch runs of simulations

To generate all the jobs and simulations for a given system, the batch script can be ran:
```
$ bash generate_simulation_logs.sh theta-gpu
```
