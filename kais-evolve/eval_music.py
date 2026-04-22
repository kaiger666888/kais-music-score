#!/usr/bin/env python3
"""kais-evolve 评估脚本 — 生成好曲/烂曲 MIDI，评估区分度"""
import json, os, sys, subprocess, tempfile, music21, shutil

# 确保在项目根目录
PROJECT_DIR = "/tmp/crew-kais-music-score"
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))

def generate_good_midis(out_dir):
    """生成 3 个好曲 MIDI"""
    results = {}
    
    # 1. 巴赫风格古典（4声部合唱，和声丰富）
    s1 = music21.stream.Stream()
    s1.id = "Classical Chorale"
    # SATB 4声部
    chords = [
        music21.chord.Chord("C4 E4 G4 C5"),
        music21.chord.Chord("A3 C4 E4 A4"),
        music21.chord.Chord("F3 A3 C4 F4"),
        music21.chord.Chord("G3 B3 D4 G4"),
        music21.chord.Chord("C4 E4 G4 C5"),
        music21.chord.Chord("F3 A3 C4 F4"),
        music21.chord.Chord("G3 B3 D4 G4"),
        music21.chord.Chord("C4 E4 G4 C5"),
    ]
    for ch in chords:
        ch.quarterLength = 1.0
        ch.volume = music21.volume.Volume(velocity=80)
    s1.append(chords)
    p1 = os.path.join(out_dir, "good_classical.mid")
    s1.write("midi", fp=p1)
    results["good_classical"] = p1
    
    # 2. 爵士风格（复杂和弦 + 切分）
    s2 = music21.stream.Stream()
    s2.id = "Jazz Progression"
    jazz_chords = [
        music21.chord.Chord("C4 E4 G4 B4"),    # Cmaj7
        music21.chord.Chord("F3 A3 C4 E4"),    # Fmaj7
        music21.chord.Chord("G3 B3 D4 F4"),    # G7
        music21.chord.Chord("C4 E4 G4 B4"),    # Cmaj7
        music21.chord.Chord("A3 C4 E4 G4"),    # Am7
        music21.chord.Chord("D3 F#3 A3 C4"),   # Dm7
        music21.chord.Chord("G3 B3 D4 F4"),    # G7
        music21.chord.Chord("C4 E4 G4 B4"),    # Cmaj7
    ]
    for i, ch in enumerate(jazz_chords):
        ch.quarterLength = 0.75 if i % 2 == 1 else 1.25  # 切分
        ch.volume = music21.volume.Volume(velocity=70 + (i % 3) * 15)
    s2.append(jazz_chords)
    p2 = os.path.join(out_dir, "good_jazz.mid")
    s2.write("midi", fp=p2)
    results["good_jazz"] = p2
    
    # 3. 流行旋律（AB结构，好听旋律线）
    s3 = music21.stream.Stream()
    s3.id = "Pop Melody"
    # A段
    melody_a = ["C5", "D5", "E5", "G5", "A5", "G5", "E5", "D5"]
    # B段
    melody_b = ["E5", "F5", "G5", "A5", "C6", "A5", "G5", "E5"]
    for note_name in melody_a + melody_b:
        n = music21.note.Note(note_name)
        n.quarterLength = 0.5
        n.volume = music21.volume.Volume(velocity=75)
        s3.append(n)
    p3 = os.path.join(out_dir, "good_pop.mid")
    s3.write("midi", fp=p3)
    results["good_pop"] = p3
    
    return results

def generate_bad_midis(out_dir):
    """生成 3 个烂曲 MIDI"""
    results = {}
    import random
    random.seed(42)
    
    # 1. 随机音符（无调性）
    s1 = music21.stream.Stream()
    s1.id = "Random Notes"
    for _ in range(32):
        n = music21.note.Note(random.randint(36, 84))
        n.quarterLength = 0.25
        n.volume = music21.volume.Volume(velocity=64)
        s1.append(n)
    p1 = os.path.join(out_dir, "bad_random.mid")
    s1.write("midi", fp=p1)
    results["bad_random"] = p1
    
    # 2. 单音重复
    s2 = music21.stream.Stream()
    s2.id = "Single Note Repeat"
    for _ in range(64):
        n = music21.note.Note("C4")
        n.quarterLength = 0.25
        n.volume = music21.volume.Volume(velocity=64)
        s2.append(n)
    p2 = os.path.join(out_dir, "bad_repeat.mid")
    s2.write("midi", fp=p2)
    results["bad_repeat"] = p2
    
    # 3. 全音符（无变化）
    s3 = music21.stream.Stream()
    s3.id = "Whole Notes Only"
    for pitch in ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]:
        n = music21.note.Note(pitch)
        n.quarterLength = 4.0
        n.volume = music21.volume.Volume(velocity=64)
        s3.append(n)
    p3 = os.path.join(out_dir, "bad_wholenotes.mid")
    s3.write("midi", fp=p3)
    results["bad_wholenotes"] = p3
    
    return results

def run_analysis(midi_path, out_dir, label):
    """运行 CLI 并解析结果"""
    try:
        subprocess.run(
            [sys.executable, "-m", "src.cli", "--input", midi_path, 
             "--output-dir", out_dir, "--format", "json"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=60
        )
        json_path = os.path.join(out_dir, "report.json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                data = json.load(f)
            total = data.get("total_score", 0)
            dims = data.get("dimensions", {})
            return {"label": label, "total": total, **dims}
        return {"label": label, "total": 0, "error": "no report.json"}
    except Exception as e:
        return {"label": label, "total": 0, "error": str(e)}

def main():
    tmpdir = tempfile.mkdtemp(prefix="music_eval_")
    try:
        print("🎵 生成测试 MIDI...")
        good = generate_good_midis(tmpdir)
        bad = generate_bad_midis(tmpdir)
        
        print("📊 运行分析...")
        results = []
        for label, path in {**good, **bad}.items():
            out_dir = os.path.join(tmpdir, f"out_{label}")
            os.makedirs(out_dir, exist_ok=True)
            r = run_analysis(path, out_dir, label)
            results.append(r)
            status = "✅" if r["total"] > 0 else "❌"
            print(f"  {status} {label:20} total={r['total']:6.1f}")
        
        good_scores = [r["total"] for r in results if r["label"].startswith("good")]
        bad_scores = [r["total"] for r in results if r["label"].startswith("bad")]
        
        avg_good = sum(good_scores) / len(good_scores) if good_scores else 0
        avg_bad = sum(bad_scores) / len(bad_scores) if bad_scores else 0
        gap = avg_good - avg_bad
        min_good = min(good_scores) if good_scores else 0
        max_bad = max(bad_scores) if bad_scores else 0
        perfect = min_good > max_bad
        
        print(f"\n{'='*50}")
        print(f"  好曲平均: {avg_good:.1f}  (最低: {min_good:.1f})")
        print(f"  烂曲平均: {avg_bad:.1f}  (最高: {max_bad:.1f})")
        print(f"  区分度:   {gap:.1f}")
        print(f"  完美区分: {'✅' if perfect else '❌'} ({min_good:.1f} vs {max_bad:.1f})")
        print(f"{'='*50}")
        
        # 输出 TSV 行
        print(f"\nTSV:\t{gap:.1f}\t{gap > 0}\t{min_good:.1f}\t{max_bad:.1f}")
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
