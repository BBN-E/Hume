class KBElement(object):
    def __init__(self):
        pass

    # JSON serialization helper
    def reprJSON(self):
        d = dict()
        for a, v in self.__dict__.items():
            if v is None:
                continue
            elif a == "document":
                d[a] = v.id
            elif (hasattr(v, "reprJSON")):
                d[a] = v.reprJSON()
            else:
                d[a] = v
        return d
