from NeticaPy import Netica
from enum import Enum, EnumMeta, _EnumDict
import json
import pandas as pd
import sys

#custom enum metaclass so that calling MyEnum.MY_VALUE returns b'MY_VALUE'
#str method should return just the name of the enum value
class MyEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, oldclassdict):
        newclassdict = _EnumDict()
        newclassdict._cls_name = cls
        for key, value in oldclassdict.items():
            if value == ():
                value = key.encode('utf-8')
            newclassdict[key] = value
        return super().__new__(metacls, cls, bases, newclassdict)
class MyEnum(bytes, Enum, metaclass=MyEnumMeta):
    """base class for enum where values are bytes of the enum name"""
    def __str__(self):
        return self.name


class Val(MyEnum):
    Zero = ()
    Low = ()
    Med = ()
    High = ()

class In(MyEnum):
    SUB_FISH_SFLO = ()
    SUB_FISH_SSUP = ()
    SUB_VEG_SFLO = ()
    DOM_WAT_RFLO = ()

class Out(MyEnum):
    LIV_VEG_END = ()
    SUB_FISH_END = ()
    SUB_VEG_END = ()

#netica setup
N=Netica()
mesg=bytearray()
env=N.NewNeticaEnviron_ns(b"+ObrienG/NorthwestU/120-6-A/15312",None,b"")
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
with open('configs/limpopo.json') as f:
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
country = 'South Africa'
catchment = 'Limpopo'
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
