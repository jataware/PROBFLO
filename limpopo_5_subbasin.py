from netica import NeticaManager, NeticaGraph, NeticaNode
import json
import pandas as pd
import numpy as np

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
column_measure_map = {
    'mean': 'Mean',
    'std': 'Standard Deviation'
}
def column_mapper(name:str):
    """convert the raw column name to a human readable version"""
    var, measure = name.split('-')
    mapped_var = column_name_map[var]
    mapped_measure = column_measure_map[measure]
    return f"{mapped_var} ({mapped_measure})"


levels = ['Zero', 'Low', 'Med', 'High']
input_nodes = ['DISCHARGE_YR', 'DISCHARGE_LF', 'DISCHARGE_HF', 'DISCHARGE_FD', 'WQ_ECOSYSTEM', 'NO_BARRIERS', 'DOM_WAT_GRO', 'WQ_TREATMENT', 'LANDUSE_SSUP', 'WAT_DIS_HUM', 'WQ_PEOPLE', 'WQ_LIVESTOCK']
output_nodes = ['SUB_VEG_END', 'SUB_FISH_END', 'LIV_VEG_END', 'DOM_WAT_END', 'FLO_ATT_END', 'RIV_ASS_END', 'WAT_DIS_END', 'RES_RES_END', 'FISH_ECO_END', 'VEG_ECO_END', 'INV_ECO_END', 'REC_SPIR_END', 'TOURISM_END']


#TODO: these nodes are not set with Zero, Low, Med, High values. Need to have some method for managing their values.
# probably can extend the netica convenience API to check the type of each node + it's possible input values
# these nodes take 29 binned input values for a distribution range from 0-584.7
skip_nodes = {'DISCHARGE_LF', 'DISCHARGE_HF', 'DISCHARGE_YR', 'DISCHARGE_FD'}


#TODO
{
    'Limpopo Croc': 'crocodile_marico sub-catchment',
    'LIMP-A71L-MAPUN': 'upper limpopo',
    'LIMP-Y30D-PAFUR': 'middle limpopo',
    'LIMP-Y30F-CHOKW': 'lower limpopo',
    'ELEP-Y30C-SINGU': 'elephantes'
}


#functions for getting the mean and standard deviation of the output nodes
def get_stats(node:int|str|NeticaNode, net:NeticaGraph):
    """Given a histogram of beliefs (Zero, Low, Medium, High), compute mean and std-dev"""
    beliefs = np.array([net.get_node_belief(node, level) for level in levels]) #np.array([N.GetNodeBelief(out, level, net) for level in Val])
    centers = np.arange(4)*25 + 12.5
    mean = np.sum(beliefs*centers)

    #hacky standard deviation approximation. Deriving the standard deviation analytically was too difficult
    samples = 10000
    x = np.linspace(0,100,samples)
    y = np.repeat(beliefs, samples//4)
    std = np.sqrt(np.sum(y*(x-mean)**2)/samples)*2

    return mean, std


def main():

    files = [
        'neta/limpopo_5_subbasin/crocodile_marico.neta',
        'neta/limpopo_5_subbasin/elephantes.neta',
        'neta/limpopo_5_subbasin/lower_limpopo.neta',
        'neta/limpopo_5_subbasin/middle_limpopo.neta',
        'neta/limpopo_5_subbasin/upper_limpopo.neta',
    ]

    netica = NeticaManager()
    
    net = netica.new_graph("neta/limpopo.neta")

    # read input from json
    with open('configs/limpopo.json') as f:
        input = json.load(f)

    # set input values from the config file
    for key, value in input.items():
        if key in skip_nodes:
            print(f"skipping {key} because it has been marked as skip")
            continue
        if value is not None:
            #verify that key is from In enum, and value is from Val enum
            if key not in input_nodes:
                raise ValueError(f"invalid input: {key}:{value}. Key must be one of {input_nodes}")
            if value not in levels:
                raise ValueError(f"invalid input: {key}:{value}. Value must be one of {levels}")

            net.enter_finding(key, value, verbose=True)



    #crate a dataframe with [Catchment,Year,Level,*[*output_nodes x (*levels + ['mean', 'std'])]] as the columns, and Val as the rows
    columns = ['Country', 'Catchment', 'Year']
    for out in output_nodes:
        for level in levels:
            columns.append(f'{out}-{level}')
        columns.append(f'{out}-mean')
        columns.append(f'{out}-std')
    columns_cleaned = [c.replace("b'","").replace("'","") for c in columns]

    #constant fields for all values
    country = 'South Africa'
    catchment = 'Limpopo'
    year = 2022


    #output results as a single row for each combination of Out x Val and Out x ['mean', 'std']
    row = [country, catchment, year]
    for out in output_nodes:
        for level in levels:
            # belief = N.GetNodeBelief(out, level, net)
            belief = net.get_node_belief(out, level)
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


if __name__ == '__main__':
    main()