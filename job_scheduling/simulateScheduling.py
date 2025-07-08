import pandas as pd
import numpy as np
import sys
import logging
import argparse
import matplotlib.pyplot as plt

import ScheduleFlow

job_color={0: '#1f2f98', 1: '#1ca7ec', 2: '#4adede'}

def consecutive(data, stepsize=1):
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)

def interpol_gantt_chart(df, nb_cores, name, round = None, figsize=(25,10),
                         time_divider='seconds_to_hours', x_max = -1):
    # if x_max is not set, show the entire duration of the log
    if x_max == -1:
        x_max = int((df.TimeEnd.max() - df.TimeStart.min()) / 3600)
    plt.rcParams.update({'font.size': 18})
    fig, ax = plt.subplots(figsize=figsize)
    ft = np.array(df.TimeEnd)
    cr = np.array(df.NodesRequested, dtype = int)
    # ss = np.array(df.QueuedTimestamp)
    st = np.array(df.TimeStart)
    pr = np.array(df.Priority)

    sorted_arguments = np.argsort(st)

    st = st[sorted_arguments]
    ft = ft[sorted_arguments]
    cr = cr[sorted_arguments]
    pr = pr[sorted_arguments]
    # ss = ss[sorted_arguments]

    if round is not None:
        ft.round(decimals=round)
        # cr.round(decimals=round)
        # ss.round(decimals=round)
        st.round(decimals=round)

    if time_divider == 'seconds_to_hours':
        ft /= 3600
        st /= 3600
        plt.xlabel('Time (Hours)')
    plt.ylabel('Cores')

    min_start_time = np.amin(st)
    max_finish_time = np.amax(ft)
    # plt.xlim(left = 0, right = max_finish_time - min_start_time)
    plt.xlim(left = 0, right = x_max)
    plt.ylim(bottom = 0, top = nb_cores)

    timestamps = np.unique(np.concatenate((ft,st)))
    cores_used = -np.ones(shape=(len(timestamps), nb_cores), dtype = int)

    for i in range(len(cr)):

        position_of_concerned_timestamps = np.logical_and(st[i] <= timestamps, timestamps < ft[i] )
        concerned_timestamps = cores_used[position_of_concerned_timestamps]
        free_cores = np.all(concerned_timestamps == -1, axis = 0)

        ind_free_cores = np.argwhere(free_cores)[:,0]
        if len(ind_free_cores) < cr[i]:
            print('NOT ENOUGH CORES !! at time', st[i], ":", cr[i], "limit", len(ind_free_cores))
            raise 'NOT ENOUGH CORES !!'


        affected_cores = ind_free_cores[:cr[i]]

        cores_used[np.ix_(position_of_concerned_timestamps, affected_cores)] = i

        splitted_cores_list = consecutive(affected_cores)
        for ccores in splitted_cores_list:
            ax.add_patch(plt.Rectangle((st[i] - min_start_time, ccores[0]), ft[i] - st[i], len(ccores), edgecolor = 'red', facecolor = job_color[pr[i]] ))

    plt.savefig("%s" %(name))
    return cores_used

# create scheduler jobs from a priority analysis list
def add_jobs(df, sim, disable_priority):
    for i in range(len(df)):
        processing_units = df.iloc[i]["NodesRequested"]
        submission_time = df.iloc[i]["QueuedTimestamp"]
        execution_time = df.iloc[i]["Runtime"]
        request_time = df.iloc[i]["WallTimeRequested"]
        p = df.iloc[i]["Priority"]
        if disable_priority:
            p = 0
        job = ScheduleFlow.Application(
                int(processing_units),
                int(submission_time),
                int(execution_time),
                [int(request_time)],
                priority=int(p), name="J"+str(i))
        sim.add_application(job)
    return sim

def write_to_file_execution_log(filename, df, execution_log):
    df["TimeStart"] = [0.]*len(df)
    df["TimeEnd"] = [0.]*len(df)
    for job in execution_log:
        idx = int(job.name[1:])
        df.loc[idx, "TimeStart"] = execution_log[job][0]
        df.loc[idx, "TimeEnd"] = execution_log[job][1]
    df.to_csv(filename+".schedule.csv")
    return df

# compute statistics only for the portion of the log that can give objective metrics
# ts_start indicates the moment there are more jobs that availability in the system
# i.e. when the job start > submission time
# ts_end indicates the moment there are no more jobs submitted in the system
def filter_log(df, time_start, time_end):
    df = df[(df.TimeEnd > 0) & (df.TimeStart > 0)]
    for priority in df.Priority.unique():
        print(" - Jobs with priority", priority, "count",
              len(df[df.Priority==priority]))
    # the first time a job is not starting imediatly after being scheduled
    if time_start == -1:
        time_start = 0
        if len(df[df.QueuedTimestamp < df.TimeStart]) > 0:
            time_start = df[df.QueuedTimestamp < df.TimeStart]["TimeStart"].min()
    # The last moment there are enough jobs in the system to keep the procs busy
    if time_end == -1:
        time_end = df["QueuedTimestamp"].max()
    print("Generating stats between timestamps %s and %s" %(
        time_start, time_end))
    print("Duration: %.2f hours" %((time_end - time_start)/3600))
    df = df[(df.TimeEnd >= time_start) & (df.TimeStart < time_end)]

    # Update start time for jobs starting before the analysis timeframe
    df.loc[df['TimeStart'] < time_start, 'QueuedTimestamp'] = df['QueuedTimestamp'] + time_start - df['TimeStart']
    df.loc[df['TimeStart'] < time_start, 'TimeStart'] = time_start
    # Update end time for the last jobs to the analysis timeframe
    df.loc[df['TimeEnd'] > time_end, 'TimeEnd'] = time_end
    print("Sanity check: should be the same:", df["TimeEnd"].max() - df["TimeStart"].min(), time_end - time_start)
    return df

# the script can use the rule above to filter the log or use custom values
def generate_stats(df_all, numNodes, name, verbose, generateJPG,
                   time_start=-1, time_end=-1):
    df = filter_log(df_all, time_start, time_end)
    time_start = df["TimeStart"].min()
    time_end = df["TimeEnd"].max()
    print("Generate stats for %d jobs in timeframe %.2f hours" % (
        len(df), (time_end - time_start) / 3600))
    # Utilization and makespan for the timeframe
    df["Volume"] = df["NodesRequested"] * df["Runtime"]
    df["ResponseTime"] = df["TimeStart"] - df["QueuedTimestamp"]
    total_volume = (time_end - time_start) * numNodes
    used_volume = df["Volume"].sum()
    print("Utilization: ", used_volume/total_volume)
    print("AvgResponseTime: ", df["ResponseTime"].mean())
    print("MedianResponseTime: ", df["ResponseTime"].median())
    # stats per priority
    response = [0] * 3
    for priority in df.Priority.unique():
        print(priority)
        priority = int(priority)
        if len(df[df.Priority==priority]):
            response[priority] = df[df.Priority==priority]["ResponseTime"].median()

        print("Priority %d : Count %d : AvgResponseTime %.2f" %(
            priority, len(df[df.Priority==priority]),
            response[priority]))

    print(name, time_start, time_end, used_volume/total_volume, df["ResponseTime"].mean(),
          len(df[df.Priority==0]), response[0],
          len(df[df.Priority==1]), response[1],
          len(df[df.Priority==2]), response[2],
          df["ResponseTime"].median())
    if generateJPG:
        # save the scheduling figure
        cu = interpol_gantt_chart(df, numNodes, name+".schedule.jpg", figsize=(20,6)) 

# for each job the log is a list of (time_start, time_end) pair
# return the last entry for each job (successful run)
def filter_failed_runs(execution_log):
    return {job:(execution_log[job][-1][0], execution_log[job][-1][1])
            for job in execution_log}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, help='csv file with jobs')
    parser.add_argument('procs', type=int, help='number of system procs')
    parser.add_argument('--disable-priority', action='store_true',
                        dest='disable_priority', help='discard the priority '
                        'provided in the list of jobs for scheduling')
    parser.add_argument("--scheduler", dest='scheduler',
                        choices=["FCFS", "LJF", "SJF"], default='FCFS')
    parser.add_argument("--backfill", dest='backfill',
                        choices=["easy", "conservative"], default='easy')
    parser.add_argument('-v', '--verbose', type=int, default=0,
                        dest='verbose', help='Verbose level 0-2, '
                             'the higher the more messages (default 0)')
    parser.add_argument('-s', '--start', type=int, dest='start',
                        default=-1, help='End time for the stats')
    parser.add_argument('-e', '--end', type=int, dest='end',
                        default=-1, help='Start time for the stats')
    parser.add_argument('-n', '--name', type=str, default='test',
                        help='Name of the simulation (default test).'
                        ' Scheduling logs will be saved in {name}.schedule.csv.'
                        ' Figures will be saved in {name}.schedule.jpg')
    parser.add_argument('--stats-only', action='store_true', dest="onlyStats",
                        help='DO NOT run simulation, only generate stats')
    parser.add_argument('--generate-jpg', action='store_true', dest="generateJPG",
                        help='Generate a JPG of the schedule')
    args = parser.parse_args()

    if args.onlyStats:
        print("SIMULATION DEACTIVATED ! Run only stats generation on the csv")
        print("Ignoring any other input arguments ...")

    if args.verbose > 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # reqd the jobs
    df = pd.read_csv(args.filename)
    num_processing_units = args.procs
    print(" - Min procs for higherst priority: ", df[df.Priority == 0]["NodesRequested"].min())
    print(" - Procs range for medium priority:", df[df.Priority == 1]["NodesRequested"].min(), df[df.Priority == 1]["NodesRequested"].max())
    print(" - Max procs for lowest priority:", df[df.Priority == 2]["NodesRequested"].max())
    if not args.onlyStats:
        nPriorities = df.Priority.max() + 1
        if args.disable_priority:
            nPriorities = 1

        # create the simulator
        simulator = ScheduleFlow.Simulator(check_correctness=True,
                                           generate_gif=False,
                                           output_file_handler=sys.stdout,
                                           loops = 1)
        # create the scheduler
        backfill_policy = ScheduleFlow.BackfillPolicy.Easy
        if args.backfill == "conservative":
            backfill_policy = ScheduleFlow.BackfillPolicy.Conservative
        scheduler = ScheduleFlow.PriorityPolicy.FCFS
        if args.scheduler == "LJF":
            scheduler = ScheduleFlow.PriorityPolicy.LJF
        if args.scheduler == "SJF":
            scheduler = ScheduleFlow.PriorityPolicy.SJF
        sch = ScheduleFlow.Scheduler(
                ScheduleFlow.System(num_processing_units),
                priority_policy=scheduler,
                backfill_policy=backfill_policy,
                logger=logging.getLogger(__name__),
                priorityLevels = nPriorities)

        # add scheduler and jobs to the simulation
        simulator.create_scenario(sch)
        simulator = add_jobs(df, simulator, args.disable_priority)
        if args.verbose > 0:
            print("Starting simulation on %d jobs | Using priority: %s" % (
                len(df), args.disable_priority))

        print("Scheduling simulation running ...")
        # dictionary, for each job the log is a list of (time_start, time_end)
        execution_log = simulator.run(
                metrics="execution_log")
        # keep only the successful runs
        execution_log = filter_failed_runs(execution_log)

        if args.verbose > 0:
            fist_ts = min([execution_log[job][0] for job in execution_log])
            last_ts = max([execution_log[job][1] for job in execution_log])
            print("%d jobs executed successfully in a timespan of %.2f hours" %(
                len(execution_log.keys()), (last_ts-fist_ts)/3600))
        
        # write the log to a file
        df = write_to_file_execution_log(args.name, df, execution_log)

    # write statistics about the runs
    generate_stats(df, num_processing_units, args.name, (args.verbose > 0),
                   args.generateJPG, time_start=args.start, time_end=args.end)
