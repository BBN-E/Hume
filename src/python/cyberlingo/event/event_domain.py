from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


class EventDomain(object):
    """An abstract class representing the event types and event roles we have in a particular domain"""
    __metaclass__ = ABCMeta

    def __init__(self, event_types, event_roles, entity_types):
        """
        :type event_types: list[str]
        :type event_roles: list[str]
        """
        self.event_types = dict()
        self.event_types_inv = dict()
        self._init_event_type_indices(event_types)

        self.event_roles = dict()
        self.event_roles_inv = dict()
        self._init_event_role_indices(event_roles)

        self.entity_types = dict()
        self.entity_types_inv = dict()
        self._init_entity_type_indices(entity_types)

    @abstractmethod
    def domain(self):
        """Returns a string representing the current event domain"""
        pass

    def _init_entity_type_indices(self, entity_types):
        """
        :type entity_types: list[str]
        """
        for i, et in enumerate(entity_types):
            self.entity_types[et] = i
            self.entity_types_inv[i] = et
        self.entity_types['None'] = len(entity_types)
        self.entity_types_inv[len(entity_types)] = 'None'

    def _init_event_type_indices(self, event_types):
        """
        :type event_types: list[str]
        """
        for i, et in enumerate(event_types):
            self.event_types[et] = i
            self.event_types_inv[i] = et
        self.event_types['None'] = len(event_types)
        self.event_types_inv[len(event_types)] = 'None'


    def _init_event_role_indices(self, event_roles):
        """
        :type event_roles: list[str]
        """
        for i, er in enumerate(event_roles):
            self.event_roles[er] = i
            self.event_roles_inv[i] = er
        self.event_roles['None'] = len(event_roles)
        self.event_roles_inv[len(event_roles)] = 'None'

    def get_entity_type_index(self, entity_type):
        if entity_type in self.entity_types.keys():
            return self.entity_types[entity_type]
        else:
            raise ValueError('Input entity_type "%s" is not in the set of known entity_types: %s' % (entity_type, ','.join(self.entity_types.keys())))

    def get_event_type_index(self, event_type):
        """
        :type event_type: str
        Returns:
            int
        """
        if event_type in self.event_types.keys():
            return self.event_types[event_type]
        else:
            raise ValueError('Input event_type "%s" is not in the set of known event_types: %s' % (event_type, ','.join(self.event_types.keys())))

    def get_event_type_from_index(self, index):
        if index in self.event_types_inv.keys():
            return self.event_types_inv[index]
        else:
            raise ValueError('Input event_type_index %d is not in the set of known event_types: %s' % (index, ','.join(self.event_types_inv.keys())))

    def get_event_role_index(self, event_role):
        """
        :type event_role: str
        Returns:
            int
        """
        if event_role in self.event_roles.keys():
            return self.event_roles[event_role]
        else:
            raise ValueError('Input event_role "%s" is not in the set of known event_roles: %s' % (event_role, ','.join(self.event_roles.keys())))

    def get_event_role_from_index(self, index):
        if index in self.event_roles_inv.keys():
            return self.event_roles_inv[index]
        else:
            raise ValueError('Input event_role_index %d is not in the set of known event_roles: %s' % (index, ','.join(self.event_roles_inv.keys())))

class AceDomain(EventDomain):
    EVENT_TYPES = [ 'Life.Be-Born', 'Life.Die', 'Life.Marry', 'Life.Divorce', 'Life.Injure',
                    'Transaction.Transfer-Ownership', 'Transaction.Transfer-Money',
                    'Movement.Transport',
                    'Business.Start-Org', 'Business.End-Org', 'Business.Declare-Bankruptcy', 'Business.Merge-Org',
                    'Conflict.Attack', 'Conflict.Demonstrate',
                    'Contact.Meet', 'Contact.Phone-Write',
                    'Personnel.Start-Position', 'Personnel.End-Position', 'Personnel.Nominate', 'Personnel.Elect',
                    'Justice.Arrest-Jail', 'Justice.Release-Parole', 'Justice.Charge-Indict', 'Justice.Trial-Hearing',
                    'Justice.Sue', 'Justice.Convict', 'Justice.Sentence', 'Justice.Fine', 'Justice.Execute',
                    'Justice.Extradite', 'Justice.Acquit', 'Justice.Pardon', 'Justice.Appeal']
    EVENT_ROLES = [ 'Person', 'Place', 'Buyer', 'Seller', 'Beneficiary', 'Price',
                    'Artifact', 'Origin', 'Destination', 'Giver', 'Recipient', 'Money',
                    'Org', 'Agent', 'Victim', 'Instrument', 'Entity', 'Attacker', 'Target',
                    'Defendant', 'Adjudicator', 'Prosecutor', 'Plaintiff', 'Crime',
                    'Position', 'Sentence', 'Vehicle', 'Time-Within', 'Time-Starting',
                    'Time-Ending', 'Time-Before', 'Time-After', 'Time-Holds', 'Time-At-Beginning', 'Time-At-End']
    ENTITY_TYPES = ['FAC', 'PER', 'LOC', 'GPE', 'ORG', 'WEA', 'VEH', 'Sentence', 'Job-Title', 'Crime', 'Contact-Info',
                    'Numeric', 'Time']

    def __init__(self):
        EventDomain.__init__(self, self.EVENT_TYPES, self.EVENT_ROLES, self.ENTITY_TYPES)

    def domain(self):
        return 'ACE'

