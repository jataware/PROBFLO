from NeticaPy import Netica
import json
import pandas as pd
import sys
import os
from utilities import MyEnum
import numpy as np


class Val(MyEnum):
    Zero = ()
    Low = ()
    Med = ()
    High = ()

class In(MyEnum):
    DISCHARGE_YR = ()
    DISCHARGE_LF = ()
    DISCHARGE_HF = ()
    DISCHARGE_FD = ()
    WQ_ECOSYSTEM = ()
    NO_BARRIERS = ()
    DOM_WAT_GRO = ()
    WQ_TREATMENT = ()
    LANDUSE_SSUP = ()
    WAT_DIS_HUM = ()
    WQ_PEOPLE = ()
    WQ_LIVESTOCK = ()

class Out(MyEnum):
    SUB_VEG_END = ()
    SUB_FISH_END = ()
    LIV_VEG_END = ()
    DOM_WAT_END = ()
    FLO_ATT_END = ()
    RIV_ASS_END = ()
    WAT_DIS_END = ()
    RES_RES_END = ()
    FISH_ECO_END = ()
    VEG_ECO_END = ()
    INV_ECO_END = ()
    REC_SPIR_END = ()
    TOURISM_END = ()

#netica setup
N=Netica()
mesg=bytearray()
password = os.environ.get('NETICA_PASSWORD', default="").encode('utf-8')
env=N.NewNeticaEnviron_ns(password,None,b"")
res = N.InitNetica2_bn(env, mesg)



#network file is passed in as the first argument
try:
    path = sys.argv[1]
except IndexError:
    print("Please pass in the path to the network file as the first argument")
    print("Example: python mara_demo.py mara.neta")
    sys.exit(1)

#ensure that the network file exists
try:
    with open(path, 'r'):
        pass
except FileNotFoundError:
    print(f"The network file at {path} does not exist")
    sys.exit(1)


#convert path to a byte array
path = path.encode('utf-8')

#load the network
net = N.ReadNet_bn(N.NewFileStream_ns(path, env, b""), 0)
N.CompileNet_bn(net)


#functions for getting the mean and standard deviation of the output nodes
def get_stats(out, net):
    beliefs = np.array([N.GetNodeBelief(out, level, net) for level in Val])
    centers = np.arange(4)*25 + 12.5
    mean = np.sum(beliefs*centers)
    std = np.sqrt(np.sum(beliefs*(centers-mean)**2))
    return mean, std


# read input from json
with open('configs/limpopo.json') as f:
    input = json.load(f)

# set input values
for key, value in input.items():
    if value is not None:
        #verify that key is from In enum, and value is from Val enum
        if key not in In.__members__:
            print(f"skipping invalid input: {key}:{value}. Key must be one of {In.__members__.keys()}")
            continue
        if value not in Val.__members__:
            print(f"skipping invalid input: {value}:{value}. Value must be one of {Val.__members__.keys()}")
            continue

        print(f"setting {key} to {value}")
        N.EnterFinding(key.encode('utf-8'), value.encode('utf-8'), net)




#crate a dataframe with [Catchment,Year,Level,*Out] as the columns, and Val as the rows
columns = ['Country', 'Catchment', 'Year', 'Node', 'Mean', 'STD', *Val.__members__.keys()]#, *Out.__members__.keys()]

#constant fields for all values
country = 'South Africa'
catchment = 'Limpopo'
year = 2022


# #loop through all possible values of Level
rows = []
for out in Out:
    row = [country, catchment, year, out]
    
    #get the mean and standard deviation of the output
    mean, std = get_stats(out, net)
    row.append(mean)
    row.append(std)
    
    #get the belief for the output for each level: zero, low, med, high
    for level in Val.__members__.values():
        belief = N.GetNodeBelief(out, level, net)
        row.append(belief)   

    #add the row to the dataframe
    rows.append(row)


df = pd.DataFrame(rows, columns=columns)

#save to csv
print(f'saving to {catchment}.csv')
df.to_csv(f'results/{catchment}.csv', index=False)




#cleanup
N.DeleteNet_bn(net)
res = N.CloseNetica_bn(env, mesg)
print(mesg.decode("utf-8"))
