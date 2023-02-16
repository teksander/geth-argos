import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pylab import show, xlabel, ylabel, title, plot, fill_between, ylim, legend

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
        if support_deposit/total_deposit>=0.5:
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
  #fill_between([get_x(x) for x in xs], lower_conf, upper_conf, alpha=0.3)
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

experiment_main_foler = './results/data/experiment_SingleSourceSupp'

#this_exps = ['lca_0_6_16_lnb','lca_0_3_16_lnb', 'lca_0_0_16_lnb', 'wmsr_3_6_16_lnb', 'wmsr_3_3_16_lnb', 'wmsr_3_0_16_lnb', 'sc_5_15_lnb','sc_3_16_lnb','sc_0_16_lnb']
#this_exps = ['sc_0_15_lnb','sc_1_15_lnb','sc_2_15_lnb','sc_3_15_lnb','sc_4_15_lnb', 'sc_5_15_lnb']
#this_exps = ['lca_3_0_15_lnb','lca_3_1_15_lnb','lca_3_2_15_lnb','lca_3_3_15_lnb','lca_3_4_15_lnb', 'lca_3_5_15_lnb']
lca_sample_set = ['lca_3_0_15_lnb','lca_3_1_15_lnb','lca_3_2_15_lnb','lca_3_3_15_lnb','lca_3_4_15_lnb', 'lca_3_5_15_lnb']
wmsr_sample_set =['wmsr_3_0_15_lnb', 'wmsr_3_1_15_lnb','wmsr_3_2_15_lnb','wmsr_3_3_15_lnb','wmsr_3_4_15_lnb', 'wmsr_3_5_15_lnb']
sc_sample_set = ['sc_0_15_lnb','sc_1_15_lnb','sc_2_15_lnb','sc_3_15_lnb','sc_4_15_lnb', 'sc_5_15_lnb']
blockchain_num_consensus = [0]
num_robots = 15

def extract_consensus_sample_set(this_exps):
    exp_data_ens = []
    for exp_name in this_exps:
        for this_num in blockchain_num_consensus:
            this_path = os.path.join(experiment_main_foler,exp_name)
            this_exp_data = []
            for exp_time in os.listdir(this_path):
                this_exp_path = os.path.join(this_path, exp_time)
                this_data = []
                this_consensus = []
                for num_robot in range(num_robots):
                    this_robot_path = os.path.join(this_exp_path, str(num_robot+1))
                    this_csv_path = os.path.join(this_robot_path, 'consensus_status.csv')
                    with open(this_csv_path, 'r') as file:
                        data = file.readlines()
                        lastRow = data[-1]
                        if not exp_name.startswith('sc'): #is a baseline exp data
                            try:
                                this_consensus = np.array([float(lastRow.split(' ')[2][1:-1]), float(lastRow.split(' ')[3][1:-1])])
                                ground_truth = np.array([float(lastRow.split(' ')[4][1:-1]), float(lastRow.split(' ')[5][1:-2])])
                                this_data.append((np.linalg.norm(this_consensus-ground_truth)))
                            except:
                                pass
                        elif num_robot==5:
                            ground_truth = np.array([float(lastRow.split(' [')[1].split(', ')[0]), float(lastRow.split(' [')[1].split(', ')[1][:-1])])
                            consensus_list = extract_all_consensus(lastRow.split(' [')[2])
                            this_consensus = np.array([float(consensus_list[this_num][0]), float(consensus_list[this_num][1])])
                            this_data.append((np.linalg.norm(this_consensus-ground_truth)*(0.44/0.21)))


                if len(this_data)>0:
                    this_avg = np.mean(np.array(this_data))
                    this_exp_data.append(this_avg)
            print(np.mean(this_exp_data), np.var(this_exp_data))
            if this_exp_data:
                exp_data_ens.append(this_exp_data)
    return exp_data_ens

#fig = plt.figure(figsize=(10, 7))

# Creating axes instance
#fig1, ax1 = plt.subplots()
all_samples = [lca_sample_set, wmsr_sample_set, sc_sample_set]
# Creating plot
#bp = ax1.boxplot(exp_data_ens)

exp_data_ens = extract_consensus_sample_set(['sc_0_15_lnb03'])


for this_sample_list in all_samples:
    exp_data_ens = extract_consensus_sample_set(this_sample_list)
    plot_with_confidence(exp_data_ens, lambda x:x)
    #legend('lca', 'lca')
for this_sample_list in all_samples:
    exp_data_ens = extract_consensus_sample_set(this_sample_list)
    fill_with_confidence(exp_data_ens, lambda x:x)
legend(['LCA', 'W-MSR excluding 3 outliers', 'Our method'])
xlabel('Number of malicious agent')
ylabel('Euclidean distance from consensus to ground truth')
#blockchain_num_consensus = [4]
#exp_data_ens = extract_consensus_sample_set(sc_sample_set)
#plot_with_confidence(exp_data_ens, lambda x:x)
# show plot
show()
#plt.show()






