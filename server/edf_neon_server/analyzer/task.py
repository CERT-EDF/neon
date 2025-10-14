"""Analyzer Task"""

from dataclasses import dataclass

from edf_neon_core.concept import Analysis, Case, Sample

Samples = list[tuple[Case, Sample]]


@dataclass(kw_only=True)
class AnalyzerTask:
    """Analyzer Task"""

    primary_digest: str
    analysis: Analysis
    samples: Samples
