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

experiment_main_foler = ['./results/data/161501_paper_config_more_log_90min', './results/data/161501_paper_config_more_log_30min']

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
def extract_consensus_sample_set():
    exp_data_ens = []

    for this_path in experiment_main_foler:
        for exp_time in os.listdir(this_path):
            this_exp_path = os.path.join(this_path, exp_time)
            this_data = []
            this_data_rcd = []
            for num_robot in [5]:
                this_robot_path = os.path.join(this_exp_path, str(num_robot))
                this_csv_path = os.path.join(this_robot_path, 'consensus_status.csv')
                with open(this_csv_path, 'r') as file:
                    data = file.readlines()
                    lastRow = data[-1]
                    ground_truth_lst = []
                    for idx in range(3):
                        if lastRow.split(' [')[idx+1].split(', ')[0].startswith('['):
                            ground_truth = np.array(
                                [float(lastRow.split(' [')[idx+1].split(', ')[0][1:]), float(lastRow.split(' [')[idx+1].split(', ')[1][:-2])])
                        elif lastRow.split(' [')[idx+1].split(', ')[1].endswith(']]'):
                            ground_truth = np.array([float(lastRow.split(' [')[idx + 1].split(', ')[0]),float(lastRow.split(' [')[idx + 1].split(', ')[1][:-2])])
                        else:
                            ground_truth = np.array([float(lastRow.split(' [')[idx + 1].split(', ')[0]),
                                                     float(lastRow.split(' [')[idx + 1].split(', ')[1][:-2])])
                        ground_truth_lst.append(ground_truth)

                    consensus_list = extract_all_consensus(lastRow.split(' [')[4])

                    for this_consensus_all in consensus_list:
                        this_consensus = np.array([float(this_consensus_all[0]),float(this_consensus_all[1])])
                        min_dist = 1000000000
                        for this_source in ground_truth:
                            this_dis = np.linalg.norm(this_consensus - this_source)
                            if this_dis<min_dist:
                                min_dist = this_dis
                        this_data_rcd.append(float(this_consensus_all[2]))

                        this_data.append(min_dist)
                print(len(this_data))

                if len(this_data)>=10:
                    if this_data_rcd[4] < 0.75:
                        print(this_csv_path)
                    data_avg = []
                    for idx in range(5):
                        data_avg.append(np.mean(this_data_rcd[idx*5:(idx+1)*5]))
                    exp_data_ens.append(this_data_rcd[:5])
    return numpy.array(exp_data_ens).T

fig, axs = plt.subplots(1,1)


consensus_acc = extract_consensus_sample_set()
plot_with_confidence(consensus_acc, lambda x:x+1)
legend(['Mean of RCD with 95% confidence interval'], loc='lower right')

fill_with_confidence(consensus_acc, lambda x:x+1)
axs.boxplot(consensus_acc.T)
plt.rcParams.update({'font.size': 20})
xlabel('Number of confirmed food sources')
ylabel('Relative correct deposit (RCD)')
plt.ylim([0.55, 1.03])
fig.set_size_inches(6, 4)
fig.tight_layout()
plt.savefig('rcd.pdf', format='pdf', bbox_inches='tight', pad_inches=0.1)
plt.show()