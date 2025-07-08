import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as ss
import pandas as pd

def number_of_cores_used(df):
    start = np.array(df.TimeStart)
    end = np.array(df.TimeEnd)
    cores_requested = np.array(df.CoresRequested)
    start_arg = np.argsort(np.array(start))
    end_arg = np.argsort(np.array(end))

    si, ei = 0, 0
    times, cores_used = [min(start)], [0]

    while max(si, ei) < len(df):
        if start[start_arg[si]] < end[end_arg[ei]]:
            times.append(start[start_arg[si]])
            cores_used+= [cores_used[-1] + cores_requested[start_arg[si]]]
            si += 1
        else:
            times.append(end[end_arg[ei]])
            cores_used+= [cores_used[-1] - cores_requested[end_arg[ei]]]
            ei += 1
    while si < len(df):
            times.append(start[start_arg[si]])
            cores_used+= [cores_used[-1] + cores_requested[start_arg[si]]]
            si += 1
    while ei < len(df):
            times.append(end[end_arg[ei]])
            cores_used+= [cores_used[-1] - cores_requested[end_arg[ei]]]
            ei += 1 
    return np.array(times), np.array(cores_used)

def workload_in_queue(df):
    queue = np.array(df.QueuedTimestamp)
    start = np.array(df.TimeStart)
    rt = np.array(df.Runtime)
    cores_requested = np.array(df.CoresRequested)
    queue_arg = np.argsort(queue)
    start_arg = np.argsort(start)

    qi, si = 0, 0
    times, queue_work = [min(df.QueuedTimestamp)], [0]

    while max(qi, si) < len(df):
        if queue[queue_arg[qi]] <= start[start_arg[si]]:
            times.append(queue[queue_arg[qi]])
            queue_work+= [queue_work[-1] + rt[queue_arg[qi]] * cores_requested[queue_arg[qi]]]
            qi += 1
        else:
            times.append(start[start_arg[si]])
            queue_work+= [queue_work[-1] - rt[start_arg[si]] * cores_requested[start_arg[si]]]
            si += 1
    while qi < len(df):
            times.append(queue[queue_arg[qi]])
            queue_work+= [queue_work[-1] + rt[queue_arg[qi]] * cores_requested[queue_arg[qi]]]
            qi += 1
    while si < len(df):
            times.append(start[start_arg[si]])
            queue_work+= [queue_work[-1] - rt[start_arg[si]] * cores_requested[start_arg[si]]]
            si += 1 
    return np.array(times), np.array(queue_work)

def tasks_in_queue(df):
    queue = np.array(df.QueuedTimestamp)
    start = np.array(df.TimeStart)
    time_requested = np.array(df.WallTimeRequested)
    cores_requested = np.array(df.CoresRequested)
    queue_arg = np.argsort(queue)
    start_arg = np.argsort(start)

    qi, si = 0, 0
    times, queue_work = [min(df.QueuedTimestamp)], [0]

    while max(qi, si) < len(df):
        if queue[queue_arg[qi]] < start[start_arg[si]]:
            times.append(queue[queue_arg[qi]])
            queue_work+= [queue_work[-1] + 1]
            qi += 1
        else:
            times.append(start[start_arg[si]])
            queue_work+= [queue_work[-1] - 1]
            si += 1
    while qi < len(df):
            times.append(queue[queue_arg[qi]])
            queue_work+= [queue_work[-1] + 1]
            qi += 1
    while si < len(df):
            times.append(start[start_arg[si]])
            queue_work+= [queue_work[-1] - 1]
            si += 1 
    return np.array(times), np.array(queue_work)

def nombre_de_taches_en_cour(df):
    start = np.array(df.TimeStart)
    end = np.array(df.TimeEnd)
    start_arg = np.argsort(np.array(start))
    end_arg = np.argsort(np.array(end))

    si, ei = 0, 0
    times, current_compute = [min(start)], [0]

    while max(si, ei) < len(df):
        if start[start_arg[si]] < end[end_arg[ei]]:
            times.append(start[start_arg[si]])
            current_compute+= [current_compute[-1] + 1]
            si += 1
        else:
            times.append(end[end_arg[ei]])
            current_compute+= [current_compute[-1] - 1]
            ei += 1

    while si < len(df):
            times.append(start[start_arg[si]])
            current_compute+= [current_compute[-1] + 1]
            si += 1
    while ei < len(df):
            times.append(end[end_arg[ei]])
            current_compute+= [current_compute[-1] - 1]
            ei += 1 
    
    return np.array(times), np.array(current_compute)

def print_trace_studie(df):
    rt = np.array(df.Runtime)
    wt = np.array(df.WallTimeRequested)
    qt = np.array(df.QueuedTimestamp)
    et = np.array(df.TimeEnd)
    st = np.array(df.TimeStart)
    wqt = np.array(df.WaitTimeInQueue)
    cr = np.array(df.CoresRequested)
    print('number of jobs :', len(df))
    print('submissions makespan :', np.round((np.max(qt) - np.min(qt))/(3600*24), 2), 'days' ) 
    print('execution makespan :', np.round((np.max(et) - np.min(st))/(3600*24), 2), 'days' )
    print('average number of cores :', np.mean(cr))
    print('average requested time :', np.round(np.mean(wt), 2), 'seconds')
    print('average execution time :', np.round(np.mean(rt), 2), 'seconds')
    print('average number of cores simultaniously used :', np.sum(cr*rt)/(np.max(et) - np.min(st)))
    print('average wait time in the queue:', df.WaitTimeInQueue.mean())
    print('median wait time in the queue:', np.median(wqt))
    print()
    print(np.round(np.mean(rt > wt)*100, 2), "% of the jobs have a runtime higher than their walltime")
    x = np.mean(rt == 0)
    print(np.round(100*x, 2), "% of the jobs have a runtime equal to zero")
    x = np.mean(rt < 0)
    print(np.round(100*x, 2), "% of the jobs have a runtime smaller than zero")
    #print(df[['TimeStart', 'QueuedTimestamp', 'WaitTimeInQueue']])

def plot_trace_study(df, figsize = (40, 40), labelsize = 30, system_name="test"):
    rt = np.array(df.Runtime)
    wt = np.array(df.WallTimeRequested)
    qt = np.array(df.QueuedTimestamp)
    et = np.array(df.TimeEnd)
    st = np.array(df.TimeStart)
    wqt = np.array(df.WaitTimeInQueue)
    cr = np.array(df.CoresRequested)

    plt.figure(figsize = figsize)
    plt.rc('xtick', labelsize=labelsize)
    plt.rc('ytick', labelsize=labelsize) 
    plt.rc('axes', labelsize=labelsize) 
    plt.rc('figure', titlesize=labelsize)

    plt.subplot(441)
    moments_array, cores_used_array = number_of_cores_used(df)
    repeat_moments_array = np.repeat(moments_array, 2)[1:]
    repeat_cores_used_array = np.repeat(cores_used_array, 2)[:-1]
    plt.plot((repeat_moments_array - np.min(repeat_moments_array))/(3600*24), repeat_cores_used_array)
    plt.ylabel('cores used')
    plt.xlabel("time (in days)")

    plt.subplot(422)
    moments_array, cores_used_array = workload_in_queue(df)
    repeat_moments_array = np.repeat(moments_array, 2)[1:]
    repeat_cores_used_array = np.repeat(cores_used_array, 2)[:-1]
    plt.plot((repeat_moments_array - np.min(repeat_moments_array))/(3600*24), repeat_cores_used_array)
    plt.ylabel('workload in queue')
    plt.xlabel("time (in days)")

    plt.subplot(423)
    moments_array, cores_used_array = nombre_de_taches_en_cour(df)
    repeat_moments_array = np.repeat(moments_array, 2)[1:]
    repeat_cores_used_array = np.repeat(cores_used_array, 2)[:-1]
    plt.plot((repeat_moments_array - np.min(repeat_moments_array))/(3600*24), repeat_cores_used_array)
    plt.ylabel('number of tasks running')
    plt.xlabel("time (in days)")

    plt.subplot(424)
    cond = np.logical_not(rt > wt)
    rt, wt = rt[cond], wt[cond]
    plt.hist(rt/wt, bins = 100, density =True, stacked = True)
    plt.title('distribution of the values of runtime/walltime', fontsize = labelsize)

    plt.subplot(425)
    plt.hist(cr, bins = np.geomspace(max(1, np.amin(cr)), np.amax(cr), 101), density = False)
    plt.xscale('log')
    plt.title('distribution of the number of cores asked', fontsize = labelsize)

    plt.subplot(426)
    plt.hist(wt, bins = np.geomspace(max(1, min(wt)), max(wt), 101), density = False)
    plt.xscale('log')
    plt.title('distribution of the walltime', fontsize = labelsize)

    plt.subplot(427)
    plt.hist(rt, bins = np.geomspace(max(1, min(rt)), max(rt), 101), density = False)
    plt.xscale('log')
    plt.title('distribution of the runtime', fontsize = labelsize)

    plt.subplot(428)
    plt.hist(rt, bins = np.geomspace(max(1, min(wqt)), max(wqt), 101), density = False)
    plt.xscale('log')
    plt.title('distribution of the wait time', fontsize = labelsize)
    plt.savefig("stats_%s.jpg" %(system_name))

def mult_plot_queue_workload(df_list, figsize = (30, 85), labelsize = 30, title = None, titlesize = 15):

    plt.rc('xtick', labelsize=labelsize)
    plt.rc('ytick', labelsize=labelsize) 
    plt.rc('axes', labelsize=labelsize) 
    plt.rc('figure', titlesize=labelsize)
    for i,df in enumerate(df_list):

        plt.subplot(int(np.ceil(len(df_list)/2)), 2, i+1)
        moments_array, cores_used_array = workload_in_queue(df)
        # moments_array, cores_used_array = tasks_in_queue(df)
        repeat_moments_array = np.repeat(moments_array, 2)[1:]
        repeat_cores_used_array = np.repeat(cores_used_array, 2)[:-1]
        plt.plot((repeat_moments_array - np.min(repeat_moments_array))/(3600*24), repeat_cores_used_array)
        if title is not None:
            plt.title(title[i], fontsize = titlesize)
        plt.ylabel('Workload in queue')
        plt.xlabel("time (in days)")

def mult_plot_number_of_cores_used(df_list, figsize = (30, 85), labelsize = 30, title = None, titlesize = 15):

    plt.rc('xtick', labelsize=labelsize)
    plt.rc('ytick', labelsize=labelsize) 
    plt.rc('axes', labelsize=labelsize) 
    plt.rc('figure', titlesize=labelsize)
    for i,df in enumerate(df_list):

        plt.subplot(int(np.ceil(len(df_list)/2)), 2, i+1)
        moments_array, cores_used_array = number_of_cores_used(df)
        # moments_array, cores_used_array = tasks_in_queue(df)
        repeat_moments_array = np.repeat(moments_array, 2)[1:]
        repeat_cores_used_array = np.repeat(cores_used_array, 2)[:-1]
        plt.plot((repeat_moments_array - np.min(repeat_moments_array))/(3600*24), repeat_cores_used_array)
        if title is not None:
            plt.title(title[i], fontsize = titlesize)
        plt.ylabel('number of cores used')
        plt.xlabel("time (in days)")
