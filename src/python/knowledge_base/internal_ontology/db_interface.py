import sqlite3
from collections import defaultdict
from elements.structured.structured_entity import EntityData
from elements.kb_entity import KBEntity
from elements.kb_mention import KBMention
from ontology_class import OntologyClass
import numpy
from rdflib import URIRef
from shared_id_manager.shared_id_manager import SharedIDManager


class Database(object):

    def __init__(
            self, sqlite_file, internal_ontology, targets, indices, clobber):
        self.io = internal_ontology  # type: internal_ontology.InternalOntology
        self.connection = sqlite3.connect(sqlite_file)
        self.cache = defaultdict(lambda: defaultdict(list))
        self.embed_targets(targets, clobber)
        self.index(indices)

    def embed_targets(self, targets, clobber):
        """
        :param targets: list of triples of (1) table names in which to embed
        (2) column names grouped by (3) a grouping column (PK/FK)
        :type targets: [(str, str, str)]
        :param clobber: whether to clobber existing embeddings
        """

        def embed_group(db, group_embeddings, db_table, group_field, group):
            no_embedding_in_group = len(group_embeddings) == 0
            if no_embedding_in_group:
                # when all else fails, use zero vector
                group_embeddings.append(db.io.make_zeros())
            averaged = db.io.vecs.average_vectors(group_embeddings)
            averaged_str = " ".join([str(dimension) for dimension in averaged])
            _q = """update {} set embedding = "{}" where {} = {}
                 """.format(db_table, averaged_str, group_field, group)
            subcursor = db.connection.cursor()
            try:
                subcursor.execute(_q)
            except sqlite3.OperationalError as e:
                print repr(_q)
                print db_table
                print averaged_str
                print group_field
                print group
                print repr(row[0])
                raise e
            return

        def embed_row(db, e, pkey_value, primary_key, db_table):
            """
            :param e: [numpy.ndarray]
            """
            if len(e) == 0:
                row_embedding = [db.io.make_zeros()]
            else:
                row_embedding = e
            averaged = db.io.vecs.average_vectors(row_embedding)
            averaged_str = " ".join([str(dimension) for dimension in averaged])
            _q = """update {} set embedding = "{}" where {} = {}
                 """.format(db_table, averaged_str, primary_key, pkey_value)
            subcursor = db.connection.cursor()
            subcursor.execute(_q)
            return

        # instead of grouper, use primary key
        #for table, column, grouper in targets:
        for table, column, id_field in targets:
            cursor = self.connection.cursor()
            cursor.execute('pragma table_info({})'.format(table))
            fields = cursor.fetchall()

            # check if embedding exists
            if any([f[1] == 'embedding' for f in fields]):  # 1 is name
                print '{}.{} has already been embedded: '.format(table, column),
                if clobber:
                    print 'clobbering'

                    kept_names = [f[1] for f in fields if f[1] != 'embedding']
                    kept_types = [f[2] for f in fields if f[1] != 'embedding']
                    kept_pkeys = [str(f[5]) for f in fields if f[1] != 'embedding']
                    for i in range(len(kept_pkeys)):
                        if kept_pkeys[i] == '1':
                            kept_pkeys[i] = 'PRIMARY KEY'
                        else:
                            kept_pkeys[i] = ''
                    kept = ','.join(' '.join(z) for z in
                                    zip(kept_names, kept_types, kept_pkeys))
                    kept_names = ','.join(kept_names)
                    script = '''
                             begin transaction; 
                             create temporary table tmp_tab({});
                             insert into tmp_tab select {} from {}; 
                             drop table {};
                             create table {}({});
                             insert into {} select {} from tmp_tab;
                             drop table tmp_tab;
                             commit;
                             '''.format(kept,
                                        kept_names, table,
                                        table,
                                        table, kept,
                                        table, kept_names)
                    cursor.executescript(script)

                else:  # don't clobber and don't re-embed
                    print 'skipping'
                    continue

            # embed
            print "embedding field {} in table {}...".format(column, table)
            q = """alter table {} add column embedding TEXT;""".format(table)
            cursor.execute(q)

            # TODO decide whether to keep averaging all of an entity's names.
            # This is being done because many names in AWAKE will be zero
            # vectors, and we would like to limit the number of arbitrary
            # guesses we make.  To change, stop using the grouper.

            #q = """select t.{}, t.{} from {} t order by {}
            #    """.format(column, grouper, table, grouper)
            q = """select t.{}, t.{} from {} t
                """.format(column, id_field, table)
            cursor.execute(q)
            #print q
            last_identity = None
            embeddings_in_group = []
            count = 0
            ids = 0
            for row in cursor:
                count += 1
                #print count
                #name_to_embed = row[0].encode('ascii', 'backslashreplace')
                embedding = self.io.embed_text(row[0])  # == column
                identity = row[1]
                new_identity = identity != last_identity
                found_embedding = len(embedding) > 0

                # skip this step: using extend instead
                #if found_embedding:
                #    # average the components of this mention
                #    embedding = self.io.vecs.average_vectors(embedding)

                # no longer grouping mentions in db
                """
                # new group to begin embedding: finalize previous embedding
                if new_identity and last_identity is not None:
                    embed_group(self,
                                embeddings_in_group,
                                table,
                                grouper,
                                last_identity)

                    ids += 1
                    #print "updated {} with averaged vec {}".format(last, e)
                    #print "using query:\t{}".format(q)
                    if ids % 2500 == 0:
                        pass
                        #print "{} individuals embedded".format(ids)
                        #print "(most recent: {} with {})".format(last, e)
                        #print "query was:\n\t{}".format(q)

                    # reset group
                    last_identity = identity
                    embeddings_in_group = [embedding] * found_embedding

                # same identity as last embedding: toss it on the pile
                else:
                    embeddings_in_group.extend(embedding)
                """
                embed_row(self, embedding, identity, id_field, table)
                ids += 1

                if count % 5000 == 0:
                    print "{} rows embedded".format(count)

            # no longer grouping mentions in db
            """
            # plus the last row, if not embedded above
            if last_identity is not None and new_identity:
                embed_group(
                    self, embeddings_in_group, table, grouper, last_identity)
            """

            self.connection.commit()

    def index(self, indices):
        """
        :param indices: list of pairs of (1) tables in which to set indices on
        (2) columns
        :type indices: [(str, str)]
        """
        for table, column in indices:
            print 'Indexing column {} in table {}...'.format(column, table)
            cursor = self.connection.cursor()
            cursor.execute("""CREATE INDEX IF NOT EXISTS 
                {}_{}_idx ON {} ( {} )""".format(table, column, table, column))
        self.connection.commit()


class EntityDB(Database):

    def __init__(self, sqlite_file, internal_ontology, clobber):
        # instead of grouper, use primary key
        #embedding_targets = [('altnames', 'lower_alternate_name', 'geonameid'),
        #                     ('actorstring', 'string', 'actorid')]
        embedding_targets = [('altnames', 'lower_alternate_name', 'alternateNameId'),
                             ('actorstring', 'string', 'actorstringid')]
        indices = [
            ('actor', 'geonameid'), ('altnames', 'geonameid'),
            ('actor', 'canonicalname'), ('altnames', 'lower_alternate_name'),
            ('actor', 'entitysubtype'), ('geonames', 'geonameid'),
            ('geonames', 'country_code'), ('actorstring', 'actorid'),
            ('actorstring', 'string'), ('actor', 'actorid'),
            ('actorisocode', 'actorid'), ('geonames', 'population')]
        super(EntityDB, self).__init__(
            sqlite_file, internal_ontology, embedding_targets, indices, clobber)
        self.country_iso_code_cache = {}

    def ground_entity_to_individual(
            self, mentions, internal_types, properties, n_best):
        """

        :type mentions: [unicode]
        :type internal_types: [(ontology_class.OntologyClass, float)]
        :type properties: dict
        :type n_best: int
        :return: {OntologyClass -> [(id, score)]}
        """
        text_embedding = self.io.embed_text(u' '.join(mentions))
        if len(text_embedding) == 0:
            # TODO handle more intelligently
            text_embedding = [self.io.make_zeros()]
        text_embedding = self.io.vecs.average_vectors(text_embedding)
        cache_key = u" ".join([unicode(dim) for dim in text_embedding])
        individuals = {}

        for internal_type, score in internal_types:  # type: (OntologyClass, float)
            class_name = internal_type.class_name
            cached = (class_name in self.cache
                      and cache_key in self.cache[class_name]
                      and len(self.cache[class_name][cache_key]) >= n_best)
            country_check = 'IDENTIFIER' in properties

            if country_check or not cached:
                identities = {}
                query = self.get_query(class_name, properties)
                if not query:
                    raise IOError("invalid internal class "
                                  "{}".format(class_name))
                cursor = self.connection.cursor()
                cursor.execute(query)

                # calculate similarity for all individuals
                for row in cursor:
                    candidate_embedding = numpy.asarray(row[1].split(),
                                                        numpy.float64)
                    similarity = self.io.vecs.get_vector_similarity(
                        text_embedding, candidate_embedding, metric='cosine')
                    individual = unicode(row[0])

                    # CAMEO: if country, individual here is a canonical name
                    # this function leaves it alone if not country
                    individual = SharedIDManager.convert_to_cameo_optionally(
                        individual)
                    # TODO do we want to allow GPEs that share names with countries?
                    """
                    if "Nation" in query:
                        individual = SharedIDManager.\
                            convert_to_cameo_optionally(individual)
                    """

                    if individual in identities:
                        # take max among all versions of this individual
                        if similarity > identities[individual]:
                            identities[individual] = similarity
                    else:
                        identities[individual] = similarity


                # cache n_best for this type and mention set
                if country_check:
                    return sorted(identities.items(),
                                  key=lambda x: x[1],
                                  reverse=True)[0][0]
                else:
                    self._cache(identities, class_name, cache_key, n_best)

            individuals[class_name] = self.cache[class_name][cache_key][:n_best]
        return individuals

    def _cache(self, identities, class_name, cache_key, n_best):
        best = sorted(identities.items(), key=lambda x: x[1], reverse=True)
        self.cache[class_name][cache_key] = best[:n_best]

    def get_query(self, class_name, properties):
        trunks = [
            ("Country",
             """select distinct a.<IDENTIFIER>, an.embedding
                    from actor a, altnames an
                where a.geonameid=an.geonameid
                    and a.entitysubtype='Nation'
                    and an.isolanguage='en'"""),
            ("City",
             """select distinct a.actorid, an.embedding
                    from actor a, altnames an, geonames g
                where a.geonameid=an.geonameid
                    <ADD_COUNTRY>
                    and (a.entitysubtype is null or a.entitysubtype<>'Nation')
                    and an.isolanguage='en'"""),
            ("Organization",
             """select distinct a.actorid, s.embedding
                from actor a, actorstring s
                where a.actorid=s.actorid"""),
            ("Person",  # same as org
             """select distinct a.actorid, s.embedding
                from actor a, actorstring s
                where a.actorid=s.actorid"""),
            ("GroupOfPersons",  # same as org
             """select distinct a.actorid, s.embedding
                from actor a, actorstring s
                where a.actorid=s.actorid""")]

        for trunk, query in trunks:
            rdf_query = '''
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                select (count(*) as ?count) where {{
                    <{}> rdfs:subClassOf* <{}>
                }}'''.format(class_name, trunk)
            results = self.io.rdf.query(rdf_query)
            how_many = list(results)[0][0]
            descendant_of_trunk = bool(how_many)

            if descendant_of_trunk:

                if "country" in properties:
                    # TODO fix hack: inserts country into city query
                    modified_properties = properties.copy()
                    modified_properties['IDENTIFIER'] = 'actorid'
                    modified_properties.pop('country')
                    country_actor_id = self.ground_entity_to_individual(
                        [properties['country']],
                        [self.io.class_finder[URIRef('Country')]],
                        modified_properties,
                        n_best=1
                    )
                    country_iso = self.get_iso_code_for_country_actor_id(
                        country_actor_id)
                    return query.replace('<ADD_COUNTRY>',
                                         'and an.geonameid=g.geonameid and ' +
                                         'g.country_code=' +
                                         '\'{}\''.format(country_iso))

                else:
                    return query.replace('<IDENTIFIER>',
                                          properties.get('IDENTIFIER',
                                                         'canonicalname'))

    def get_iso_code_for_country_actor_id(self, country_actor_id):
        if country_actor_id in self.country_iso_code_cache:
            return self.country_iso_code_cache[country_actor_id]
        cur = self.connection.cursor()
        cur.execute(
            """SELECT isocode FROM actorisocode
               WHERE actorid=?
               limit 1""",
            (country_actor_id,))
        row = cur.fetchone()
        if row is None:
            self.country_iso_code_cache[country_actor_id] = None
            return None
        self.country_iso_code_cache[country_actor_id] = row[0]
        return row[0]


class EventDB(Database):

    def __init__(self, sqlite_file, internal_ontology, clobber):
        # instead of grouper, use primary key
        embedding_targets = []
        indices = []
        super(EventDB, self).__init__(
            sqlite_file, internal_ontology, embedding_targets, indices, clobber)

    def ground_unstructured_event_to_individual(self):
        pass

    def ground_structured_property_to_individual(self):
        pass
