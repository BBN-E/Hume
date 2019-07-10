from elements.kb_element import KBElement

class OntologyClass(KBElement):
    
    def __init__(self, class_name,parent=None):
        #print "New ontology class: " + class_name
        self.class_name = class_name
        self.children = []
        self.parent = parent

        self.id = None
        self.description = None
        self.examples = []
        self.exemplars = []
        self.sources = []
        self.type_embedding = None
        self.exemplars_embedding = None

    def add_property(self, key, value):
        #print "adding property to: " + self.class_name
        #print str(key) + ": " + str(value)
        self.properties[key] = value
    
    # JSON serialization helper
    def reprJSON(self):
        d = dict()
        d["id"] = str(self.id)
        return d
