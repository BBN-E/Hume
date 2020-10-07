import os, sys

current_root = os.path.realpath(os.path.join(__file__, os.pardir))

sys.path.append(current_root)


from node import Node
from ontology import Ontology
from ontology import OntologyMapper
import utility as utils
