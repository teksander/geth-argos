#!/usr/bin/env python3
# This scipt collects data from the real and simulated robots
# Assumptions:
# - Robot datasets are in folder data/Experiment_<title>/<robotID>
# Options:
# - If a flag is given then the data is plotted for each robot

import time
import os
import shutil
import sys
import pandas as pd
from matplotlib import pyplot as plt
import glob
import numpy as np


def perform_corrections(df):
    df['TIME'] = (1000*df['TIME']).astype(int)
    try:
        df['ESTIMATE'] = pd.to_numeric(df['ESTIMATE'], errors='coerce')
    except KeyError:
        pass

    return df
        

def create_df(experiment, datafile, datadir):
    data_list = []


    for rep_folder in glob.glob('{}/Experiment_{}/*'.format(datadir, experiment)):

        #print(rep_folder)
        rep = rep_folder.split('/')[-1]
        
        for rob_file in glob.glob('{}/*/{}.csv'.format(rep_folder, datafile)):

            rob = rob_file.split('/')[-2]
            
            df = pd.read_csv(rob_file, delimiter=" ")
            df['NREP'] = int(rep.split('-')[-1])
            df['NBYZ'] = int(rep.split('-')[-2][:-3])
            df['NROB'] = int(rep.split('-')[-3][:-3])
            df = perform_corrections(df)
            data_list.append(df)
            
    if data_list:          
        full_df = pd.concat(data_list, ignore_index=True)
        return full_df
    else:
        return None


if __name__ == "__main__":

    # 'Normal' experiments (in contrast to the long run-times below)
    experiments = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9']
    #experiments = ['G3', 'G4']

    # Simulation results
    datadir_sim = '/home/volker/geth-argos/FloorEstimation/results/data'

    # Real robot results
    datadir_real = '/home/volker/final_data_extracted/data'

    setups = ["reality", "simulation"]
    #setups = ["simulation"]

    # Prepare supplementary data folder
    data_folder = "processed_data/"
    if os.path.exists(data_folder):
        shutil.rmtree(data_folder)
    os.makedirs(data_folder)

    # Put README file into the data folder
    shutil.copy2("README.md", data_folder)

    # Prepare folders for raw data
    raw_data = data_folder + "raw_data/"
    raw_data_sim = raw_data + "simulation"
    raw_data_reality = raw_data + "reality"

    shutil.copytree(datadir_sim, raw_data_sim)
    shutil.copytree(datadir_real, raw_data_reality)

    # Prepare folder for aggregated CSV data
    csv_file_folder = data_folder + "csv_aggregated/"

    os.makedirs(csv_file_folder)

    for EXP in experiments:
        
        file_name_base = csv_file_folder + "combined_" + EXP
        file_name_png = file_name_base + ".png"
        file_name_csv = file_name_base + ".csv"

        if not os.path.exists(csv_file_folder):
            os.makedirs(csv_file_folder)

        with open(file_name_csv, "w") as f: 

            print("NROB NBYZ NREP TIME MAXTIME MEAN AVGESTIMATE SETUP", file=f)
            
            for setup in setups:

                if setup == "reality":
                    datadir = datadir_real
                elif setup == "simulation":
                    datadir = datadir_sim

                # Collect data
                df = create_df(EXP, 'sc', datadir)
                df_estimate = create_df(EXP, 'estimate', datadir)

                if df is not None and df_estimate is not None:

                    df['TIME'] = pd.to_numeric(df['TIME'])

                    groups = df.groupby(['NROB', 'NBYZ', 'NREP'])
                    groups_estimate = df_estimate.groupby(['NROB', 'NBYZ', 'NREP'])

                    average_estimates = []

                    for x, run in groups_estimate:
                        print(x)
                        #print(run['NROB'], run['NBYZ'], run['NREP'])
                        average_estimate = np.mean(run.groupby('ID').last()['ESTIMATE'])
                        average_estimate = round(average_estimate, 4)
                        average_estimates.append(average_estimate)
                        

                    m = 0
                    for x, run in groups:

                        consensus_reached = run[(run['C?'])]

                        consensus_reached_first = consensus_reached.groupby('ID').first()

                        max_time = max(run['TIME']) / 1000

                        if len(consensus_reached_first) != x[0]:
                            print("No CONSENSUS !!!")
                            continue

                        cons_time_idx = consensus_reached_first['TIME'].idxmax()

                        cons_time = consensus_reached_first['TIME'][cons_time_idx] / 1000
                        mean = consensus_reached_first['MEAN'][cons_time_idx]

                        print(x[0], x[1], x[2], cons_time, max_time, mean, average_estimates[m], setup, file=f) 
                        m = m + 1




    # # Long run-time experiments
    # experiments = ['G7', 'G8']

    # setups = ["reality"]

    # for EXP in experiments:

    #     file_name_base = "combined_" + EXP
    #     file_name_png = file_name_base + ".png"
    #     file_name_csv = file_name_base + ".csv"

    #     for setup in setups:

    #         if setup == "reality":
    #             datadir = datadir_real
    #         elif setup == "simulation":
    #             datadir = datadir_sim


    #     # Collect data
    #     df = create_df(EXP, 'extra', datadir)
    #     #print(df[, ["TIME", "CHAINDATASIZE"]])
    #     print(x[0], x[1], x[2], cons_time, mean, setup, file=f) 


    # Connectivity experiments
    experiments = ['G5', 'G6', 'G9']

    setups = ["reality"]


    for EXP in experiments:

        connectivity_folder = data_folder + "average_connectivity/"

        if not os.path.exists(connectivity_folder):

            os.makedirs(connectivity_folder)

        file_name_base = "peers_" + EXP
        file_name_csv = connectivity_folder + file_name_base + ".csv"

        with open(file_name_csv, "w") as f: 

            print("NROB NBYZ NREP CONNECTIVITY SETUP", file=f)    


            for setup in setups:

                if setup == "reality":
                    datadir = datadir_real
                elif setup == "simulation":
                    datadir = datadir_sim


            # Collect data
            df = create_df(EXP, 'buffer', datadir)

            if df is not None:

                df['TIME'] = pd.to_numeric(df['TIME'])

                groups = df.groupby(['NROB', 'NBYZ', 'NREP'])

                for x, run in groups:

                    # TODO: Calculate average connectivity here
                    average_connectivity = sum(run['#BUFFER']) / len(run['#BUFFER'])
                    print(x[0], x[1], x[2], average_connectivity, setup, file=f) 



    #shutil.make_archive("all_files", 'zip', data_folder)
    #full_df = pd.concat(data_list, ignore_index=True)
    #return full_df

def tic():
    global tstart
    tstart = time.time()
    
def toc():
    print(time.time()-tstart)
