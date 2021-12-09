#!/usr/bin/env python3
# This is a scipt to generate plots data collected from the robots
# Assumptions:
# - Robot datasets are in folder data/Experiment_<tittle>/<robotID>
# Options:
# - If a flag is given then the data is plotted for each robot

import time
import os
import sys
import pandas as pd
from matplotlib import pyplot as plt
import glob
from graphviz import Digraph
import pydotplus
import networkx as nx
from networkx.algorithms.shortest_paths.generic import shortest_path as get_mainchain

global tstart

datadir = '/home/eksander/geth-argos/MarketForaging/results/data'
def tic():
    global tstart
    tstart = time.time()
def toc():
    print(time.time()-tstart)
    
def create_df(experiment, logfile):
    df_list = []
    csvfile_list = sorted(glob.glob('%s/experiment_%s/*/*/%s.csv' % (datadir, experiment, logfile)))

    for csvfile in csvfile_list:
        
        df = pd.read_csv(csvfile, delimiter=" ")
        df['NREP'] = csvfile.split('/')[-3]
        
#         df['NROB'] = csvfile.split('/')[-2]
#         df = perform_corrections(df)
        df_list.append(df)
        
    if df_list:
        full_df = pd.concat(df_list, ignore_index=True)
        return full_df
    else:
        return None

def perform_corrections(df):
    df['TIME_M'] = (1000*df['TIME']).astype(int)
    return df


# Construct digraph
def create_digraph(df):
    # Default settings for blockchain viz
    digraph = Digraph(comment='Blockchain', 
                      edge_attr={'arrowhead':'none'},
                      node_attr={'shape': 'record', 'margin': '0', 'fontsize':'9', 'height':'0.35', 'width':'0.35'}, 
                      graph_attr={'rankdir': 'LR', 'ranksep': '0.1', 'splines':'ortho'})
    

#     df.apply(lambda row : digraph.node(row['HASH'], str(row['BLOCK'])), axis = 1)
    digraph.node(df['PHASH'].iloc[0], '<f0> {} | <f1> {}'.format(df['PHASH'].iloc[0][2:6], 'Genesis'))
    df.apply(lambda row : digraph.node(row['HASH'], '<f0> {} | <f1> {}'.format(row['HASH'][2:6], str(row['BLOCK']))), axis = 1)
    df.apply(lambda row : digraph.edge(row['PHASH'], row['HASH']), axis = 1)
    
    return digraph

def convert_digraph(digraph):
    return nx.nx_pydot.from_pydot(pydotplus.graph_from_dot_data(digraph.source))

# Remove childless blocks
def trim_chain(df, levels=1):
    sub_df = df
    while levels:
        sub_df = sub_df.query('HASH in PHASH')
        levels -= 1
    return sub_df

def paths_longer_than(paths, n):
    return [x for x in paths if len(x)>=n]

def nodes_in_paths(paths):
    return [item for sublist in paths for item in sublist]