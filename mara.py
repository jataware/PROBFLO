from NeticaPy import Netica
import json
import pandas as pd
import sys
from utilities import MyEnum


class Val(MyEnum):
    Zero = ()
    Low = ()
    Med = ()
    High = ()

class In(MyEnum):
    TOXICITY_BHN = ()
    SED_BHN = ()
    PATHOGENS_BHN = ()
    DILUTION_MITIGATION = ()
    TREATMENT_DRINKING = ()
    QUANTITY = ()
    DEMAND_BHN = ()
    TREATMENT_WASTEWATER = ()
    AQUATIC_BIO_CUES = ()
    INUNDATION = ()
    RIVER_GEOMORPH = ()
    TOX_ECO = ()
    INVASIVE_SPECIES = ()
    SED_ECO = ()
    IMPORTANCE_ECO = ()
    DILUTION_SALTS_CP = ()
    SALTS_CP = ()
    CROP_DEMAND = ()
    QUALITY_LIVESTOCK = ()
    ANIMALS_TRAMPLING = ()
    DEMAND_LIVESTOCK = ()
    VEG_BANK = ()
    VEG_COVER_WETLAND = ()
    SED_WETLAND = ()
    PLANT_COMMUNITY = ()
    IMPORTANCE_WETLAND = ()
    SAFETY_TOURISTS = ()
    DEMAND_ECOTOURISM = ()

class Out(MyEnum):
    BASIC_HUMAN_NEEDS = ()
    ECOLOGICAL_INTEGRITY = ()
    ECOTOURISM_INDUSTRY = ()
    IRRIGATED_CROP_PRODUCTION = ()
    LIVESTOCK_HERDING_CAPACITY = ()
    WETLAND_CONSERVATION = ()


#netica setup
N=Netica()
mesg=bytearray()
env=N.NewNeticaEnviron_ns(b"",None,b"")
res = N.InitNetica2_bn(env, mesg)



#network file is passed in as the first argument
try:
    path = sys.argv[1]
except IndexError:
    # print("Please pass in the path to the network file as the first argument")
    # print("Example: python mara_demo.py mara.neta")
    # sys.exit(1)
    path = "neta/mara.neta" #default to hardcoded path

#ensure that the network file exists
try:
    with open(path, 'r'):
        pass
except FileNotFoundError:
    print(f"The network file at {path} does not exist")
    sys.exit(1)


#convert path to a byte array
path = path.encode('utf-8')

#debug hardcoded path
# path = b"neta/O'Brien et al Mara Netica BN.neta"

#load the network
net = N.ReadNet_bn(N.NewFileStream_ns(path, env, b""), 0)
N.CompileNet_bn(net)


#manual example
# print(In.TOXICITY_BHN, Val.Zero, N.GetNodeBelief(In.TOXICITY_BHN, Val.Zero, net))
# print(Out.BASIC_HUMAN_NEEDS, Val.Low, N.GetNodeBelief(Out.BASIC_HUMAN_NEEDS, Val.Low, net))

# print(f'updating', In.TOXICITY_BHN, Val.Zero, 'to 1')
# N.EnterFinding(In.TOXICITY_BHN, Val.Zero, net)
# print(In.TOXICITY_BHN, Val.Zero, N.GetNodeBelief(In.TOXICITY_BHN, Val.Zero, net))
# print(Out.BASIC_HUMAN_NEEDS, Val.Low, N.GetNodeBelief(Out.BASIC_HUMAN_NEEDS, Val.Low, net))





# read input from json
with open('configs/mara.json') as f:
    input = json.load(f)

# set input values
for key, value in input.items():
    if value is not None:
        #verify that key is from In enum, and value is from Val enum
        if key in In.__members__ and value in Val.__members__:
            print(f"setting {key} to {value}")
            N.EnterFinding(key.encode('utf-8'), value.encode('utf-8'), net)
        else:
            print("invalid input: ", key, value)





#crate a dataframe with [Catchment,Year,Level,*Out] as the columns, and Val as the rows
columns = ['Country', 'Catchment', 'Year', 'Level', *Out.__members__.keys()]

#constant fields for all values
country = 'Kenya'
catchment = 'Mara'
year = 2022


#loop through all possible values of Level
rows = []
for level in Val:
    row = [country, catchment, year, level]
    for out in Out:
        #get the belief for the output
        belief = N.GetNodeBelief(out, level, net)
        #add the belief to the row
        row.append(belief)

    rows.append(row)
    
df = pd.DataFrame(rows, columns=columns)

#save to csv
print(f'saving to {catchment}.csv')
df.to_csv(f'results/{catchment}.csv', index=False)




#cleanup
N.DeleteNet_bn(net)
res = N.CloseNetica_bn(env, mesg)
print(mesg.decode("utf-8"))
