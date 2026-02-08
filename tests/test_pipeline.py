import pytest

from src.data.models import StrokeMetrics, SessionSummary
from src.data.pipeline import (
    compute_stroke_metrics,
    compute_session_summary,
    compute_force_velocity_profile,
    compute_phase_breakdown,
)


EXPECTED_PHASES = {"Glide", "Catch", "Pull", "Push", "Recovery"}


class TestComputeStrokeMetrics:
    def test_compute_stroke_metrics_rep1(self, sample_records):
        rep1_records = [r for r in sample_records if r.rep == 1]
        metrics = compute_stroke_metrics(rep1_records, rep_number=1)
        assert isinstance(metrics, StrokeMetrics)
        assert metrics.rep_number == 1, (
            f"rep_number should be 1, got {metrics.rep_number}"
        )
        assert metrics.peak_velocity > 0, (
            f"peak_velocity should be > 0, got {metrics.peak_velocity}"
        )
        assert metrics.duration > 0, (
            f"duration should be > 0, got {metrics.duration}"
        )

    def test_compute_stroke_metrics_has_all_fields(self, sample_records):
        rep1_records = [r for r in sample_records if r.rep == 1]
        metrics = compute_stroke_metrics(rep1_records, rep_number=1)
        assert metrics.rep_number is not None, "rep_number should not be None"
        assert metrics.stroke_rate is not None, "stroke_rate should not be None"
        assert metrics.stroke_length is not None, "stroke_length should not be None"
        assert metrics.avg_velocity is not None, "avg_velocity should not be None"
        assert metrics.peak_velocity is not None, "peak_velocity should not be None"
        assert metrics.avg_force is not None, "avg_force should not be None"
        assert metrics.peak_force is not None, "peak_force should not be None"
        assert metrics.avg_power is not None, "avg_power should not be None"
        assert metrics.peak_power is not None, "peak_power should not be None"
        assert metrics.duration is not None, "duration should not be None"
        assert metrics.phase_durations is not None, "phase_durations should not be None"

    def test_compute_stroke_metrics_stroke_rate(self, sample_records):
        rep1_records = [r for r in sample_records if r.rep == 1]
        metrics = compute_stroke_metrics(rep1_records, rep_number=1)
        expected_rate = 60.0 / metrics.duration
        assert metrics.stroke_rate == pytest.approx(expected_rate, rel=1e-3), (
            f"stroke_rate should be 60/duration={expected_rate:.3f}, "
            f"got {metrics.stroke_rate}"
        )

    def test_compute_stroke_metrics_phase_durations(self, sample_records):
        rep1_records = [r for r in sample_records if r.rep == 1]
        metrics = compute_stroke_metrics(rep1_records, rep_number=1)
        rep1_phases = {r.stroke_phase for r in rep1_records}
        assert isinstance(metrics.phase_durations, dict), (
            "phase_durations should be a dict"
        )
        for phase in rep1_phases:
            assert phase in metrics.phase_durations, (
                f"phase '{phase}' should be in phase_durations"
            )
            assert metrics.phase_durations[phase] > 0, (
                f"phase duration for '{phase}' should be > 0"
            )


class TestComputeSessionSummary:
    def test_compute_session_summary(self, sample_records):
        summary = compute_session_summary(
            "sprint_session_001.csv", sample_records
        )
        assert isinstance(summary, SessionSummary)
        unique_reps = len({r.rep for r in sample_records})
        assert summary.total_reps == unique_reps, (
            f"total_reps should be {unique_reps}, got {summary.total_reps}"
        )

    def test_compute_session_summary_distance(self, sample_records):
        summary = compute_session_summary(
            "sprint_session_001.csv", sample_records
        )
        assert summary.total_distance > 0, (
            f"total_distance should be > 0, got {summary.total_distance}"
        )

    def test_compute_session_summary_stroke_count(self, sample_records):
        summary = compute_session_summary(
            "sprint_session_001.csv", sample_records
        )
        assert len(summary.strokes) == summary.total_reps, (
            f"len(strokes) should equal total_reps ({summary.total_reps}), "
            f"got {len(summary.strokes)}"
        )


class TestComputeForceVelocityProfile:
    def test_compute_force_velocity_profile(self, sample_records):
        profile = compute_force_velocity_profile(sample_records)
        assert isinstance(profile, list), "profile should be a list"
        assert len(profile) > 0, "profile should be non-empty"
        for entry in profile:
            assert isinstance(entry, dict), "each entry should be a dict"
            assert "velocity" in entry, "each entry should have 'velocity' key"
            assert "force" in entry, "each entry should have 'force' key"

    def test_compute_force_velocity_profile_excludes_zero(self, sample_records):
        profile = compute_force_velocity_profile(sample_records)
        zero_velocity_entries = [e for e in profile if e["velocity"] == 0]
        assert len(zero_velocity_entries) == 0, (
            "profile should not contain entries with velocity == 0"
        )


class TestComputePhaseBreakdown:
    def test_compute_phase_breakdown(self, sample_records):
        breakdown = compute_phase_breakdown(sample_records)
        assert isinstance(breakdown, dict), "phase breakdown should be a dict"
        for phase in EXPECTED_PHASES:
            assert phase in breakdown, (
                f"phase '{phase}' should be in breakdown"
            )

    def test_compute_phase_breakdown_sums_to_one(self, sample_records):
        breakdown = compute_phase_breakdown(sample_records)
        total = sum(breakdown.values())
        assert total == pytest.approx(1.0, abs=0.01), (
            f"phase proportions should sum to ~1.0, got {total}"
        )
