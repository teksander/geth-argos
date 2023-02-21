from scipy import stats
from pylab import show, xlabel, ylabel, title, plot, fill_between, ylim, legend
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
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
lca_sample_set = ['lca_0_15_lnb03','lca_1_15_lnb03','lca_2_15_lnb03','lca_3_15_lnb03','lca_4_15_lnb03', 'lca_5_15_lnb03']
#wmsr_sample_set =['wmsr_5_0_15_lnb03', 'wmsr_3_1_15_lnb','wmsr_3_2_15_lnb','wmsr_3_3_15_lnb','wmsr_3_4_15_lnb', 'wmsr_3_5_15_lnb']
sc_sample_set = ['sc_0_15_lnb03b','sc_1_15_lnb03','sc_2_15_lnb03','sc_3_15_lnb03','sc_4_15_lnb03', 'sc_5_15_lnb03']
wmsr_sample_set =['wmsr_5_0_15_lnb03','wmsr_5_1_15_lnb03','wmsr_5_2_15_lnb03','wmsr_5_3_15_lnb03','wmsr_5_4_15_lnb03','wmsr_5_5_15_lnb03']
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
                            this_data.append((np.linalg.norm(this_consensus-ground_truth)))


                if len(this_data)>0:
                    this_avg = np.mean(np.array(this_data))
                    this_exp_data.append(this_avg)
            print(np.mean(this_exp_data), np.var(this_exp_data))
            if this_exp_data:
                exp_data_ens.append(this_exp_data)
    return exp_data_ens

fig, axs = plt.subplots(1,1)

compare_item = ['LCA','W-MSR', 'Our method']
this_env = 'Door-Panda-OSC-POSE-SEED59'
this_fault = 'stuck_at_zero'
plt.rcParams.update({'font.size': 20})
box_colors = ['darkkhaki', 'royalblue', 'mediumseagreen', 'lightsalmon']

lca_data_ens = extract_consensus_sample_set(lca_sample_set)
wmsr_data_ens = extract_consensus_sample_set(wmsr_sample_set)
sc_data_ens = extract_consensus_sample_set(sc_sample_set)
random_dists=[]
xtick_dist = []
for malicious_num in range(6):
    for item_idx, this_item in enumerate(compare_item):
        this_data=[]
        if this_item == 'LCA':
            this_data = lca_data_ens[malicious_num]
            #random_dists.append('')
        elif this_item == 'W-MSR':
            this_data = wmsr_data_ens[malicious_num]
            random_dists.append(str(malicious_num))
        elif this_item == 'Our method':
            this_data = sc_data_ens[malicious_num]
            #random_dists.append('')
        bp = axs.boxplot(this_data, positions = [(4*malicious_num)+item_idx], widths = 0.6)
        if this_item == 'W-MSR':
            xtick_dist.append((4*malicious_num)+item_idx)
        # Now fill the boxes with desired colors
        num_boxes = 1
        medians = np.empty(num_boxes)
        for i in range(num_boxes):
            box = bp['boxes'][i]
            box_x = []
            box_y = []
            for j in range(5):
                box_x.append(box.get_xdata()[j])
                box_y.append(box.get_ydata()[j])
            box_coords = np.column_stack([box_x, box_y])
            # Alternate between Dark Khaki and Royal Blue
            axs.add_patch(Polygon(box_coords, facecolor=box_colors[item_idx]))
            axs.set(ylabel='Averaged consensus error')
            axs.set(xlabel='Number of malicious robot')
            # Now draw the median lines back over what we just filled in
            med = bp['medians'][i]
            median_x = []
            median_y = []
            for j in range(2):
                median_x.append(med.get_xdata()[j])
                median_y.append(med.get_ydata()[j])
                axs.plot(median_x, median_y, 'k')
            medians[i] = median_y[0]
            # Finally, overplot the sample averages, with horizontal alignment
            # in the center of each box
axs.set_xticks(xtick_dist)
axs.set_xticklabels(random_dists, rotation=0, fontsize=17)
ax=axs
for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
             ax.get_xticklabels() + ax.get_yticklabels()):
    item.set_fontsize(20)
fig.set_size_inches(13, 7)
fig.tight_layout()


fig.text(0.11, 0.86, 'LCP',
         backgroundcolor=box_colors[0], color='black', weight='roman',
         size=21)
fig.text(0.11, 0.79, 'W-MSR',
         backgroundcolor=box_colors[1],
         color='white', weight='roman', size=21)
fig.text(0.11, 0.72, 'Our method',
         backgroundcolor=box_colors[2],
         color='white', weight='roman', size=21)
plt.savefig('consensus_error.eps', format='eps', bbox_inches='tight', pad_inches=0.1)
plt.show()




