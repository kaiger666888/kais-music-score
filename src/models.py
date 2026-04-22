"""数据模型定义 — 所有分析模块的输入/输出类型"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PieceInfo:
    """乐曲基本信息"""
    source_file: str = ""
    format: str = "midi"
    total_measures: int = 0
    total_duration_q: float = 0.0
    key: str = ""
    time_signatures: list = field(default_factory=list)
    tempo_marks: list = field(default_factory=list)
    part_count: int = 0
    track_names: list = field(default_factory=list)


@dataclass
class ChordEvent:
    """和弦事件"""
    measure: int = 0
    beat: float = 0.0
    name: str = ""
    root: int = 0
    pitches: list = field(default_factory=list)


@dataclass
class MelodicPoint:
    """旋律分析单点"""
    measure: int = 0
    beat: float = 0.0
    pitch: int = 0
    interval_from_prev: int = 0
    direction: int = 0


@dataclass
class RhythmicPoint:
    """节奏分析单点"""
    measure: int = 0
    beat: float = 0.0
    duration_q: float = 0.0
    beat_strength: float = 0.0
    is_syncopated: bool = False


@dataclass
class HarmonyResult:
    chord_diversity_entropy: float = 0.0
    modulation_count: int = 0
    voice_leading_smoothness: float = 0.0
    root_motion_distribution: dict = field(default_factory=dict)
    chord_events: list = field(default_factory=list)
    score: float = 0.0


@dataclass
class MelodyResult:
    interval_diversity_entropy: float = 0.0
    contour_change_ratio: float = 0.0
    pitch_range_semitones: int = 0
    motivic_repetition_rate: float = 0.0
    melodic_points: list = field(default_factory=list)
    score: float = 0.0


@dataclass
class RhythmResult:
    rhythmic_diversity_entropy: float = 0.0
    syncopation_ratio: float = 0.0
    notes_per_second: float = 0.0
    polyrhythm_detected: bool = False
    rhythmic_points: list = field(default_factory=list)
    score: float = 0.0


@dataclass
class StructureResult:
    repetition_coverage: float = 0.0
    detected_form: str = ""
    phrase_symmetry_cv: float = 0.0
    development_logic_score: float = 0.0
    section_boundaries: list = field(default_factory=list)
    score: float = 0.0


@dataclass
class ExpressivenessResult:
    dynamic_range: int = 0
    dynamic_change_frequency: float = 0.0
    tempo_variation_range: float = 0.0
    articulation_types: int = 0
    articulation_details: list = field(default_factory=list)
    score: float = 0.0


@dataclass
class GenreDetection:
    detected_genre: str = "pop"
    confidence: float = 0.0
    genre_scores: dict = field(default_factory=dict)


@dataclass
class ScoreResult:
    detected_genre: str = "pop"
    genre_confidence: float = 0.0
    genre_scores: dict = field(default_factory=dict)
    dimensions: dict = field(default_factory=dict)
    total: float = 0.0
    grade: str = "D"


@dataclass
class AnalysisReport:
    """完整分析报告"""
    piece: PieceInfo = field(default_factory=PieceInfo)
    genre: GenreDetection = field(default_factory=GenreDetection)
    harmony: HarmonyResult = field(default_factory=HarmonyResult)
    melody: MelodyResult = field(default_factory=MelodyResult)
    rhythm: RhythmResult = field(default_factory=RhythmResult)
    structure: StructureResult = field(default_factory=StructureResult)
    expressiveness: ExpressivenessResult = field(default_factory=ExpressivenessResult)
    score: Optional[ScoreResult] = None
