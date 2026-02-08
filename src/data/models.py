from dataclasses import dataclass, field


@dataclass
class SprintRecord:
    rep: int
    timestamp: float
    position: float
    velocity: float
    acceleration: float
    force: float
    power: float
    stroke_phase: str


@dataclass
class StrokeMetrics:
    rep_number: int
    stroke_rate: float
    stroke_length: float
    avg_velocity: float
    peak_velocity: float
    avg_force: float
    peak_force: float
    avg_power: float
    peak_power: float
    duration: float
    phase_durations: dict[str, float] = field(default_factory=dict)


@dataclass
class SessionSummary:
    filename: str
    total_reps: int
    total_distance: float
    total_duration: float
    avg_stroke_rate: float
    avg_stroke_length: float
    strokes: list[StrokeMetrics] = field(default_factory=list)
