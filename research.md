# 音乐评估维度与计算音乐学指标研究报告

> 基于 music21 (MIT) 的 MIDI 音乐复杂度量化分析框架
> 参考文献：Madsen & Widmer (2015), Conklin (2006), MihailMiller/music-complexity

---

## 1. 和声复杂度 (Harmonic Complexity)

### 1.1 可计算指标

#### 指标1：和弦多样性 (Chord Diversity)
- **定义**：乐曲中不同和弦类型的数量与总数的比率，用 Shannon 熵衡量
- **算法**：将每个时间窗（如每拍/每小节）内的音符归并为和弦 → `chord.identify()` 获取和弦名称 → 统计和弦类型的频率分布 → 计算 `H = -Σ p(i) * log2(p(i))`
- **music21 API**：
  ```python
  from music21 import chord, harmony, stream
  s = converter.parse('file.mid')
  for c in s.chordify().recurse().getElementsByClass(chord.Chord):
      print(c.commonName, c.figuresWritten)
  ```
- **评分标准**：
  | 范围 | 评级 | 说明 |
  |------|------|------|
  | H < 1.0 | 低 | 仅3-4种和弦反复（如 I-V-vi-IV） |
  | 1.0 ≤ H < 2.0 | 中 | 5-8种和弦，有基本的转调 |
  | H ≥ 2.0 | 高 | 丰富和弦变化，含借用和弦/转位/延伸音 |
  | H > 3.0 | 极高 | 爵士/晚期浪漫主义级别 |

#### 指标2：调性变化频率 (Modulation Frequency)
- **定义**：乐曲中调性中心发生变化的次数与乐段数的比值
- **算法**：将乐曲按乐段（8-16小节）分段 → 每段调用 `score.analyze('key')` → 统计调性中心变化次数
- **music21 API**：
  ```python
  from music21 import analyze
  key = score.analyze('key')
  key.tonic, key.mode  # 调性中心与大小调
  # 逐段分析
  for segment in segments:
      k = segment.analyze('key')
  ```
- **评分标准**：
  | 变化频率 | 评级 |
  |----------|------|
  | 0 次 | 静态和声（流行/民谣典型） |
  | 1-2 次 | 中等，有近关系转调 |
  | 3-5 次 | 较复杂，有远关系转调 |
  | >5 次 | 高度复杂（爵士/古典） |

#### 指标3：声部进行质量 (Voice Leading Quality)
- **定义**：相邻和弦间各声部移动的平均半音距离，越小越平滑
- **算法**：提取各声部线（SATB）→ 计算相邻和弦同声部间的音程距离 → 统计平均值和标准差
- **music21 API**：
  ```python
  from music21 import voiceLeading
  v = voiceLeading.VoiceLeadingQuarterly(c1.pitches, c2.pitches)
  v.smallestVoiceLeadingDistance()  # 声部进行距离
  ```
- **评分标准**：
  | 平均半音距离 | 评级 |
  |-------------|------|
  | < 1.5 | 优秀（平滑声部进行） |
  | 1.5-3.0 | 良好 |
  | > 3.0 | 较粗糙（跳跃较多） |

#### 指标4：和弦根音运动模式 (Root Motion Patterns)
- **定义**：和弦根音间音程的分布，纯五度下行多=传统，三度/半音多=丰富
- **算法**：提取所有相邻和弦根音 → 计算音程分布（纯五度=7半音，三度=3/4，半音=1）
- **music21 API**：`chord.root()` + `interval.Interval(pitch1, pitch2)`

### 1.2 推荐算法
- **Shannon 熵**：Madsen & Widmer (2015) 的核心方法，适用于所有维度的多样性度量
- **Markov Chain 转移概率**：和弦进行转移矩阵的熵
- **Tonnetz 分析**：music21 的 `chord.commonEmbellishment` / `chord.hasAnyEnharmonicSpelling`

---

## 2. 旋律多样性 (Melodic Diversity)

### 2.1 可计算指标

#### 指标1：音程多样性 (Interval Diversity)
- **定义**：旋律中出现的不同音程类型的丰富程度（用熵衡量）
- **算法**：提取旋律声部 → 计算所有相邻音符间的音程 → 统计音程类型频率分布 → 计算熵
- **music21 API**：
  ```python
  melody = score.parts[0].flatten().getElementsByClass(note.Note)
  intervals = [interval.Interval(melody[i], melody[i+1]).name for i in range(len(melody)-1)]
  ```
- **评分标准**：
  | 熵值 | 评级 |
  |------|------|
  | H < 1.5 | 低（以级进为主，如儿歌/流行） |
  | 1.5 ≤ H < 2.5 | 中（有跳进和级进混合） |
  | H ≥ 2.5 | 高（大量不同音程，如爵士） |

#### 指标2：旋律轮廓变化 (Melodic Contour Variation)
- **定义**：旋律方向变化的频率（上升/下降/平直的转折次数）
- **算法**：提取旋律音高序列 → 计算方向序列（+1/-1/0）→ 统计方向变化次数与音符总数的比值
- **music21 API**：
  ```python
  from music21 import contour
  # 旋律轮廓可用 note.pitch.midi 的差分方向序列
  pitches = [n.pitch.midi for n in melody_notes]
  directions = [1 if pitches[i+1]>pitches[i] else -1 if pitches[i+1]<pitches[i] else 0 
                for i in range(len(pitches)-1)]
  changes = sum(1 for i in range(len(directions)-1) if directions[i] != directions[i+1])
  contour_ratio = changes / len(directions)
  ```
- **评分标准**：
  | 轮廓变化率 | 评级 |
  |-----------|------|
  | < 0.3 | 低（单调重复轮廓） |
  | 0.3-0.5 | 中（适度变化） |
  | > 0.5 | 高（频繁转折，如华彩段） |

#### 指标3：音域范围 (Pitch Range)
- **定义**：旋律使用的最高音与最低音之间的半音数
- **算法**：`max(pitches) - min(pitches)`
- **music21 API**：
  ```python
  all_pitches = score.flatten().pitches
  range_semitones = max(p.midi for p in all_pitches) - min(p.midi for p in all_pitches)
  ```
- **评分标准**（以单旋律为基准）：
  | 音域（半音） | 评级 |
  |-------------|------|
  | < 10 (不到一个八度) | 窄 |
  | 10-19 (1-1.5八度) | 中等 |
  | 20-30 (1.5-2.5八度) | 宽 |
  | > 30 (>2.5八度) | 很宽 |

#### 指标4：旋律动机重复与变化 (Motivic Repetition & Variation)
- **定义**：相同或相似旋律片段的重复次数及变化程度
- **算法**：提取 n-gram 旋律片段（n=3-8音符）→ 用编辑距离聚类 → 统计重复率与变化率
- **music21 API**：`stream.search()` + 自定义 n-gram 提取

---

## 3. 节奏创新性 (Rhythmic Innovation)

### 3.1 可计算指标

#### 指标1：节奏多样性熵 (Rhythmic Diversity Entropy)
- **定义**：不同节奏型（duration pattern）的 Shannon 熵
- **算法**：将每个音符时值量化为最近的标准时值 → 提取节奏 n-gram（如连续3个音符的时值组合）→ 统计频率分布 → 计算熵
- **music21 API**：
  ```python
  from music21 import meter, duration
  durations = [n.duration.type for n in notes]  # 'quarter', 'eighth', etc.
  # 或用 quarterLength 获取精确时值
  qLengths = [n.duration.quarterLength for n in notes]
  ```
- **评分标准**：
  | 熵值 | 评级 |
  |------|------|
  | H < 1.0 | 低（几乎全是四分/八分音符） |
  | 1.0 ≤ H < 2.0 | 中 |
  | H ≥ 2.0 | 高（丰富节奏型） |

#### 指标2：切分音比例 (Syncopation Ratio)
- **定义**：落在弱拍或反拍上的音符数量与总音符数量的比值
- **算法**：确定拍号 → 计算每个音符的 beat position → 判断是否在弱拍/反拍 → 计算比例
- **music21 API**：
  ```python
  from music21 import meter
  ts = score.getTimeSignatures()[0]
  for n in notes:
      beat = n.beat  # 在小节中的拍位
      beatStrength = n.beatStrength  # music21 计算的拍子强度
      if beatStrength < 0.5:  # 弱拍
          syncopated += 1
  ```
- **评分标准**：
  | 切分比例 | 评级 |
  |---------|------|
  | < 10% | 低（严格正拍） |
  | 10-25% | 中 |
  | 25-40% | 高（明显切分） |
  | > 40% | 极高（爵士/放克典型） |

#### 指标3：节奏密度 (Rhythmic Density)
- **定义**：每分钟的平均音符数量（Note On Events Per Minute）
- **算法**：统计总音符数 / 总时长(分钟)
- **music21 API**：
  ```python
  total_notes = len(score.flatten().getElementsByClass(note.Note))
  total_duration_q = score.flatten().highestTime  # quarterLength
  # 结合 tempo 标记换算为分钟
  ```
- **评分标准**（相对指标，因 BPM 差异大）：
  | 音符/秒 | 评级 |
  |---------|------|
  | < 2 | 稀疏（ambient/氛围音乐） |
  | 2-6 | 中等 |
  | > 6 | 密集（金属/速弹/电子碎拍） |

#### 指标4：多节奏/复合节奏 (Polyrhythm Detection)
- **定义**：同时存在的不同节奏层的数量和复杂度
- **算法**：按声部分离 → 分别提取节奏型 → 检测是否有非整数倍关系的节奏叠加
- **music21 API**：`score.parts` 分离声部 + 各声部 `meter.beatStrength` 对比

---

## 4. 结构完整性 (Structural Integrity)

### 4.1 可计算指标

#### 指标1：重复模式检测 (Repetition Pattern Score)
- **定义**：乐曲中重复片段（精确+近似重复）占总时长的比例
- **算法**：提取旋律/和弦序列 → 用滑动窗口匹配相似片段 → 统计重复覆盖率
- **music21 API**：
  ```python
  # 精确重复
  from music21 import search
  # 旋律轮廓重复（方向序列匹配）
  # 近似重复可用编辑距离
  ```
- **评分标准**：
  | 重复覆盖率 | 评级 |
  |-----------|------|
  | < 20% | 低（几乎无重复，即兴风格） |
  | 20-40% | 中（适度重复，发展良好） |
  | 40-60% | 高（经典曲式结构） |
  | > 60% | 过高（可能单调） |

#### 指标2：曲式识别 (Form Analysis)
- **定义**：识别乐曲的大结构形式（ABA, ABAC, ABACB, Rondo, Sonata 等）
- **算法**：按乐段分段 → 提取每段的特征向量（和弦进行/旋律轮廓/节奏型）→ 聚类判断哪些段落相似 → 推断曲式
- **music21 API**：
  ```python
  from music21 import analysis
  # 分段：按小节或乐句
  measures = score.parts[0].getElementsByClass(stream.Measure)
  # 逐段提取特征后聚类
  ```
- **评分标准**：
  | 曲式类型 | 复杂度 |
  |---------|--------|
  | 单一乐段重复(AAAA) | 低 |
  | 二部/三部曲式(AB/ABA) | 中 |
  | 回旋曲/复合曲式(ABACA/ABACABA) | 高 |
  | 奏鸣曲式/自由曲式 | 很高 |

#### 指标3：乐句结构对称性 (Phrase Symmetry)
- **定义**：乐句长度的一致性（4+4=8小节为对称，3+5=8为不对称）
- **算法**：检测乐句边界（休止符/终止式）→ 统计乐句长度 → 计算长度的标准差与变异系数
- **music21 API**：
  ```python
  # 检测乐句边界：长时间休止符或终止和弦
  rests = score.flatten().getElementsByClass(note.Rest)
  phrases = split_by_rests(score)
  phrase_lengths = [p.highestTime for p in phrases]
  cv = std(phrase_lengths) / mean(phrase_lengths)  # 变异系数
  ```
- **评分标准**：
  | 变异系数 | 评级 |
  |---------|------|
  | < 0.1 | 高度对称（古典/流行标准） |
  | 0.1-0.3 | 适度不对称 |
  | > 0.3 | 高度不对称（爵士/自由即兴） |

#### 指标4：发展逻辑评分 (Development Logic Score)
- **定义**：音乐素材从呈示→发展→再现的逻辑完整性
- **算法**：将乐曲分为三大部分 → 分析呈示部素材在发展部的变形程度 → 检测再现部的回归程度 → 综合评分
- **实现**：需结合重复检测 + 特征相似度矩阵

---

## 5. 表现力 (Expressiveness)

### 5.1 可计算指标

#### 指标1：力度变化幅度 (Dynamic Range)
- **定义**：乐曲中力度标记（或 MIDI velocity）的最大变化范围
- **算法**：提取所有音符的 velocity → 计算 max - min → 归一化到 0-127
- **music21 API**：
  ```python
  velocities = [n.volume.velocity for n in notes if n.volume.velocity is not None]
  # 或使用力度标记
  dynamics = score.flatten().getElementsByClass(dynamics.Dynamic)
  for d in dynamics:
      print(d.value, d.volumeSelling)  # 'pp', 'ff', etc.
  ```
- **评分标准**：
  | Velocity 范围 | 力度标记范围 | 评级 |
  |---------------|-------------|------|
  | < 20 | < pp | 缺乏表现力 |
  | 20-50 | pp-p | 有一定变化 |
  | 50-80 | p-ff | 丰富 |
  | > 80 | ppp-fff | 极富表现力 |

#### 指标2：力度变化频率 (Dynamic Change Frequency)
- **定义**：力度发生明显变化的次数（每分钟）
- **算法**：对 velocity 序列做差分 → 统计超过阈值的次数 / 总时长
- **评分标准**：
  | 变化次数/分钟 | 评级 |
  |--------------|------|
  | < 3 | 平淡 |
  | 3-8 | 适中 |
  | > 8 | 富于变化 |

#### 指标3：速度变化 (Tempo Variation)
- **定义**：BPM 变化的幅度和频率
- **算法**：提取所有 tempo 标记 → 计算极差和变化次数
- **music21 API**：
  ```python
  from music21 import tempo
  tempo_marks = score.flatten().getElementsByClass(tempo.MetronomeMark)
  for t in tempo_marks:
      print(t.number)  # BPM value
  ```
- **评分标准**：
  | BPM 变化范围 | 评级 |
  |-------------|------|
  | 0 (恒定速度) | 机械感 |
  | 1-10 | 微小弹性速度 |
  | 10-30 | 明显速度变化 |
  | > 30 | 大幅速度变化（古典协奏曲/自由速度） |

#### 指标4：Articulation 多样性 (Articulation Diversity)
- **定义**：不同 articulation 标记（断奏、连奏、重音等）的种类和分布
- **算法**：提取所有 articulation 对象 → 统计种类和频率
- **music21 API**：
  ```python
  articulations = set()
  for n in notes:
      for art in n.articulations:
          articulations.add(type(art).__name__)
  # types: Staccato, Accent, Tenuto, Fermata, etc.
  ```
- **评分标准**：
  | Articulation 种类数 | 评级 |
  |--------------------|------|
  | 0 | 无（纯 MIDI velocity 无标记） |
  | 1-2 | 基础 |
  | 3-5 | 丰富 |
  | > 5 | 极丰富（专业乐谱级别） |

---

## 6. 音乐类型理想特征差异

| 维度 | 古典 | 流行 | 爵士 | 电子 | 摇滚 |
|------|------|------|------|------|------|
| **和弦多样性** | 中-高 (H: 1.5-3.0) | 低-中 (H: 0.8-1.5) | 极高 (H: 2.5-4.0) | 低-中 (H: 0.5-1.5) | 低 (H: 0.5-1.2) |
| **调性变化** | 2-5次（奏鸣曲多） | 0-1次 | 2-8次（频繁转调） | 0-1次（多为单调） | 0-1次 |
| **声部进行** | 优秀 (<1.5) | 一般 (2-3) | 优秀-良好 (1-2) | N/A（合成器） | 一般 (2-4) |
| **音程多样性** | 中-高 (H: 2.0-3.0) | 低 (H: 1.0-2.0) | 高 (H: 2.5-3.5) | 低-中 (H: 1.0-2.0) | 中 (H: 1.5-2.5) |
| **旋律轮廓** | 0.3-0.5 | 0.2-0.4 | 0.4-0.6 | 0.2-0.4 | 0.3-0.5 |
| **音域** | 宽 (20-36半音) | 窄-中 (8-16半音) | 宽 (18-30半音) | 窄 (5-12半音) | 中 (10-20半音) |
| **节奏熵** | 中 (H: 1.5-2.5) | 低-中 (H: 1.0-2.0) | 高 (H: 2.0-3.5) | 低-中 (H: 0.5-1.5) | 低 (H: 0.8-1.5) |
| **切分比例** | 低-中 (5-15%) | 低 (5-15%) | 高 (30-50%) | 中 (15-30%) | 中 (10-25%) |
| **重复率** | 40-60% | 40-60% | 20-40% | 50-80% | 30-50% |
| **曲式** | ABA/奏鸣曲 | AB/ABC/ABAB | AABA/布鲁斯12小节 | AB(循环) | AB/ABA/ABAB |
| **力度范围** | 丰富 (ppp-fff) | 中等 (mp-f) | 中等 (p-f) | 低-中 (通过混音实现) | 高 (p-fff) |
| **速度变化** | 多（弹性速度） | 无（固定节拍器） | 中（swing/shuffle） | 无（电子节拍器） | 中（少量变化） |

### 关键洞察

1. **爵士乐**在所有维度上几乎都是最复杂的——高和声熵、高节奏创新、频繁转调、丰富的切分
2. **流行音乐**追求可预测性和记忆点，因此和声和节奏复杂度有意降低
3. **电子音乐**的结构重复率最高（loop-based），但通过音色变化（无法通过 MIDI 纯分析）实现表现力
4. **古典音乐**在声部进行质量和结构完整性上最突出
5. **摇滚**的核心特征不在于复杂度，而在于力度和音色的表现力（后者 MIDI 分析有限）

---

## 7. 实现建议

### 7.1 核心依赖
```python
# requirements.txt
music21>=9.1.0
numpy>=1.24.0
scipy>=1.10.0
```

### 7.2 统一评分框架
```python
class MusicComplexityAnalyzer:
    def __init__(self, midi_path):
        self.score = converter.parse(midi_path)
        self.results = {}
    
    def analyze_harmony(self): ...
    def analyze_melody(self): ...
    def analyze_rhythm(self): ...
    def analyze_structure(self): ...
    def analyze_expression(self): ...
    
    def get_overall_score(self):
        """加权综合分 (0-100)"""
        weights = {
            'harmony': 0.25,
            'melody': 0.20,
            'rhythm': 0.20,
            'structure': 0.20,
            'expression': 0.15
        }
        return sum(self.results[dim] * w for dim, w in weights.items())
```

### 7.3 注意事项
- **MIDI 质量依赖**：分析结果严重依赖 MIDI 文件的质量和编码规范
- **多声部分离**：`score.chordify()` 可合并声部用于和声分析，但旋律分析需单独提取声部
- **velocity 不可靠**：MIDI velocity 在不同音源间含义不同，力度分析需谨慎
- **电子音乐局限**：纯 MIDI 分析无法捕捉音色、混响、效果器等电子音乐核心元素
- **标准化**：不同长度的乐曲需归一化指标（如按每分钟或每小节计算）

---

## 8. 参考文献

1. Madsen, S. & Widmer, G. (2015). "A complexity-based approach to melody track identification in MIDI files." *International Workshop on Artificial Intelligence and Music*.
2. Conklin, D. (2006). "Melodic analysis with segment classes." *Machine Learning*, 65(2), 349-360.
3. Cuthbert, M.S. & Ariza, C. (2010). "Music21: A Toolkit for Computer-Aided Musicology and Symbolic Music Data." *ISMIR*.
4. MihailMiller/music-complexity — [GitHub](https://github.com/MihailMiller/music-complexity)
5. music21 Documentation — [web.mit.edu/music21](https://web.mit.edu/music21/)
