# Changelog

Notable changes to the SOLVE-IT ontology.

Versions up to 0.1.9 were reconstructed retrospectively from git history on
2026-08-11. Patch versions are assigned automatically by CI on push (see
`scripts/sync_version.py`), so each version below is dated by the commit that
stamped it. Patch versions containing only automated rebuilds and no ontology
changes (0.0.8, 0.1.1) are omitted.

## [Unreleased]

- `hasCASEInputClass` and `hasCASEOutputClass` no longer assert
  `rdfs:range owl:Class`. A technique can consume or produce a single value
  rather than an object, and then the term it names is a property:
  `case-investigation:exhibitNumber`, `uco-core:name`,
  `uco-observable:filePath`. Of the 173 terms the knowledge base references,
  42 are properties. The range was satisfied for those only because the
  generator declared every term an `owl:Class`, which stated something false
  about them. No single range is true of both classes and properties, so the
  constraint moves to SHACL where the alternatives can be enumerated.
- Added `TechniqueIOTermShape`: every term named as a technique input or
  output must be declared an `owl:Class`, `owl:DatatypeProperty` or
  `owl:ObjectProperty`.
- Added `TechniqueIOTermConsistencyShape`: a term must not be declared as more
  than one of those kinds. This is what catches a SOLVE-IT declaration that
  contradicts CASE or UCO, which the shape above cannot, since the knowledge
  base's own declaration is what satisfies it. It bites only when CASE and UCO
  are loaded alongside the data. Against the knowledge base published before
  this change it reports 56 violations across the 42 property terms; against
  the output of the corrected generator, none.
- The property names still say "Class" while now admitting properties. They
  are expected to become `hasInput` and `hasOutput` alongside a knowledge base
  change, and are left alone here so the rename happens once.

- `validate_examples.py`: knowledge base entities must be named in the
  `solveit-data:` namespace. An example writing `:techniqueDFT-1002` against its
  own default prefix creates a look-alike in the examples namespace instead of
  referring to the catalogue entry. Such a file is internally consistent, so it
  parses and validates cleanly while describing entities that exist nowhere
  else.
- `validate_examples.py`: inline copies of catalogue entries are checked against
  the knowledge base. Examples restate techniques, weaknesses and mitigations so
  a reader can follow a file without opening the knowledge base, and those
  copies can drift. A value the example omits is accepted — stating two of a
  technique's five input classes is a shortened quotation, not a contradiction —
  but a value it asserts that the knowledge base does not have is reported.
- `validate_examples.py`: input and output type checking now follows
  `rdfs:subClassOf`. A technique declaring `Timeline` as its input is satisfied
  by a `SortedTimeline`; the previous set intersection missed that and reported
  a mismatch on correct data.

## [0.2.0] — 2026-08-19

- `Technique` now subclasses `uco-action:Technique` rather than
  `case-investigation:InvestigativeAction`, following the metaclass model
  introduced in UCO 1.5.0. A technique is a class; a performed action states
  which technique it implements by `rdf:type`, not by a property. The previous
  axiom sat on the metaclass and so made every catalogue entry a performed
  action.
- `SolveitInvestigativeAction` retained, and is now the parent of every
  technique class. It remains the anchor for occurrence-level properties, so
  `appliedMitigation` is unchanged — its domain is satisfied by inference.
- `usedTechnique` marked `owl:deprecated`. Retained so existing data parses.
- `hasCASEInputClass` and `hasCASEOutputClass` changed from datatype properties
  with range `xsd:anyURI` to object properties with range `owl:Class`. A class
  IRI held in a string literal cannot be followed by a reasoner, walked by a
  SPARQL property path, or checked for a typo.
- All UCO and CASE imports moved from 1.4.0 to 1.5.0 across 9 files. A partial
  bump does not work: `uco-action` 1.5.0 imports `uco-core` 1.5.0, which would
  put two versionIRIs of the same ontology in one import closure.
- SHACL: retired `SolveitInvestigativeActionShape`, which required at least one
  `usedTechnique`; under the metaclass model there is no violating state left
  to detect. Added `TechniqueShape`, checking what OWL cannot express — that a
  technique is also declared `owl:Class` and carries an `rdfs:subClassOf`.
- Example actions migrated from `usedTechnique` to `rdf:type` against the
  technique class, across six files.
- `validate_examples.py` now loads the generated knowledge base
  (`docs/data/solve-it-kb.ttl`). The technique classes the examples type their
  actions with are defined there, not in the ontology files, so without it the
  examples could not be resolved against a complete schema and every domain
  check against an action reported a violation that was not real.
- Retyped the keyword indexing example from `techniqueDFT-1126` (Keyword search
  (live) (physical)) to `techniqueDFT-1121` (Index a data source for keyword
  searching). The action builds an index from a `FileSet` and an `ArtifactSet`
  and produces a `KeywordIndex`, which is what DFT-1121 declares; it was typed
  as a search.
- Qualified the technique and weaknesses in `weakness_assessment_examples.ttl`
  with the `solveit-data:` prefix. They were written against the file's default
  prefix, so they resolved into the examples namespace and described
  look-alikes rather than the catalogue entries the evaluations scored.

## [0.1.10] — 2026-08-11

- Added `rowid` data property to `SQLiteRecord`.
- Clarified comments on `fieldType` and `hasBlobContent` in the SQLite module.

## [0.1.9] — 2026-07-10

- Added `HypothesisedUserAccount` to the analysis module.
- README: documented that external consumers (e.g. the KB build) need updating
  when new module files are added.

## [0.1.8] — 2026-07-02

- Added `HypothesisSet` to support SOLVE-IT technique modelling.

## [0.1.7] — 2026-06-25

- Added `VirtualizedDevice` and `VirtualizedComputer`.

## [0.1.6] — 2026-06-24

- Added `VideoFile` and `AudioFile`.

## [0.1.5] — 2026-06-24

- Added `HashSet` (with `HashSetEntry` and `HashVerificationResult`) plus example.
- Added IDs to the timeline sorting example.

## [0.1.4] — 2026-03-30

- Added sorted timeline concept (`SortedTimeline`, `SortedTimelineEntry`) and a
  draft example using the SOLVE-IT timeline techniques.

## [0.1.3] — 2026-03-23

- Added `TimestampOffset`.

## [0.1.2] — 2026-03-21

- Added `SmartHomeAppFiles`.

## [0.1.0] — 2026-03-20

- Renamed `PerformedTechnique` to `SolveitInvestigativeAction`.
- Restructured weakness classification to support the new weakness formats.
- Added detail to keyword classes and added search examples.
- Improved examples and updated them to the new naming scheme.
- Added input/output class validation for examples (`validate_example_io.py`).

## [0.0.7] — 2026-03-17

- Added `GamingAppFiles`.

## [0.0.6] — 2026-03-09

- Added weakness assessment module (`solve_it_weakness_assessment.ttl`) with
  risk scoring, plus examples.
- Added application file set classes (`BrowserAppFiles`, `ChatAppFiles`,
  `EmailAppFiles`, `PhotosAppFiles`, and others).
- Added hypothesised event subclasses to the analysis module
  (`HypothesisedWebSearch`, `HypothesisedCommunication`, and others).

## [0.0.5] — 2026-03-03

- Updated `FileSystemExtraction`.

## [0.0.4] — 2026-03-03

- Added mobile acquisition types: `iOSDeviceGeneratedBackup`,
  `AndroidDeviceGeneratedBackup`, `AppleUnifiedLogArchive`, `ContentQueryData`.

## [0.0.3] — 2026-03-03

- Docs tooling: GitHub repository link added to generated documentation pages.

## [0.0.2] — 2026-03-03

- Added SQLite module (`solve_it_sqlite.ttl`) with classes and examples.
- Added hypothesis stub classes and `hypothesisedDateTime` property.
- Added CASE input class support (`hasCaseInputClass`).
- Added `FileSet` and `FilteredFileSet`; refined `RedactedFileSet`; added a
  `PrioritizedDeviceSet` example.
- Acquisition/interface updates: added `ReadWriteDeviceInterface`, reworded
  read-only interface; accommodated screenshots and clock offsets as
  acquisitions; SHACL fix for `ClockOffsetMeasurement`.
- Split forensic image containers into subclasses by contents
  (`PhysicalImageContainer`, `LogicalImageContainer`).
- Added `BitstreamRandomAccessed` and `LiveOSDeviceInterface`.
- Added `BrowserCacheData`.
- `Mitigation` now subclasses `InvestigativeAction`.
- Reworded `usedTechnique` (potentially breaking).
- Accommodated time ranges in `TimelineEntry`.
- Tooling: validation scripts run as a GitHub Action; automatic version sync.

## [0.0.1] — 2026-02-20

First versioned release: added the `VERSION` file, version bump/sync scripts,
and documentation tidy-up. The ontology content at this point comprised the
pre-versioning development below.

## Pre-versioning (2025-12-17 – 2026-02-20)

- Initial ontology structure: core classes (`Objective`, `Technique`,
  `Weakness`, `Mitigation`) aligned to CASE/UCO, with observables and analysis
  split into separate module files.
- Added `PerformedTechnique` linking performed actions to techniques and
  applied mitigations; `Technique` changed to subclass `InvestigativeAction`
  rather than `UcoObject`.
- Added tool profile module (`ToolCapabilityProfile`, `MitigationCapability`,
  `SolveItAwareInstrument`).
- Many observable classes: `Timeline`/`TimelineEntry`,
  `ImplicitTimingInformation`, `KeywordSearchResult`, `KeywordIndex`,
  `UnlockPattern`, `DecryptionKey`, `RedactedFileSet`/`RedactedArtifactSet`,
  `NetworkPacketCapture`, `ForensicToolTagBasedReport`, `ClockOffset`,
  `HTTPResponseHeader`, `DateTimeStamp`, `ApplicationFiles`,
  screenshot acquisition types, `AcquisitionRecordFile`.
- Added `DataAcquisition` and subclasses with acquisition error records.
- Updated CASE/UCO alignment from 1.3 to 1.4.0.
- Infrastructure: GitHub Pages documentation at `ontology.solveit-df.org` with
  IRI redirects; daily knowledge base RDF endpoint; MIT licence.
