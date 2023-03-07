
from NeticaPy import Netica, NewNode as NeticaNode
from typing import Generator
from weakref import finalize
import os

import pdb

#TODO: handling errors that the netica API returns. i.e. self.res

N = Netica()
class NeticaManager:
    def __init__(self, password_varname="NETICA_PASSWORD"):
        # get the password from the environment variable
        password = os.environ.get(password_varname, default="")
        
        # create the netica environment
        self.env = N.NewNeticaEnviron_ns(password.encode('utf-8'), None, b"")
        self.mesg = bytearray()
        self.res = N.InitNetica2_bn(self.env, self.mesg)

        self.finilizer = finalize(self, self.cleanup_env)

    def new_graph(self, path:str) -> "NeticaGraph":
        #ensure that the path exists
        try:
            with open(path, 'r'):
                pass
        except FileNotFoundError:
            raise FileNotFoundError(f"The network file at {path} does not exist")

        path = path.encode('utf-8')

        #load the network
        net = N.ReadNet_bn(N.NewFileStream_ns(path, self.env, b""), 0)
        N.CompileNet_bn(net)

        return NeticaGraph(net, self)
    
    def cleanup_env(self):
        """cleanup the netica environment when the manager is destroyed"""
        res = N.CloseNetica_bn(self.env, self.mesg)
        print(self.mesg.decode("utf-8"))

class NeticaGraph:
    def __init__(self, net, manager:NeticaManager):
        self.net = net
        self.manager = manager

        self.node_names = {self.node_name(i): i for i in range(self.num_nodes())}

        self.finallizer = finalize(self, self.cleanup_net)

    def num_nodes(self) -> int:
        """get the number of nodes in a network"""
        return N.LengthNodeList_bn(N.GetNetNodes_bn(self.net))

    def net_itr(self) -> Generator[NeticaNode, None, None]:
        """iterator over the nodes in a network"""
        nodes = N.GetNetNodes_bn(self.net)
        
        for i in range(N.LengthNodeList_bn(nodes)):
            yield N.NthNode_bn(N.GetNetNodes_bn(self.net), i)

    def get_node_by_index(self, node_idx:int) -> NeticaNode:
        """get a node by its index"""
        return N.NthNode_bn(N.GetNetNodes_bn(self.net), node_idx)
    
    def get_node_by_name(self, node_name:str) -> NeticaNode:
        """get a node by its name. (make sure that the self.node_names dict is populated before calling this)"""
        node_idx = self.node_names[node_name]
        return self.get_node_by_index(node_idx)
    
    def get_node(self, node:int|str|NeticaNode) -> NeticaNode:
        """get a node by either its index or name"""
        if isinstance(node, str):
            return self.get_node_by_name(node)
        elif isinstance(node, int):
            return self.get_node_by_index(node)
        elif isinstance(node, NeticaNode):
            return node
        else:
            raise TypeError(f"node must be either a string, int, or NeticaNode, not {type(node)}")

    def get_node_state(self, node:int|str|NeticaNode, state:int|str) -> str:
        """get the name of a state of a node"""
        node = self.get_node(node)
        if isinstance(state, int):
            return self.get_node_state_name(node, state)
        elif isinstance(state, str):
            all_node_states = [self.get_node_state_name(node, i) for i in range(self.get_node_num_states(node))]
            assert state in all_node_states, f"state {state} not in node {self.node_name(node)}'s states: {all_node_states}"
            return state
        else:
            raise TypeError(f"state must be either a string or int, not {type(state)}")
    
    def node_name(self, node:int|str|NeticaNode) -> str:
        #TODO: -> node comes from net_itr... maybe make this just take in the index of the node?
        """get the name of a node"""
        node = self.get_node(node)
        return N.GetNodeName_bn(node).decode('utf-8')

    def node_type(self, node:int|str|NeticaNode) -> int: #TODO: extract the string this refers to...
        #TODO: -> node comes from net_itr... maybe make this just take in the index of the node?
        """get the type of a node. node may be either the index, or the name of the node"""
        node = self.get_node(node)
        return N.GetNodeType_bn(node)

    def node_kind(self, node:int|str|NeticaNode) -> int: #TODO: extract the string this refers to...
        #TODO: -> node comes from net_itr... maybe make this just take in the index of the node?
        """get the kind of a node"""
        node = self.get_node(node)
        return N.GetNodeKind_bn(node)

    def get_node_num_states(self, node:int|str|NeticaNode) -> int:
        #TODO: -> node comes from net_itr... maybe make this just take in the index of the node?
        """get the number of states of a node cane take on, or 0 if it is a continuous node"""
        node = self.get_node(node)
        return N.GetNodeNumberStates_bn(node)

    def get_node_state_name(self, node:int|str|NeticaNode, state_index) -> str:
        #TODO: -> node comes from net_itr... maybe make this just take in the index of the node?
        """get the name of a state of a node"""
        node = self.get_node(node)
        return N.GetNodeStateName_bn(node, state_index).decode('utf-8')
    
    def enter_finding(self, node:int|str|NeticaNode, state:int|str, verbose=False):
        node = self.get_node(node)
        node_name = self.node_name(node)
        node_state = self.get_node_state(node, state)
        N.EnterFinding(node_name.encode('utf-8'), node_state.encode('utf-8'), self.net)
        if verbose:
            print(f"setting {node_name} to {node_state}")

    def get_node_belief(self, node:int|str|NeticaNode, state:int|str) -> float:
        node = self.get_node(node)
        node_name = self.node_name(node)
        node_state = self.get_node_state(node, state)
        belief = N.GetNodeBelief(node_name.encode('utf-8'), node_state.encode('utf-8'), self.net)
        return belief
    
    def cleanup_net(self):
        """run when the object is garbage collected"""
        N.DeleteNet_bn(self.net)