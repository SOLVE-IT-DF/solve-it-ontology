# SOLVE-IT Ontology Examples

This directory contains example instances demonstrating the use of SOLVE-IT ontology classes.

## Files

### [core_classes_examples.ttl](core_classes_examples.ttl)
Examples of the core SOLVE-IT classes, including use of the CASE/UCO Technique metaclass:
- **Objective** - Investigation objectives (e.g., "Acquire data")
- **Technique** - Methods to achieve objectives (e.g., T1002: Copy sectors from storage media, T1042: Verify hash of imaged data matches the hash of the source device)
- **Weakness** - Potential issues with techniques (e.g., incomplete acquisition)
- **Mitigation** - Ways to address weaknesses (e.g., hash verification)
- **SolveitInvestigativeAction** - A SOLVE-IT aware InvestigativeAction that records which technique(s) were used (1..n) and which mitigations were applied (0..n) during an investigation, extending CASE/UCO InvestigativeAction (provides extended version of Bifrost example from here: https://caseontology.org/examples/asgard/)

### [tool_profile_examples.ttl](tool_profile_examples.ttl)
Examples of the tool profile module, showing what a capability profile asserts and who asserted it:
- **ToolCapabilityProfile** - A publisher's statement about what one version of one tool provides (e.g. a testing programme's profile for ACME Chat Parser 1.0)
- **MitigationCapability** - A claim that the tool provides a SOLVE-IT mitigation, optionally scoped by `appliesWhen` to a SHACL shape describing where it was established (e.g. WhatsApp 13.8-14.0 only)
- **SolveitAwareInstrument** - A tool recorded as having been assessed against profiles, via `consultedProfile`, without restating the claims those profiles make
- Two publishers making the **same claim at different scopes**, kept separate rather than merged, so a reader can see who asserted what and how narrowly

### [observable_examples.ttl](observable_examples.ttl)
Examples of SOLVE-IT observable classes:
- **VideoFrame** - Individual frames extracted from video evidence
- **UnlockPattern** - Android device unlock patterns

### [timeline_resolution_examples.ttl](timeline_resolution_examples.ttl)
Timeline examples demonstrating **DateTimeStamp** with different timestamp resolutions:
- FAT filesystem timestamps with varying precision (10ms for created, 2s for modified, 1 day for accessed)
- Shows the two-step provenance chain using different SOLVE-IT techniques: T1060 extracts files, T1052 generates timeline with resolution metadata
- Demonstrates handling of timezone uncertainty

### [timeline_sequence_examples.ttl](timeline_sequence_examples.ttl)
Timeline examples demonstrating **ImplicitTimingInformation** for sequence-based ordering:
- FAT cluster allocation order as a proxy for file creation sequence
- ClusterRun objects showing file fragmentation
- Shows how ordering can be derived from non-temporal artifacts
- Demonstrates the same two-step provenance chain (T1060 -> T1052)

### [search_examples.ttl](search_examples.ttl)
Examples of keyword search and indexing classes:
- **Live keyword search** - Searching a BitstreamRandomAccessed with a case-type Wordlist, producing offset-based KeywordSearchResultSet hits
- **Keyword indexing** - Building a KeywordIndex from a FileSet and ArtifactSet with KeywordIndexingConfiguration
- **Indexed keyword search** - Searching the generated KeywordIndex with a case-specific Wordlist, producing file-level KeywordSearchResultSet hits

### [acquisition_examples.ttl](acquisition_examples.ttl)
Examples of forensic acquisition classes and workflows:
- Physical disk removal, write blocking, and imaging chain
- ForensicImageContainer, PhysicalImageContainer, and related acquisition observables

### [sqlite_examples.ttl](sqlite_examples.ttl)
Examples of SQLite observable classes for database forensics.

### [triaged_devices_examples.ttl](triaged_devices_examples.ttl)
Examples of device triage classes:
- **DeviceSet** and **PrioritizedDeviceSet** for grouping and prioritising seized devices

### [hashset_examples.ttl](hashset_examples.ttl)
Examples of hash matching classes:
- **HashSet** and **HashSetEntry** for matching file hashes against a reference set (e.g. NSRL RDS) in DFT-1047 to reduce the files examined

### [weakness_assessment_examples.ttl](weakness_assessment_examples.ttl)
Examples of weakness assessment classes for evaluating technique reliability.

## Usage

Each file is a standalone Turtle (.ttl) file that can be loaded independently. All files use the same base IRI (`https://ontology.solveit-df.org/solveit/examples/`) and import the relevant SOLVE-IT ontology modules.
