from enum import Enum, EnumMeta, _EnumDict


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


#TODO: make this into a class
#class NeticaGraph:
#    def __init__(self, neta_path, password=None):
#        ... etc

def num_nodes(net, N):
    """get the number of nodes in a network"""
    return N.LengthNodeList_bn(N.GetNetNodes_bn(net))

def net_itr(net, N):
    """iterator over the nodes in a network"""
    nodes = N.GetNetNodes_bn(net)
    
    for i in range(N.LengthNodeList_bn(nodes)):
        yield N.NthNode_bn(N.GetNetNodes_bn(net), i)

def node_name(node, N):
    """get the name of a node"""
    return N.GetNodeName_bn(node)

def node_type(node, N):
    """get the type of a node"""
    return N.GetNodeType_bn(node)

def node_kind(node, N):
    """get the kind of a node"""
    return N.GetNodeKind_bn(node)

def get_node_num_states(node, N):
    """get the number of states of a node cane take on, or 0 if it is a continuous node"""
    return N.GetNodeNumberStates_bn(node)

def get_node_state_name(node, state_index, N):
    """get the name of a state of a node"""
    return N.GetNodeStateName_bn(node, state_index)