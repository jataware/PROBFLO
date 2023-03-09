from netica import NeticaManager, NeticaGraph, NeticaNode
import json
import pandas as pd
import numpy as np

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
    
    net = netica.new_graph("neta/limpopo.neta")

    # read input from json
    with open('configs/limpopo.json') as f:
        input = json.load(f)

    # set input values from the config file
    for key, value in input.items():
        if value is not None:
            net.enter_finding(key, value, retract=(key in retract_nodes), verbose=True)



    #crate a dataframe with [Catchment,Year,Level,*[*output_nodes x (*levels + ['mean', 'std'])]] as the columns, and Val as the rows
    columns = ['Country', 'Catchment', 'Year']
    for out in output_nodes.values():
        columns.append(f'{out} (Mean)')
        columns.append(f'{out} (Standard Deviation)')

    #constant fields for all values
    country = 'South Africa'
    catchment = 'Limpopo'
    year = 2022


    #output results as a single row for each combination of Out x Val and Out x ['mean', 'std']
    row = [country, catchment, year]
    for raw_name in output_nodes:
        row.extend(get_stats(raw_name, net))

    # merge the results with the shapefile
    results = pd.DataFrame([row], columns=columns)
    shape = pd.read_csv('shapes/limpopo_0.1degree.csv')
    shape['Year'] = year
    shape['Country'] = country
    shape['Catchment'] = catchment
    shape = shape[['Year','latitude','longitude', 'Country', 'Catchment', 'RR']].copy()
    merge_on = ['Country', 'Year', 'Catchment']
    df = pd.merge(shape, results, left_on=merge_on, right_on=merge_on)

    #save to csv
    print(f'saving to {catchment}.csv')
    df.to_csv(f'results/{catchment}.csv', index=False)


if __name__ == '__main__':
    main()