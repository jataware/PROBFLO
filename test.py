from netica import NeticaManager, N

import pdb


skip_nodes = ['DISCHARGE_LF', 'DISCHARGE_HF', 'DISCHARGE_YR', 'DISCHARGE_FD']

"""
[Good]
- GetNodeBeliefs_bn(node:NeticaNode)****
---> 


funcs to test:
- EnterFinding_bn
- EnterNodeValue_bn
- EnterIntervalFinding_bn
- GetNodeFinding_bn
- GetNodeExpectedValue_bn


plausible candidates:
- CalcNodeState_bn
- CalcNodeValue_bn
- EnterFinding      -> used in netica.py
- EnterFinding_bn
- EnterNodeValue_bn
- GetNodeAllProbs
- GetNodeBelief
- GetNodeBeliefs_bn
- GetNodeFinding_bn
- GetNodeProbs_bn
- SetNodeFinding
- SetNodeProbs
- SetNodeProbs_bn
- SetNodeValue



"""

#GetNodeBelief
#GetNodeFinding_bn

# netica = NeticaManager()
# net = netica.new_graph("neta/limpopo.neta")


# node = net.get_node('DISCHARGE_LF')

# pdb.set_trace()


# 1


paths = [
    'neta/limpopo.neta',
    'neta/limpopo_5_subbasin/crocodile_marico.neta',
    'neta/limpopo_5_subbasin/elephantes.neta',
    'neta/limpopo_5_subbasin/lower_limpopo.neta',
    'neta/limpopo_5_subbasin/middle_limpopo.neta',
    'neta/limpopo_5_subbasin/upper_limpopo.neta'
]

def main():
    netica = NeticaManager()

    for path in paths:
        graph = netica.new_graph(path)
        for node in graph.net_itr():
            print(f'{graph.get_node_name(node)=}')
            print(f'{graph.get_node_type(node)=}')
            print(f'{graph.get_node_kind(node)=}')
            node_name = graph.get_node_name(node)
            node_by_name = graph.get_node_by_name(node_name)
            print(f'finding: {graph.get_node_finding(node)=}')
            for state in range(graph.get_num_node_states(node)):
                print(f'    {graph.get_node_state_name(node, state)} = {graph.get_node_belief(node, state)}')
            print()
        print('------------------------------------------------------------------')

    # all_names = []
    # for path in paths:
    #     graph = netica.new_graph(path)
    #     names = set()
    #     for node_idx in range(graph.num_nodes()):
    #         print(graph.node_name(node_idx))
    #         names.add(graph.node_name(node_idx))
    #     all_names.append(names)


    #     print()

    # #check if all the names are the same
    # for i in range(len(all_names)):
    #     for j in range(i+1, len(all_names)):
    #         print(f'{i=}, {j=}')
    #         print(f'{all_names[i] - all_names[j]=}')
    #         print(f'{all_names[j] - all_names[i]=}')
    #         print()

    # graph = netica.new_graph("next_stuff/PROBFLO/5_subbasin/2021-11-16 BN Limpopo CROC_Update CPT_EcoEnd.neta")
    # # print(f'{graph.num_nodes()=}')
    # for node_idx in range(graph.num_nodes()): #graph.net_itr():
    #     print(f'name: {graph.node_name(node_idx)}')
    #     # print(f'type: {graph.node_type(node_idx)}')
    #     # print(f'kind: {graph.node_kind(node_idx)}')

    #     # states = [graph.get_node_state_name(node_idx, i) for i in range(graph.get_num_node_states(node_idx))]
    #     # print(f'states: {states}')

    #     # print()

if __name__ == "__main__":
    main()