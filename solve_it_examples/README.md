# SOLVE-IT Ontology Examples

This directory contains example instances demonstrating the use of SOLVE-IT ontology classes.

## Files

### [core_classes_examples.ttl](core_classes_examples.ttl)
Examples of the core SOLVE-IT classes:
- **Objective** - Investigation objectives (e.g., "Acquire data")
- **Technique** - Methods to achieve objectives (e.g., T1002: Disk imaging, T1042: Hash verification)
- **Weakness** - Potential issues with techniques (e.g., incomplete acquisition)
- **Mitigation** - Ways to address weaknesses (e.g., hash verification)
- **PerformedTechnique** - Records of techniques executed during an investigation, extending CASE/UCO InvestigativeAction (provides extended version of Bifrost example from here: https://caseontology.org/examples/asgard/)

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

## Usage

Each file is a standalone Turtle (.ttl) file that can be loaded independently. All files use the same base IRI (`https://ontology.solveit-df.org/solveit/examples/`) and import the relevant SOLVE-IT ontology modules.
