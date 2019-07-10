class CauseExObject(object):

    # Serialization helper
    def reprJSON(self):
        d = dict()
        for a, v in self.__dict__.items():
            if v is None:
                continue
            if (hasattr(v, "reprJSON")):
                d[a] = v.reprJSON()
            else:
                d[a] = v
        return d
