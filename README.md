# SOLVE-IT Ontology

This is an **experimental** CASE/UCO extension to facilitate output classes in SOLVE-IT techniques that are not currently mapped in other ontologies.

Compiled ontology can be viewed here: https://ontology.solveit-df.org/

Examples are available [here](https://github.com/SOLVE-IT-DF/solve-it-ontology/tree/main/solve_it_examples).

The SOLVE-IT knowledge base is compiled using the ontology so it is available in these formats: [JSON-LD](https://data.solveit-df.org/solve-it.jsonld) and [TTL](https://data.solveit-df.org/solve-it.ttl) (this is synced with the main knowledge base daily).

## Adding a new module

The build and validation tooling in this repository discovers modules automatically (it globs `solve_it_*.ttl`), so no changes here are needed beyond the new file. However, some external consumers hard-code the module list and must be updated when a module is added:

- **[FOCAL](https://github.com/chrishargreaves/FOCAL)** — add the new module to the SOLVE-IT list in `src/store/config.js`, and register its namespace prefix in `src/utils/prefixes.js`. (This was missed when `solve_it_weakness_assessment.ttl` was added; fixed in FOCAL v1.3.1.)

A possible alternative is a master module (like UCO's `uco/master/uco.ttl`) that `owl:imports` every module, giving consumers a single entry point. Note that the ontology IRIs currently redirect to HTML documentation pages rather than the TTL files, so import-following consumers would still need a mapping from ontology IRI to raw TTL URL.
