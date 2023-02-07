from NeticaPy import Netica
import json
import pandas as pd
import sys
import os
from utilities import MyEnum
import numpy as np

column_mapper = {'SUB_FISH_END-mean': 'Maintaining fisheries for livelihoods (Mean)',
 'SUB_VEG_END-mean': 'Maintain plants for livelihoods (Mean)',
 'LIV_VEG_END-mean': 'Maintain plants for domestic livestock (Mean)',
 'DOM_WAT_END-mean': 'Maintain water for domestic use (Mean)',
 'FLO_ATT_END-mean': 'Flood attenuation services (Mean)',
 'RIV_ASS_END-mean': 'River assimilation capacity (Mean)',
 'WAT_DIS_END-mean': 'Maintain water borne diseases (Mean)',
 'RES_RES_END-mean': 'Resource resilience (Mean)',
 'FISH_ECO_END-mean': 'Maintain fish communities (Mean)',
 'VEG_ECO_END-mean': 'Maintain vegetation communities (Mean)',
 'INV_ECO_END-mean': 'Maintain invertebrate communities (Mean)',
 'REC_SPIR_END-mean': 'Maintain recreation and spiritual act (Mean)',
 'TOURISM_END-mean': 'Maintain tourism (Mean)',
 'SUB_FISH_END-std': 'Maintaining fisheries for livelihoods (Standard Deviation)',
 'SUB_VEG_END-std': 'Maintain plants for livelihoods (Standard Deviation)',
 'LIV_VEG_END-std': 'Maintain plants for domestic livestock (Standard Deviation)',
 'DOM_WAT_END-std': 'Maintain water for domestic use (Standard Deviation)',
 'FLO_ATT_END-std': 'Flood attenuation services (Standard Deviation)',
 'RIV_ASS_END-std': 'River assimilation capacity (Standard Deviation)',
 'WAT_DIS_END-std': 'Maintain water borne diseases (Standard Deviation)',
 'RES_RES_END-std': 'Resource resilience (Standard Deviation)',
 'FISH_ECO_END-std': 'Maintain fish communities (Standard Deviation)',
 'VEG_ECO_END-std': 'Maintain vegetation communities (Standard Deviation)',
 'INV_ECO_END-std': 'Maintain invertebrate communities (Standard Deviation)',
 'REC_SPIR_END-std': 'Maintain recreation and spiritual act (Standard Deviation)',
 'TOURISM_END-std': 'Maintain tourism (Standard Deviation)'}

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
    # print("Please pass in the path to the network file as the first argument")
    # print("Example: python mara_demo.py mara.neta")
    # sys.exit(1)
    path = "neta/limpopo.neta" #default to hardcoded path

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

    #hacky standard deviation approximation. Deriving the standard deviation analytically was too difficult
    samples = 10000
    x = np.linspace(0,100,samples)
    y = np.repeat(beliefs, samples//4)
    std = np.sqrt(np.sum(y*(x-mean)**2)/samples)*2

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




#crate a dataframe with [Catchment,Year,Level,*[*Out x (*Val + ['mean', 'std'])]] as the columns, and Val as the rows
columns = ['Country', 'Catchment', 'Year']
for out in Out:
    for val in Val:
        columns.append(f'{out}-{val}')
    columns.append(f'{out}-mean')
    columns.append(f'{out}-std')
columns_cleaned = [c.replace("b'","").replace("'","") for c in columns]

#constant fields for all values
country = 'South Africa'
catchment = 'Limpopo'
year = 2022


#output results as a single row for each combination of Out x Val and Out x ['mean', 'std']
row = [country, catchment, year]
for out in Out:
    for level in Val:
        belief = N.GetNodeBelief(out, level, net)
        row.append(belief)
    mean, std = get_stats(out, net)
    row.append(mean)
    row.append(std)

results = pd.DataFrame([row], columns=columns_cleaned)
shape = pd.read_csv('shapes/limpopo_0.1degree.csv')
shape = shape[['latitude','longitude','RR']].copy()
shape['Country'] = 'South Africa'
df = pd.merge(shape, results, left_on = ['Country'], right_on = ['Country'])
df = df[df.columns.drop(list(df.filter(regex='Zero|Low|Med|High')))]
df.rename(columns=column_mapper, inplace=True)

#save to csv
print(f'saving to {catchment}.csv')
df.to_csv(f'results/{catchment}.csv', index=False)

#cleanup
N.DeleteNet_bn(net)
res = N.CloseNetica_bn(env, mesg)
print(mesg.decode("utf-8"))
