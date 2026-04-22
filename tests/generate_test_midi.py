"""生成测试 MIDI 文件"""
from music21 import stream, note, meter, tempo, key, chord

def create_test_midi(path: str):
    s = stream.Score()
    s.insert(0, meter.TimeSignature('4/4'))
    s.insert(0, tempo.MetronomeMark(number=120))
    s.insert(0, key.KeySignature(0))  # C major

    # Part 1: Melody
    p1 = stream.Part()
    p1.partName = "Melody"
    p1.append(meter.TimeSignature('4/4'))
    p1.append(tempo.MetronomeMark(number=120))

    melody_pitches = [60, 64, 67, 72, 71, 67, 64, 60, 62, 65, 69, 72, 74, 69, 65, 62,
                      60, 64, 67, 72, 76, 72, 67, 64, 60, 62, 65, 69, 72, 69, 65, 60]
    for i, p in enumerate(melody_pitches):
        n = note.Note(p, quarterLength=0.5)
        n.volume.velocity = 60 + (i % 8) * 8  # varying velocity
        p1.append(n)

    # Part 2: Chords (accompaniment)
    p2 = stream.Part()
    p2.partName = "Chords"
    p2.append(meter.TimeSignature('4/4'))
    chord_progression = [
        [48, 60, 64],  # C
        [43, 55, 59],  # G/B
        [48, 60, 64],  # C
        [41, 53, 57],  # G
        [43, 55, 59],  # G/B
        [48, 60, 64],  # C
        [41, 53, 57],  # G
        [48, 60, 64],  # C
        [45, 57, 60],  # Am
        [48, 60, 64],  # C
        [50, 62, 65],  # Dm
        [52, 65, 69],  # Em/B
        [48, 60, 64],  # C
        [43, 55, 59],  # G/B
        [41, 53, 57],  # G
        [48, 60, 64],  # C
    ]
    for chord_pitches in chord_progression:
        c = chord.Chord(chord_pitches, quarterLength=1.0)
        c.volume.velocity = 50
        p2.append(c)

    s.insert(0, p1)
    s.insert(0, p2)
    s.write('midi', fp=path)
    print(f"✅ 测试 MIDI 已生成: {path}")

if __name__ == "__main__":
    create_test_midi("/tmp/test_music.mid")
