import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import numpy as np

# plots will have on vertical the ratio between PriorityBF and EasyBF/LJF
# for the given metric and the timescale on the horizontal
def plot_improvement(df, name, metric="", timescale="", scheduler="EasyBF"):
    if metric not in df.columns:
        print("[Improve] The metric chosen", metric,
              "is not part of the log columns")
        return
    if timescale not in df.columns:
        print("[Improve] The timescale chosen", timescale,
              "is not part of the log columns")
        return
    # create the data to store the ratio for the given metric
    # print(df.tail())
    merged_df = pd.merge(df[df.Scheduler=="PriorityBF"],
                         df[df.Scheduler==scheduler],
                         on=['System', 'Year', 'Week', 'Priority', 'Unnamed: 0'], how='inner')
    merged_df["Ratio"] = merged_df[metric+"_x"] / merged_df[metric+"_y"]
    # print(merged_df.tail())
    
    fig,ax = plt.subplots(figsize=(18,6))
    sns.boxplot(data=merged_df[merged_df.Priority == 0], x=timescale, y="Ratio", whis=(0, 100))
    #sns.barplot(data=merged_df, x=timescale, y="Ratio", hue="Priority") #, log_scale=True)
    ax.set_ylabel("Ratio of %s between PriorityBF and %s" %(metric, scheduler))
    ax.set_xlabel(timescale)
    plt.savefig("%s-ratio-%s-%s.jpg" %(name, scheduler, timescale))
    

# plots will have timescale unit on horizontal ax (week, year or all)
# vertically we plot the given metric (typically makespan or utilization)
def plot_statistics(df, name, metric="", timescale="",
                    groupby="", typeGraph="boxplot"):
    plt.rcParams.update({'font.size': 18})
    if groupby not in df.columns:
        print("[Stats] The groupby column", groupby,
              "is not part of the log columns")
        return
    if metric not in df.columns:
        print("[Stats] The metric chosen", metric,
              "is not part of the log columns")
        return
    if timescale not in df.columns:
        print("[Stats] The timescale chosen", timescale,
              "is not part of the log columns")
        return
    horizontal_entries = len(df[timescale].unique())
    fig,ax = plt.subplots(figsize=(2*horizontal_entries,6))
    if typeGraph == "boxplot":
        sns.barplot(data=df, x=timescale, y=metric, hue=groupby,# whis=(0, 100),
                    palette=['darkorange', 'lightseagreen', 'teal'])#,
                    #showfliers=False)
    if typeGraph == "barplot":
        sns.barplot(data=df, x=timescale, y=metric, hue=groupby,
                    palette=['darkorange', 'lightseagreen', 'teal'])
        # palette=sns.color_palette("rocket"))
    ax.set_ylabel(metric)
    ax.set_xlabel(timescale)
    plt.savefig("%s-%s-%s.jpg" %(name, metric, timescale))

# only keep the entries from when the schdeuler has enough jobs to be busy
# to the last submission time 
def filter_log(df, filename, time_start=-1, time_end=-1):
    # the first time a job is not starting imediatly after being scheduled
    if time_start == -1:
        time_start = df["QueuedTimestamp"].min()
        if len(df[df.QueuedTimestamp < df.TimeStart]) > 0:
            time_start = df[df.QueuedTimestamp < df.TimeStart]["TimeStart"].min()
    # The last moment there are enough jobs in the system to keep the procs busy
    if time_end == -1:
        time_end = df["QueuedTimestamp"].max()
    # print("%s duration: %.2f hours" %(filename, (time_end - time_start)/3600))
    df = df[(df.TimeEnd >= time_start) & (df.TimeStart < time_end)]

    # Update start time and submit time for jobs starting before the analysis timeframe
    df.loc[df['TimeStart'] < time_start, 'QueuedTimestamp'] = df['QueuedTimestamp'] + time_start - df['TimeStart']
    df.loc[df['TimeStart'] < time_start, 'TimeStart'] = time_start
    # Update end time for the last jobs to the analysis timeframe
    df.loc[df['TimeEnd'] > time_end, 'TimeEnd'] = time_end
    return df

def get_scheduler(filename):
    if 'ljf' in filename:
        return 'LJF'
    if 'easy' in filename:
        return 'EasyBF'
    return 'PriorityBF'

# extract from: result-stats/theta-gpu2020/theta-gpu2020-10.schedule.csv
# extract also from: result-stats/theta2020/theta2020-10.schedule.csv
# as well as result-stats/theta2020/theta-gpu2020-easyBF-0.schedule.csv
def get_system(filename, sch):
    # does not work for theta-gpu
    # return filename.split("-")[1][:-4].split("/")[-1]
    if sch == "PriorityBF":
        return filename.split(".")[0].split("-")[-2].split("/")[-1][:-4]
    return filename.split(".")[0].split("-")[-3].split("/")[-1][:-4]

def get_week(filename):
    return filename.split(".")[0].split("-")[-1]

def get_year(filename, sch):
    # does not work for theta-gpu
    # return filename.split("-")[1][-4:] 
    if sch == "PriorityBF":
        return filename.split(".")[0].split("-")[-2][-4:]
    return filename.split(".")[0].split("-")[-3][-4:]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('procsfile', type=str, help='file with the procs used to simulate all the timeframes')
    parser.add_argument('filename', type=str, nargs='+', help='csv files with jobs')
    parser.add_argument('-n', '--name', type=str, default="test",
                        help='the name of the output files')
    parser.add_argument("-m", "--metric", dest='metric',
                        choices=["SystemYear", "System"], default='SystemYear',
                        help='the metric used for the horizontal ax')
    parser.add_argument('--no-filter', action='store_false', dest="filter",
                        help='Generate statistics on the whole log (do not filter the beginning and end)')
    args = parser.parse_args()

    procs_df = pd.read_csv(args.procsfile)
    log_list = []
    aggregate_df = pd.DataFrame(
            columns=["System", "Scheduler", "Year", "Week", "Utilization",
                     "CountP0", "CountP1", "CountP2"])
    for filename in args.filename:
        log = pd.read_csv(filename)
        # print("Reading", filename, ":", len(log))

        sch = get_scheduler(filename)
        week = get_week(filename)
        system = get_system(filename, sch)
        year = get_year(filename, sch)

        log["System"] = [system] * len(log)
        log["Scheduler"] = [sch] * len(log)
        log["Year"] = [year] * len(log)
        log["Week"] = [year+'-'+week] * len(log)
        log["ResponseTime"] = (log["TimeStart"] - log["QueuedTimestamp"])/ 3600
        if args.filter:
            log = filter_log(log, filename)

        procs = procs_df[(procs_df.System==system) & (procs_df.Year==int(year))]["Procs"].values[0]
        total_volume = procs * (log.TimeEnd.max() - log.TimeStart.min()) / 3600
        log["Volume"] = (log.NodesRequested * (log.TimeEnd - log.TimeStart)) / 3600
        # append the utilization of the jobs in the file
        aggregate_df.loc[len(aggregate_df)] = [system, sch, year, week,
                                               log.Volume.sum() / total_volume,
                                               len(log[log.Priority == 0]),
                                               len(log[log.Priority == 1]),
                                               len(log[log.Priority == 2])]
        log_list.append(log)
    df = pd.concat(log_list, ignore_index=True)
    print("Read %d files: simulation of %d jobs" %(len(args.filename), len(df)))
    print("  - Amount of jobs for PriorityBF:", len(df[df.Scheduler == "PriorityBF"]))
    print("  - Amount of jobs for EasyBF:", len(df[df.Scheduler == "EasyBF"]))
    print("  - Amount of jobs for LJF:", len(df[df.Scheduler == "LJF"]))
    print("Years in the logs: %d (%s), weeks in the log: %d" %(
        len(df.Year.unique()), df.Year.unique(), len(df.Week.unique())))

    #columns = ['Scheduler', 'Unnamed: 0', 'System', 'Year', 'Week', 'Priority', 'ResponseTime']
    #plot_improvement(df[(df.Scheduler=="PriorityBF") | (df.Scheduler=="EasyBF")][columns],
    #                 args.name, metric="ResponseTime", timescale="Year")
    #plot_improvement(df[(df.Scheduler=="PriorityBF") | (df.Scheduler=="LJF")][columns],
    #                 args.name, metric="ResponseTime", timescale="Year", scheduler="LJF")

    df["SystemYear"] = df.System+" "+df.Year
    aggregate_df["SystemYear"] = aggregate_df.System+" "+aggregate_df.Year
    qoi = args.metric
    for priority in df.Priority.unique():
        df_temp = df[df.Priority == priority]
        plot_statistics(df_temp, args.name+"-p"+str(priority), metric="ResponseTime",
                        timescale=qoi, groupby="Scheduler")
        #plot_statistics(aggregate_df, args.name, metric="CountP"+str(priority),
        #                timescale="SystemYear", groupby="Scheduler", typeGraph="boxplot")
    plot_statistics(aggregate_df, args.name, metric="Utilization",
                    timescale=qoi, groupby="Scheduler", typeGraph="barplot")
    
