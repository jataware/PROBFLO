from NeticaPy import Netica
from enum import Enum, EnumMeta, _EnumDict
import json
import pandas as pd

import pdb


"""
installation process

#python prereqs:
- cython
- pandas
- maybe others?

$ git clone git@github.com:Koenkk/NeticaPy3.git
$ cd NeticaPy3
$ ./compile_linux.sh

#no setup.py so make a simple one
$ echo "from distutils.core import setup
setup(name='NeticaPy', version='1.0', packages=[''], package_dir={'': '.'}, package_data={'': ['NeticaPy.so', 'NeticaEx.o']})
" > setup.py
$ pip install -e .


#to set values, modify input.json. Each field may be any of ['Zero', 'Low', 'Med', 'High', null]
#setting to null keeps that node as its default distribution
#other fields clamp that value to 100%

$ python3 netica_test.py

"""



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



#network file
path = b"hess/O'Brien et al Mara Netica BN.neta"

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
with open('input.json') as f:
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
df.to_csv(f'{catchment}.csv', index=False)




#cleanup
N.DeleteNet_bn(net)
res = N.CloseNetica_bn(env, mesg)
print(mesg.decode("utf-8"))
