import os
import csv

import numpy
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pylab import show, xlabel, ylabel, title, plot, fill_between, ylim, legend
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

def extract_all_consensus(consensus_str):
    consensus_list= []
    for this_consensus in consensus_str.split(' ('):
        this_consensus.split(', ')
        corx = float(this_consensus.split(', ')[10])/1e5
        if this_consensus.split(', ')[11].endswith('\n'):
            cory = float(this_consensus.split(', ')[11][:-3])/1e5
        else:
            cory = float(this_consensus.split(', ')[11][:-2]) / 1e5
        total_deposit = float(this_consensus.split(', ')[5])
        support_deposit = float(this_consensus.split(', ')[6])
        if support_deposit/total_deposit>0.5 and float(this_consensus.split(', ')[3])!=3:
            consensus_list.append([corx,cory,support_deposit/total_deposit])
    return consensus_list

def plot_with_confidence(data, get_x=lambda x:x, alpha=0.95):
  """Plots data means and confidence intervals."""
  xs = range(len(data))
  plot([get_x(x) for x in xs], np.mean(np.array(data), 1))
  lower_conf, upper_conf = [], []
  for x in xs:
    points = data[x]
    lower, upper = stats.t.interval(
        alpha,
        len(points) - 1,
        loc=np.mean(points),
        scale=stats.sem(points))
    lower_conf.append(lower)
    upper_conf.append(upper)

def fill_with_confidence(data, get_x=lambda x:x, alpha=0.95):
    xs = range(len(data))
    lower_conf, upper_conf = [], []
    for x in xs:
        points = data[x]
        lower, upper = stats.t.interval(
            alpha,
            len(points) - 1,
            loc=np.mean(points),
            scale=stats.sem(points))
        lower_conf.append(lower)
        upper_conf.append(upper)
    fill_between([get_x(x) for x in xs], lower_conf, upper_conf, alpha=0.3)

experiment_main_foler = './results/data/161501_paper_config_more_log_90min'

#this_exps = ['lca_0_6_16_lnb','lca_0_3_16_lnb', 'lca_0_0_16_lnb', 'wmsr_3_6_16_lnb', 'wmsr_3_3_16_lnb', 'wmsr_3_0_16_lnb', 'sc_5_15_lnb','sc_3_16_lnb','sc_0_16_lnb']
#this_exps = ['sc_0_15_lnb','sc_1_15_lnb','sc_2_15_lnb','sc_3_15_lnb','sc_4_15_lnb', 'sc_5_15_lnb']
#this_exps = ['lca_3_0_15_lnb','lca_3_1_15_lnb','lca_3_2_15_lnb','lca_3_3_15_lnb','lca_3_4_15_lnb', 'lca_3_5_15_lnb']
lca_sample_set = ['lca_0_15_lnb03','lca_1_15_lnb03','lca_2_15_lnb03','lca_3_15_lnb03','lca_4_15_lnb03', 'lca_5_15_lnb03']
#wmsr_sample_set =['wmsr_5_0_15_lnb03', 'wmsr_3_1_15_lnb','wmsr_3_2_15_lnb','wmsr_3_3_15_lnb','wmsr_3_4_15_lnb', 'wmsr_3_5_15_lnb']
sc_sample_set = ['sc_0_15_lnb03b','sc_1_15_lnb03','sc_2_15_lnb03','sc_3_15_lnb03','sc_4_15_lnb03', 'sc_5_15_lnb03']
wmsr_sample_set =['wmsr_5_0_15_lnb03','wmsr_5_1_15_lnb03','wmsr_5_2_15_lnb03','wmsr_5_3_15_lnb03','wmsr_5_4_15_lnb03','wmsr_5_5_15_lnb03']
blockchain_num_consensus = [0]
num_robots = 15
best_robots = [1,2,3]
average_robots = [5,6,7,8]
worst_robots = [12,13,14]
def extract_consensus_sample_set(robot_set):
    exp_data_ens = []
    this_path = experiment_main_foler
    for exp_time in os.listdir(this_path):
        this_exp_path = os.path.join(this_path, exp_time)
        this_set_data=[]
        for num_robot in robot_set:
            this_data = []
            this_robot_path = os.path.join(this_exp_path, str(num_robot))
            this_csv_path = os.path.join(this_robot_path, 'balance.csv')
            with open(this_csv_path, 'r') as file:
                data = file.readlines()
                for this_line in data[1:]:
                    this_reading =  this_line.split(' ')[2]
                    if this_reading.endswith('\n'):
                        this_data.append(float(this_reading[:-1]))
                    else:
                        this_data.append(float(this_reading))
            this_set_data.append(this_data)

        if len(this_set_data)>0:
            min_len=len(this_set_data[0])
            min_len=800
            for temp_lst in this_set_data:
                if len(temp_lst)<min_len:
                    min_len=len(temp_lst)
            unified_lgh_data = []
            for temp_lst in this_set_data:
                unified_lgh_data.append(temp_lst[:min_len])
            this_avg = np.mean(np.array(unified_lgh_data),axis=0)
            exp_data_ens.append(this_avg)
    return numpy.array(exp_data_ens).T

fig, axs = plt.subplots(1,1)


best_ens = extract_consensus_sample_set(best_robots)
worst_ens = extract_consensus_sample_set(worst_robots)
average_ens = extract_consensus_sample_set(average_robots)
malicious_ens = extract_consensus_sample_set([15])
plot_with_confidence(best_ens, lambda x:x*5)

plot_with_confidence(average_ens, lambda x:x*5)

plot_with_confidence(worst_ens, lambda x:x*5)

plot_with_confidence(malicious_ens, lambda x:x*5)
fill_with_confidence(best_ens, lambda x:x*5)
fill_with_confidence(average_ens, lambda x:x*5)
fill_with_confidence(worst_ens, lambda x:x*5)
fill_with_confidence(malicious_ens, lambda x:x*5)



legend(['3 best robots (no. 1-3)', '4 average robots (no. 6-9)', '3 worst robots (no. 12-14)', 'malicious robot (no. 15)'])
xlabel('ARGoS time steps')
ylabel('Assets balance (ETH)')


fig.set_size_inches(7, 4.5)
fig.tight_layout()
plt.savefig('consensus_balance.pdf', format='pdf', bbox_inches='tight', pad_inches=0.1)
plt.show()
