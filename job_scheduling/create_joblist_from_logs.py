import pandas as pd
import numpy as np
import sys
import argparse
import time
import datetime
import traces_analysis as robin

def filter_invalid_entries(df, file_name):
    # filter entries where the nodes where the nodes 
    df = df[df.NODES_USED == df.NODES_REQUESTED]
    # filter entries where the processors received is 0
    df = df[df.NODES_USED > 0]
    df = df[df.CORES_USED > 0]
    # filter entries where the walltime is at least 1s
    df = df[df.RUNTIME_SECONDS > 1]
    # filter entries where the waltime < requested time
    df.loc[df['RUNTIME_SECONDS'] > df['WALLTIME_SECONDS'], 'WALLTIME_SECONDS'] = df['RUNTIME_SECONDS']
    print(file_name, "CORES to NODES requested:", set(df.CORES_USED/df.NODES_USED))
    return df

def read_log_files(trace_files):
    df_list = []
    for file_name in trace_files:
      df = pd.read_csv(file_name)
      print("READ",file_name,"df",len(df))
      df = filter_invalid_entries(df, file_name)
      df_list.append(df)

    res_list = []
    for df in df_list:
      dict_ = { 'UserID' : np.array(df.USERNAME_GENID),
        'ProjectID' : np.array(df.PROJECT_NAME_GENID),
        'QueueName' : np.array(df.QUEUE_NAME),
        'NodesRequested' : np.array(df.NODES_REQUESTED),
        'CoresRequested' : np.array(df.CORES_REQUESTED),
        'WallTimeRequested' : np.array(df.WALLTIME_SECONDS),
        'QueuedTimestamp' : np.array(df.QUEUED_TIMESTAMP),
        'TimeStart' : np.array(df.START_TIMESTAMP),
        'TimeEnd' : np.array(df.END_TIMESTAMP),
        'EligibleQueueTime' : -np.ones(len(df)),
        'Runtime' : np.array(df.RUNTIME_SECONDS),
        'NodeSecondsUsed' : np.array(df.NODES_USED)*np.array(df.RUNTIME_SECONDS),
        'CoreSecondsUsed' : np.array(df.USED_CORE_HOURS)*3600,
        'NumberofAllocatedProcessors' : np.array(df.CORES_USED)
      }
      res = pd.DataFrame(dict_, index = range(len(df)))

      dates_list = ['QueuedTimestamp', 'TimeStart', 'TimeEnd']
      for col in dates_list:
          res[col] = [ time.mktime(datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timetuple()) for s in np.array(res[col])]
      res_list.append(res)

    res = pd.concat(res_list)
    res = res.sort_values(by=['QueuedTimestamp'])
    res['WaitTimeInQueue'] = res['TimeStart'] - res['QueuedTimestamp']
    return res

def print_extra_stats(df, low_limit, up_limit):
    total_corehours = df.CoreSecondsUsed.sum() / 3600
    print("Average nodes requested:", df.NodesRequested.mean())
    core_hours = df[df.NodesRequested < low_limit]["CoreSecondsUsed"].sum() / 3600
    print("Jobs with nodes <4k:", len(df[df.NodesRequested < low_limit]),
          core_hours * 100 / total_corehours)

    core_hours = df[(df.NodesRequested >= low_limit) &
                    (df.NodesRequested <= up_limit)]["CoreSecondsUsed"].sum() / 3600
    print("Jobs with nodes between_4_and_16k:",
          len(df[(df.NodesRequested >= low_limit) & (df.NodesRequested <= up_limit)]),
          core_hours * 100 / total_corehours)

    core_hours = df[df.NodesRequested > up_limit]["CoreSecondsUsed"].sum() / 3600
    print("Jobs with nodes >16k:", len(df[df.NodesRequested > up_limit]),
          core_hours * 100 / total_corehours)


def print_extra_stats_percentile(df):
    total_corehours = df.CoreSecondsUsed.sum() / 3600
    procs = np.array(df.NodesRequested)
    # get the 60% percentile of job size
    threshold_small = int(np.percentile(procs, 80))
    print("Small jobs size:", threshold_small, min(procs), max(procs))
    core_hours = df[df.NodesRequested < threshold_small]["CoreSecondsUsed"].sum() / 3600
    print("Small jobs:", len(df[df.NodesRequested < threshold_small]),
          core_hours * 100 / total_corehours)

    threshold_large = int(np.percentile(procs, 90))
    print("Large jobs size:", threshold_large)
    core_hours = df[df.NodesRequested > threshold_large]["CoreSecondsUsed"].sum() / 3600
    print("Large jobs:", len(df[df.NodesRequested > threshold_large]),
          core_hours * 100 / total_corehours)
    return threshold_small, threshold_large

def get_queued_jobs(df, start_time, end_time, columns):
    chunk = df[(df["QueuedTimestamp"] >= start_time) &
               (df["QueuedTimestamp"] < end_time)][columns]
    # shift all times so that the first job is submitted at time 0
#        chunk['TimeStart'] = chunk['TimeStart'] - chunk['QueuedTimestamp'].min()
#        chunk['TimeEnd'] = chunk['TimeEnd'] - chunk['QueuedTimestamp'].min()
#        chunk['QueuedTimestamp'] = chunk['QueuedTimestamp'] - chunk['QueuedTimestamp'].min()
    return chunk

def get_running_jobs(df, start_time, end_time, columns):
    chunk = df[(df["TimeEnd"] > start_time) &
               (df["TimeStart"] < end_time)][columns]
    # if the job start before the start of the timeframe
    chunk.loc[chunk['TimeStart'] < start_time, 'TimeStart'] = start_time
    chunk.loc[chunk['TimeEnd'] > end_time, 'TimeEnd'] = end_time
    chunk.loc[chunk['QueuedTimestamp'] < start_time, 'QueuedTimestamp'] = start_time

    # update the execution times and request time to correspond to the new start and end times
    chunk["NewRuntime"] = chunk["TimeEnd"] - chunk["TimeStart"]
    chunk["RuntimeDifference"] = chunk["Runtime"] - chunk["NewRuntime"]
    chunk = chunk[chunk.RuntimeDifference >= 0]
    chunk["WallTimeRequested"] = chunk["WallTimeRequested"] - chunk["RuntimeDifference"]
    chunk = chunk[chunk.NewRuntime > 0]
    # request time was update, so update the runtime to the new runtime
    chunk["Runtime"] = chunk["NewRuntime"]
    return chunk[columns]

# Create joblist from the log files, jobs divided into small, medium, large
# based on procs used (procs < low_limit, etc). Each job type has a different
# priority (large jobs the highest, small the lowest). Time granularity in
# days. Create one file for each x days.
# Output file format: name priority procs walltime request_time
def create_job_file(df, name, low_limit, high_limit,
                    time_granularity=7, allJobs=False):
    print("Dividing jobs based on (%d %d) procs with a time granularity of %d days" %(
        low_limit, high_limit, time_granularity))
    columns = ['Priority', 'NodesRequested', 'Runtime', 'WallTimeRequested',
               'QueuedTimestamp', 'TimeStart', 'TimeEnd']
    # set job priority based on nodes/cores requested
    df["Priority"] = [1] * len(df) # medium priority
    # high priority for large jobs
    df.loc[df['NodesRequested'] > high_limit, 'Priority'] = 0
    # low priority for small jobs
    df.loc[df['NodesRequested'] < low_limit, 'Priority'] = 2
    print("Total jobs: %d (low %d medium %d high %d)" %(
        len(df), len(df[df.Priority == 2]),
        len(df[df.Priority == 1]),
        len(df[df.Priority == 0])))

    df.sort_values(by="QueuedTimestamp", inplace=True)
    start_time = df["QueuedTimestamp"].min()
    while start_time < df["QueuedTimestamp"].max():
        end_time = start_time + time_granularity * 3600 * 24
        # pull out all the jobs between start and end time given each strategy
        if allJobs:
            chunk = get_running_jobs(df, start_time, end_time, columns)
        else:
            chunk = get_queued_jobs(df, start_time, end_time, columns)
        if len(chunk) < 5 or len(chunk.Priority.unique()) == 1:
            # simulate a mix of jobs and more than 5 jobs total
            start_time = end_time
            continue

        fileid = int((start_time - df["QueuedTimestamp"].min()) / (time_granularity * 3600 * 24))
        print("Writing file %s_joblist_%d.csv (%d %d)"
              " for %d low, %d medium and %d high jobs" %(
            name, fileid, start_time, end_time,
            len(chunk[chunk.Priority==2]),
            len(chunk[chunk.Priority==1]),
            len(chunk[chunk.Priority==0])))
        chunk = chunk.reset_index(drop=True)
        chunk.to_csv('%s_joblist_%d.csv' %(name, fileid), index=True)
        start_time = end_time

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str, nargs='+',
                        help='input CSV file with scheduler logs')
    parser.add_argument('-n', '--name', type=str, dest='name',
                        default="test", help='system name')
    parser.add_argument('-l', '--lowlimit', type=int, dest='lowLimit',
                        default=0, help='Jobs with procs below this limit will'
                        ' be considered small')
    parser.add_argument('-u', '--uplimit', type=int, dest='highLimit',
                        default=0, help='Jobs with procs over this limit will'
                        ' be considered large')
    parser.add_argument('-t', '--time-granularity', type=int, dest='timeDays',
                        default=7, help='Time granularity in days for splitting'
                        ' the log into sub-logs (default 7 days)')
    parser.add_argument('--include-all-jobs', action='store_true',
                        dest="includeAllJobs",
                        help='For each timeframe, include all jobs start or'
                        ' end withing the timeframe (default includes only the'
                        ' jobs that are submitted in each timeframe)')
    args = parser.parse_args()

    df = read_log_files(args.filename)
    robin.print_trace_studie(df)
    robin.plot_trace_study(df, system_name=args.name)

    if args.highLimit > 0 and args.lowLimit > 0:
        #print_extra_stats(df, args.lowproc, args.highproc)
        create_job_file(df, args.name, args.lowLimit, args.highLimit,
                        time_granularity=args.timeDays,
                        allJobs=args.includeAllJobs)
    else:
        lowproc, highproc = print_extra_stats_percentile(df)
        create_job_file(df, args.name, lowproc, highproc,
                        time_granularity=args.timeDays,
                        allJobs=args.includeAllJobs)
