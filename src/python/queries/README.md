## Querying the Causal Graph

We often find ourselves in need of running several queries over our KO.  The script(s) located here enable access to a SPARQL endpoint for this purpose.

### Scripts

**run_queries.py** reads SPARQL queries directly from the contents of files having extension `.sparql`, queries the KO, and writes output to a tab-separated file for each query.

Usage:

```bash
./run_queries.py <directory containing .sparql files> [<directory to output .tsv files in>]
```

### Requirements

- Python library `sparqlwrapper`

---

(C) 2019 Raytheon BBN Technologies

