from netica import NeticaManager, NeticaGraph, NeticaNode
import json
import pandas as pd
import numpy as np

from os.path import join


# list of nodes to record the state of at the end of the simulation
# map from the raw name to what the node should be called in the output csv
output_nodes = {
    'SUB_VEG_END':  'Maintain plants for livelihoods',
    'SUB_FISH_END': 'Maintaining fisheries for livelihoods',
    'LIV_VEG_END':  'Maintain plants for domestic livestock',
    'DOM_WAT_END':  'Maintain water for domestic use',
    'FLO_ATT_END':  'Flood attenuation services',
    'RIV_ASS_END':  'River assimilation capacity',
    'WAT_DIS_END':  'Maintain water borne diseases',
    'RES_RES_END':  'Resource resilience',
    'FISH_ECO_END': 'Maintain fish communities',
    'VEG_ECO_END':  'Maintain vegetation communities',
    'INV_ECO_END':  'Maintain invertebrate communities',
    'REC_SPIR_END': 'Maintain recreation and spiritual act',
    'TOURISM_END':  'Maintain tourism',
}


# these input nodes need to be retracted before they can be assigned new values
retract_nodes = {'DISCHARGE_LF', 'DISCHARGE_HF', 'DISCHARGE_YR', 'DISCHARGE_FD'}

subbasins = [
    '2021-11-16 BN Limpopo CROC_Update CPT_EcoEnd',
    'Bonwapitse_Update CPT_EcoE',
    'Bubye_Update CPT_EcoE',
    'ELEP-Y30C-SINGU_Update CPT_EcoE',
    'GLET-B81J-LRANC_Update CPT_EcoE',
    'LEPH-A50H-SEEKO_Update CPT-EcoE',
    'LETA-B83A-LONEB_Update CPT_EcoE',
    'LIMP-A36C-LIMPK_Update CPT_EcoE',
    'LIMP-A41D-SPANW_Update CPT_EcoE',
    'LIMP-A71L-MAPUN_Update CPT_EcoE',
    'LIMP-Y30D-PAFUR FIXED_Update CPT_EcoE',
    'LIMP-Y30F-CHOKW_Update CPT_EcoE',
    'Lotsane_Update CPT_EcoE',
    'LUVU-A91K-OUTPO_Update CPT_EcoE',
    'Marico_Update CPT_EcoE',
    'MATL-A41D-WDRAAI_Update CPT_EcoE',
    'MOGA-A36D-LIMPK_Update CPT_EcoE',
    'Mokolo_Update CPT_EcoE',
    'Motloutse_Update CPT-EcoE',
    'MWEN-Y20H-MALAP_Update CPT_EcoE',
    'Ngotwane_Update CPT_EcoE',
    'OLIF-B73H-BALUL_Update CPT_EcoE',
    'Olifants_Update CPT_EcoE',
    'SAND-A71K-R508B UPDATED CPTS FOR ECO ENDP',
    'SHAS-Y20B-TULIB_1_Update CPT_EcoE',
    'SHIN-B90H-POACH_Update CPT_EcoE',
    'UMZI-Y20C-BEITB_Update CPT_EcoE',
]

# subbasins = ['Upper Limpopo', 'Crocodile Marico', 'Elephantes', 'Middle Limpopo', 'Lower Limpopo']
def to_snake_case(name:str):
    return name.lower().replace(' ', '_')


#functions for getting the mean and standard deviation of the output nodes
def get_stats(node:int|str|NeticaNode, net:NeticaGraph):
    """Given a histogram of beliefs (Zero, Low, Medium, High), compute mean and std-dev"""
    #TODO: replace beliefs array with just getting the array of state values via the API
    #      also need to make the centers use use the correct number of states, and have the correct bounds
    #      currently it's hardcoded for 4 states (zero, low, medium, high) -> (0, 25, 50, 75, 100)
    beliefs = np.array([net.get_node_belief(node, i) for i in range(net.get_num_node_states(node))])
    centers = np.arange(4)*25 + 12.5
    mean = np.sum(beliefs*centers)

    #hacky standard deviation approximation. Deriving the standard deviation analytically was too difficult
    samples = 10000
    x = np.linspace(0,100,samples)
    y = np.repeat(beliefs, samples//4)
    std = np.sqrt(np.sum(y*(x-mean)**2)/samples)*2

    return mean, std


def main():
    netica = NeticaManager()
    neta_dir = 'neta/limpopo_27_subbasin'
    output_path = join('results', f'limpopo_5_subbasin.csv')

    # get the model input settings from the config file
    with open('configs/limpopo_5_subbasin.json') as f:
        config = json.load(f)

    # create a dataframe with [Year, Country, Catchment, Level,*[*output_nodes x ['mean', 'std']]] as the columns, and one row for each subbasin
    # constant fields for all values
    country = 'South Africa'
    catchment = 'Limpopo'
    year = 2022

    columns = ['Year', 'Country', 'Catchment', 'RR']
    for output_name in output_nodes.values():
        columns.append(f'{output_name} (Mean)')
        columns.append(f'{output_name} (Standard Deviation)')
    
    # rows to be filled in by running the model
    rows = []
    
 
    # run the model for each subbasin
    for subbasin in subbasins:
        neta_path = join(neta_dir, f'{to_snake_case(subbasin)}.neta')

        # load the neta graph for this subbasin
        net = netica.new_graph(neta_path)

        # set input values from the config file for this subbasin
        input = config[to_snake_case(subbasin)]
        for key, value in input.items():
            if value is not None:
                net.enter_finding(key, value, retract=(key in retract_nodes), verbose=True)

        #generate the dataframe row for this subbasin
        row = [year, country, catchment, subbasin]
        for raw_name in output_nodes:
            #add mean and std
            row.extend(get_stats(raw_name, net))

        rows.append(row)

    # merge the results with the shapefile
    results = pd.DataFrame(rows, columns=columns)
    shape = pd.read_csv('shapes/limpopo_0.1degree.csv')
    shape['Year'] = year
    shape['Country'] = country
    shape['Catchment'] = catchment
    shape = shape[['Year','latitude','longitude', 'Country', 'Catchment','RR']].copy()
    merge_on = ['RR', 'Country', 'Year', 'Catchment']
    df = pd.merge(shape, results, left_on=merge_on, right_on=merge_on)

    #save to csv
    print(f'saving to {output_path}')
    df.to_csv(output_path, index=False)


if __name__ == '__main__':
    main()