"""数据导出 — JSON / CSV"""
import csv
import json
import os
from datetime import datetime, timezone
from .models import AnalysisReport


def _report_to_dict(report: AnalysisReport) -> dict:
    return {
        "meta": {
            "source_file": report.piece.source_file,
            "format": report.piece.format,
            "total_measures": report.piece.total_measures,
            "key": report.piece.key,
            "time_signatures": report.piece.time_signatures,
            "tempo_marks": report.piece.tempo_marks,
            "part_count": report.piece.part_count,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "genre": {
            "detected_genre": report.genre.detected_genre,
            "confidence": report.genre.confidence,
            "genre_scores": report.genre.genre_scores,
        },
        "harmony": {
            "chord_diversity_entropy": report.harmony.chord_diversity_entropy,
            "modulation_count": report.harmony.modulation_count,
            "voice_leading_smoothness": report.harmony.voice_leading_smoothness,
            "score": report.harmony.score,
        },
        "melody": {
            "interval_diversity_entropy": report.melody.interval_diversity_entropy,
            "contour_change_ratio": report.melody.contour_change_ratio,
            "pitch_range_semitones": report.melody.pitch_range_semitones,
            "motivic_repetition_rate": report.melody.motivic_repetition_rate,
            "score": report.melody.score,
        },
        "rhythm": {
            "rhythmic_diversity_entropy": report.rhythm.rhythmic_diversity_entropy,
            "syncopation_ratio": report.rhythm.syncopation_ratio,
            "notes_per_second": report.rhythm.notes_per_second,
            "polyrhythm_detected": report.rhythm.polyrhythm_detected,
            "score": report.rhythm.score,
        },
        "structure": {
            "repetition_coverage": report.structure.repetition_coverage,
            "detected_form": report.structure.detected_form,
            "phrase_symmetry_cv": report.structure.phrase_symmetry_cv,
            "development_logic_score": report.structure.development_logic_score,
            "score": report.structure.score,
        },
        "expressiveness": {
            "dynamic_range": report.expressiveness.dynamic_range,
            "dynamic_change_frequency": report.expressiveness.dynamic_change_frequency,
            "tempo_variation_range": report.expressiveness.tempo_variation_range,
            "articulation_types": report.expressiveness.articulation_types,
            "score": report.expressiveness.score,
        },
        "score": {
            "detected_genre": report.score.detected_genre if report.score else "",
            "genre_confidence": report.score.genre_confidence if report.score else 0,
            "dimensions": report.score.dimensions if report.score else {},
            "total": report.score.total if report.score else 0,
            "grade": report.score.grade if report.score else "",
        } if report.score else None,
    }


def to_json(report: AnalysisReport, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_report_to_dict(report), f, ensure_ascii=False, indent=2)


def to_csv(report: AnalysisReport, dir_path: str) -> list:
    os.makedirs(dir_path, exist_ok=True)
    files = []

    # harmony.csv
    p = os.path.join(dir_path, "harmony.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["measure", "beat", "chord_name", "root"])
        for ev in report.harmony.chord_events:
            w.writerow([ev.measure, ev.beat, ev.name, ev.root])
    files.append(p)

    # melody.csv
    p = os.path.join(dir_path, "melody.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["measure", "beat", "pitch", "interval", "direction"])
        for pt in report.melody.melodic_points:
            w.writerow([pt.measure, pt.beat, pt.pitch, pt.interval_from_prev, pt.direction])
    files.append(p)

    # rhythm.csv
    p = os.path.join(dir_path, "rhythm.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["measure", "beat", "duration", "beat_strength", "is_syncopated"])
        for pt in report.rhythm.rhythmic_points:
            w.writerow([pt.measure, pt.beat, pt.duration_q, pt.beat_strength, pt.is_syncopated])
    files.append(p)

    # structure.csv
    p = os.path.join(dir_path, "structure.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["detected_form", "repetition_coverage", "symmetry_cv", "development_score", "section_boundaries"])
        w.writerow([report.structure.detected_form, report.structure.repetition_coverage,
                    report.structure.phrase_symmetry_cv, report.structure.development_logic_score,
                    "; ".join(str(b) for b in report.structure.section_boundaries)])
    files.append(p)

    # expressiveness.csv
    p = os.path.join(dir_path, "expressiveness.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dynamic_range", "change_frequency", "tempo_variation", "articulation_types", "details"])
        w.writerow([report.expressiveness.dynamic_range, report.expressiveness.dynamic_change_frequency,
                    report.expressiveness.tempo_variation_range, report.expressiveness.articulation_types,
                    "; ".join(report.expressiveness.articulation_details)])
    files.append(p)

    # summary.csv
    p = os.path.join(dir_path, "summary.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dimension", "score"])
        w.writerow(["harmony", report.harmony.score])
        w.writerow(["melody", report.melody.score])
        w.writerow(["rhythm", report.rhythm.score])
        w.writerow(["structure", report.structure.score])
        w.writerow(["expression", report.expressiveness.score])
        if report.score:
            w.writerow(["genre", report.score.detected_genre])
            w.writerow(["total", report.score.total])
            w.writerow(["grade", report.score.grade])
    files.append(p)

    return files
