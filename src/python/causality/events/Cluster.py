class Cluster(object):
    def __init__(self, centriod, score, members):
        self.centriod = centriod
        self.score = score
        self.members = members

    def has_member(self, m):
        return m in members

    def to_string(self):
        return '{} {} {}'.format(self.centriod, self.score, ' '.join(self.members))