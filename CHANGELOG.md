# Changelog

Notable changes to the SOLVE-IT ontology.

Versions up to 0.1.9 were reconstructed retrospectively from git history on
2026-08-11. Patch versions are assigned automatically by CI on push (see
`scripts/sync_version.py`), so each version below is dated by the commit that
stamped it. Patch versions containing only automated rebuilds and no ontology
changes (0.0.8, 0.1.1) are omitted.

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
