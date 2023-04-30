from __future__ import annotations
from netica import NeticaManager, NeticaGraph, NeticaNode
from discharge_lookup import update_net_discharge_scenario
import json
import pandas as pd
import numpy as np

from os.path import join

import pdb

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

# special settings
special_settings = {'DISCHARGE_SCENARIO': update_net_discharge_scenario}


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
    
    # paths for this scenario
    neta_dir = join('neta', 'limpopo_27_subbasin')
    file_map_path = join(neta_dir, 'risk_region_mapping.csv')
    shape_path = join('shapes', 'limpopo_27_0.1degree.csv')
    output_path = join('results', f'limpopo_27_subbasin.csv')

    # load the filename map and shapefile
    file_map_df = pd.read_csv(file_map_path)
    shape = pd.read_csv(shape_path)

    # get the model input settings from the config file
    with open('configs/limpopo_27_subbasin.json') as f:
        config = json.load(f)

    # create a dataframe with [Year, Country, Catchment, Level,*[*output_nodes x ['mean', 'std']]] as the columns, and one row for each site
    # constant fields for all values
    country = 'South Africa'
    catchment = 'Limpopo'
    year = 2022

    columns = ['Year', 'Country', 'Catchment', 'Site Name']
    for output_name in output_nodes.values():
        columns.append(f'{output_name} (Mean)')
        columns.append(f'{output_name} (Standard Deviation)')
    
    # rows to be filled in by running the model
    rows = []
    
 
    # run the model for each site
    for i, row in file_map_df.iterrows():
        neta_path = join(neta_dir, row['Netica File'])
        site = row['Site']

        # load the neta graph for this site
        net = netica.new_graph(neta_path)

        # set input values from the config file for this site
        for key, value in config.items():

            if key in special_settings:
                #config settings that are more complicated than just setting a node value
                special_settings[key](site, net, value)
                continue

            if value is not None:
                # normal set node value in net
                net.enter_finding(key, value, retract=(key in retract_nodes), verbose=True)

        #generate the dataframe row for this site
        row = [year, country, catchment, site]
        for raw_name in output_nodes:
            #add mean and std
            row.extend(get_stats(raw_name, net))

        rows.append(row)

    # merge the results with the shapefile
    results = pd.DataFrame(rows, columns=columns)
    shape['Year'] = year
    shape['Country'] = country
    shape['Catchment'] = catchment
    shape = shape[['Year','latitude','longitude', 'Country', 'Catchment','Site Name']].copy()
    merge_on = ['Site Name', 'Country', 'Year', 'Catchment']
    df = pd.merge(shape, results, left_on=merge_on, right_on=merge_on)
    df = df.rename(columns={'Site Name': 'RR'})
    #save to csv
    print(f'saving to {output_path}')
    df.to_csv(output_path, index=False)


if __name__ == '__main__':
    main()
