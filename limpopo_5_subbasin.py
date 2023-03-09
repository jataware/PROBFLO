from netica import NeticaManager, NeticaGraph, NeticaNode
import json
import pandas as pd
import numpy as np

from os.path import join

import pdb

column_name_map = {
    'SUB_FISH_END': 'Maintaining fisheries for livelihoods',
    'SUB_VEG_END':  'Maintain plants for livelihoods',
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

# levels = ['Zero', 'Low', 'Med', 'High']
# input_nodes = ['DISCHARGE_YR', 'DISCHARGE_LF', 'DISCHARGE_HF', 'DISCHARGE_FD', 'WQ_ECOSYSTEM', 'NO_BARRIERS', 'DOM_WAT_GRO', 'WQ_TREATMENT', 'LANDUSE_SSUP', 'WAT_DIS_HUM', 'WQ_PEOPLE', 'WQ_LIVESTOCK']
output_nodes = ['SUB_VEG_END', 'SUB_FISH_END', 'LIV_VEG_END', 'DOM_WAT_END', 'FLO_ATT_END', 'RIV_ASS_END', 'WAT_DIS_END', 'RES_RES_END', 'FISH_ECO_END', 'VEG_ECO_END', 'INV_ECO_END', 'REC_SPIR_END', 'TOURISM_END']

# these nodes need to be retracted before they can be assigned new values
retract_nodes = {'DISCHARGE_LF', 'DISCHARGE_HF', 'DISCHARGE_YR', 'DISCHARGE_FD'}


subbasins = ['Upper Limpopo', 'Crocodile Marico', 'Elephantes', 'Middle Limpopo', 'Lower Limpopo']
def to_snake_case(name:str):
    return name.lower().replace(' ', '_')


#functions for getting the mean and standard deviation of the output nodes
def get_stats(node:int|str|NeticaNode, net:NeticaGraph):
    """Given a histogram of beliefs (Zero, Low, Medium, High), compute mean and std-dev"""
    #TODO: replace levels with just getting the array of state values
    beliefs = np.array([net.get_node_belief(node, i) for i in range(net.get_num_node_states(node))]) #np.array([N.GetNodeBelief(out, level, net) for level in Val])
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
    neta_dir = 'neta/limpopo_5_subbasin'
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
    for out in output_nodes:
        # for level in levels:
        #     columns.append(f'{column_name_map[out]} ({level})')
        columns.append(f'{column_name_map[out]} (Mean)')
        columns.append(f'{column_name_map[out]} (Standard Deviation)')
    
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
        for out in output_nodes:
            #do Zero, Low, Med, High
            # for level in levels:
            #     belief = net.get_node_belief(out, level)
            #     row.append(belief)
            #add mean and std
            row.extend(get_stats(out, net))

        rows.append(row)

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