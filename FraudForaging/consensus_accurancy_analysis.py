import os
import csv
import numpy as np
import matplotlib.pyplot as plt

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
        if support_deposit/total_deposit>0.5:
            consensus_list.append([corx,cory,support_deposit/total_deposit])
    return consensus_list

experiment_main_foler = './results/data/experiment_SingleSourceSupp'

this_exps = ['sc_3', 'wmsr_3_3', 'lca_0_3_2','lca_0_5_2']
blockchain_num_consensus = [0]
num_robots = 15

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
                            this_data.append(np.linalg.norm(this_consensus-ground_truth))
                        except:
                            pass
                    else:
                        ground_truth = np.array([float(lastRow.split(' [')[1].split(', ')[0]), float(lastRow.split(' [')[1].split(', ')[1][:-1])])
                        consensus_list = extract_all_consensus(lastRow.split(' [')[2])
                        this_consensus = np.array([float(consensus_list[this_num][0]), float(consensus_list[this_num][1])])
                        this_data.append(np.linalg.norm(this_consensus-ground_truth))


            if len(this_data)>0:
                this_avg = np.mean(np.array(this_data))
                this_exp_data.append(this_avg)
        print(np.mean(this_exp_data), np.var(this_exp_data))
        if this_exp_data:
            exp_data_ens.append(this_exp_data)

fig = plt.figure(figsize=(10, 7))

# Creating axes instance
fig1, ax1 = plt.subplots()

# Creating plot
bp = ax1.boxplot(exp_data_ens)

# show plot
plt.show()






