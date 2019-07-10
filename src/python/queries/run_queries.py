#!/nfs/deft-dev100/u10/criley/miniconda2/bin/python
#
# (C) 2019 Raytheon BBN Technologies
#

import os
import sys
import io
from SPARQLWrapper import SPARQLWrapper as SW


def get_sparql_paths(directory):
    for f in os.listdir(directory):
        if f.endswith('.sparql'):
            yield os.path.join(directory, f)


def get_query(path):
    with io.open(path, 'r', encoding='utf8') as f:
        return f.read()


def query_ko(query, graph):
    graph.setQuery(query)
    results = graph.queryAndConvert()
    return results


def write_results(results, out_path):
    header = results['head']['vars']
    with io.open(out_path, 'w', encoding='utf8') as f:
        f.write(u'\t'.join(header) + u'\n')
        for row in results['results']['bindings']:
            cells = []
            for binding in header:
                cell = row.get(binding, {'value': u''})
                cells.append(cell['value'])
            f.write(u'\t'.join(cells) + u'\n')


def get_ko(endpoint, return_format):
    ko = SW(endpoint)
    ko.setReturnFormat(return_format)
    return ko


def main():
    in_directory = sys.argv[1]
    out_directory = sys.argv[2] if len(sys.argv) > 2 else in_directory
    
    sparql_endpoint = 'http://localhost:8890/sparql/'
    query_return_format = 'json'

    ko = get_ko(sparql_endpoint, query_return_format)
    sparqls = get_sparql_paths(in_directory)
    
    for path in sparqls:
        sparql_query = get_query(path)
        sparql_results = query_ko(sparql_query, ko)
        query_file = os.path.basename(path)
        query_name = os.path.splitext(query_file)[0]
        result_path = os.path.join(out_directory, query_name + '.tsv')
        write_results(sparql_results, result_path)


if __name__ == '__main__':
    main()
