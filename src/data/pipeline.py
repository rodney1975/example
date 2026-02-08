from src.data.models import SprintRecord, StrokeMetrics, SessionSummary


def compute_stroke_metrics(records: list[SprintRecord], rep_number: int) -> StrokeMetrics:
    rep_records = [r for r in records if r.rep == rep_number]
    if not rep_records:
        raise ValueError(f"No records found for rep {rep_number}")

    timestamps = [r.timestamp for r in rep_records]
    velocities = [r.velocity for r in rep_records]
    forces = [r.force for r in rep_records]
    powers = [r.power for r in rep_records]
    positions = [r.position for r in rep_records]

    duration = max(timestamps) - min(timestamps)
    stroke_rate = 60.0 / duration if duration > 0 else 0.0
    stroke_length = max(positions) - min(positions)

    avg_velocity = sum(velocities) / len(velocities)
    peak_velocity = max(velocities)
    avg_force = sum(forces) / len(forces)
    peak_force = max(forces)
    avg_power = sum(powers) / len(powers)
    peak_power = max(powers)

    phase_durations: dict[str, float] = {}
    for i in range(1, len(rep_records)):
        phase = rep_records[i].stroke_phase
        dt = rep_records[i].timestamp - rep_records[i - 1].timestamp
        phase_durations[phase] = phase_durations.get(phase, 0.0) + dt

    return StrokeMetrics(
        rep_number=rep_number,
        stroke_rate=round(stroke_rate, 2),
        stroke_length=round(stroke_length, 3),
        avg_velocity=round(avg_velocity, 3),
        peak_velocity=round(peak_velocity, 3),
        avg_force=round(avg_force, 2),
        peak_force=round(peak_force, 2),
        avg_power=round(avg_power, 2),
        peak_power=round(peak_power, 2),
        duration=round(duration, 3),
        phase_durations={k: round(v, 4) for k, v in phase_durations.items()},
    )


def compute_session_summary(filename: str, records: list[SprintRecord]) -> SessionSummary:
    rep_numbers = sorted(set(r.rep for r in records))
    strokes = [compute_stroke_metrics(records, rep) for rep in rep_numbers]

    total_reps = len(rep_numbers)
    positions = [r.position for r in records]
    total_distance = max(positions) - min(positions) if positions else 0.0
    timestamps = [r.timestamp for r in records]
    total_duration = max(timestamps) - min(timestamps) if timestamps else 0.0

    stroke_rates = [s.stroke_rate for s in strokes]
    stroke_lengths = [s.stroke_length for s in strokes]
    avg_stroke_rate = sum(stroke_rates) / len(stroke_rates) if stroke_rates else 0.0
    avg_stroke_length = sum(stroke_lengths) / len(stroke_lengths) if stroke_lengths else 0.0

    return SessionSummary(
        filename=filename,
        total_reps=total_reps,
        total_distance=round(total_distance, 3),
        total_duration=round(total_duration, 3),
        avg_stroke_rate=round(avg_stroke_rate, 2),
        avg_stroke_length=round(avg_stroke_length, 3),
        strokes=strokes,
    )


def compute_force_velocity_profile(records: list[SprintRecord]) -> list[dict]:
    result: list[dict] = []
    for r in records:
        if abs(r.velocity) > 0.05:
            result.append({"velocity": round(r.velocity, 3), "force": round(r.force, 2)})
    return result


def compute_phase_breakdown(records: list[SprintRecord]) -> dict[str, float]:
    phase_time: dict[str, float] = {}
    total_time = 0.0

    for i in range(1, len(records)):
        phase = records[i].stroke_phase
        dt = records[i].timestamp - records[i - 1].timestamp
        phase_time[phase] = phase_time.get(phase, 0.0) + dt
        total_time += dt

    if total_time > 0:
        return {phase: round(t / total_time, 4) for phase, t in phase_time.items()}
    return phase_time
