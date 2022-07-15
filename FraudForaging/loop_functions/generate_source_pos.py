#!/usr/bin/env python3
import os, math
import random
if os.path.exists('loop_functions/source_pos.txt'):
    os.remove('loop_functions/source_pos.txt')
from loop_function_params import *
num_malicious = int(os.environ["NUM2"])
def distance(list1, list2):
    """Distance between two vectors."""
    squares = [(p-q) ** 2 for p, q in zip(list1, list2)]
    return sum(squares) ** .5




def save(path,fs_list):
    l=[]
    for fs in fs_list:
        for coor in fs:
            l.append(coor)
    with open(path,'w') as file:
        file.write(' '.join(map(str,l)))

def load(path):
    fs_list=[]
    with open(path,'r') as file:
        l= list(map(float,file.read().split()))
    for idx in range(generic_params['num_food_source']):
        fs_list.append([l[idx*2],l[idx*2+1]])
    return fs_list

fs_list=[]
while len(fs_list)<(generic_params['num_food_source']+num_malicious):
    print(len(fs_list))
    fs=[0,0]
    minIntSrcDist = 0.3
    interSource = False
    while distance(fs,params['home']['position'])<0.3 or distance(fs,params['home']['position'])>0.8 or not interSource:
        fs = [(random.random()-0.5)*eval(params['environ']['ARENADIMX'])*0.9,
          (random.random() - 0.5) * eval(params['environ']['ARENADIMY'])*0.9]
        interSource = True
        for pt in fs_list:
            if distance(fs,pt)<minIntSrcDist:
                interSource=False
    fs_list.append(fs)


save('loop_functions/source_pos.txt',fs_list)
