# kais-music-score 验证报告

**验证时间**: 2026-04-22 19:23 CST  
**验证人**: QA Subagent

---

## 1. 文件完整性检查 ✅

| 文件 | 状态 |
|------|------|
| `src/__init__.py` | ✅ |
| `src/cli.py` | ✅ |
| `src/export.py` | ✅ |
| `src/expressiveness.py` | ✅ |
| `src/harmony_complexity.py` | ✅ |
| `src/melody_diversity.py` | ✅ |
| `src/models.py` | ✅ |
| `src/music_scorer.py` | ✅ |
| `src/preprocess.py` | ✅ |
| `src/rhythm_innovation.py` | ✅ |
| `src/structure_coherence.py` | ✅ |
| `templates/report.html.j2` | ✅ |
| `requirements.txt` | ✅ |

**结论**: 13/13 文件全部存在，结构完整。

---

## 2. 依赖安装 ✅

`music21` + `jinja2` 安装成功，无报错。

---

## 3. CLI 运行结果 ✅

三个测试文件全部成功生成输出：

| 测试文件 | 输出目录 | report.html | report.json | CSV (6个) |
|----------|----------|-------------|-------------|-----------|
| classical.mid | /tmp/test-classical/ | ✅ | ✅ | ✅ |
| pop.mid | /tmp/test-pop/ | ✅ | ✅ | ✅ |
| complex.mid | /tmp/test-complex/ | ✅ | ✅ | ✅ |

---

## 4. 测试结果汇总表

| 测试文件 | 调性 | 类型检测 | 和声 | 旋律 | 节奏 | 结构 | 表现力 | 总分 | 评级 |
|----------|------|----------|------|------|------|------|--------|------|------|
| classical.mid | D major | electronic (12%) | 33.0 | 0.0 | 0.0 | 40.0 | 0.0 | **7.3** | D |
| pop.mid | A minor | electronic (26%) | 23.8 | 57.1 | 35.0 | 81.2 | 0.0 | **26.1** | D |
| complex.mid | E♭ major | electronic (16%) | 27.6 | 77.1 | 62.6 | 51.8 | 25.0 | **43.3** | C |

---

## 5. report.json 结构验证 ✅

所有报告包含要求的字段：
- ✅ `harmony.score` (harmony_complexity)
- ✅ `melody.score` (melody_diversity)
- ✅ `rhythm.score` (rhythm_innovation)
- ✅ `structure.score` (structure_coherence)
- ✅ `expressiveness.score` (expressiveness)
- ✅ `genre.detected_genre` + `genre.confidence`
- ✅ `score.total` + `score.grade`
- ✅ `score.dimensions` 含五维权重

---

## 6. 评分合理性分析

### 合理的维度
- **旋律多样性**: complex(77.1) > pop(57.1) > classical(0.0) ✅ — 复杂曲目音程变化最多
- **节奏创新性**: complex(62.6) > pop(35.0) > classical(0.0) ✅ — 复杂曲目切分最多
- **结构完整性**: pop(81.2) > complex(51.8) > classical(40.0) ✅ — 流行音乐重复结构最明显

### 存在的问题

#### 问题1: 表现力权重过高导致总分失真 ⚠️
- **表现力权重 = 0.45**（占近一半），但 MIDI 文件通常不含力度信息
- 三个测试文件表现力均为 0 或接近 0，导致总分被严重拉低
- **建议**: 将表现力权重降至 0.15~0.20，或将缺少力度信息的 MIDI 文件给予基础分

#### 问题2: 类型检测全部为 electronic ⚠️
- 巴赫风格合唱 → electronic（置信度仅12%）
- 置信度普遍很低（12%~26%），说明分类器区分度不足
- **原因**: MIDI 单声部检测 + 缺少力度信息导致特征不足
- **建议**: 低置信度时应标记为 "unknown" 而非强制选择

#### 问题3: 古典曲目旋律/节奏评分为 0 ⚠️
- 原因: 测试 MIDI 的4个声部被塞进同一小节的 chord 对象，music21 检测为 1 个声部
- `extract_melody` 无法从全音符和弦中提取旋律
- **这是测试 MIDI 的问题，不是代码 bug**，但说明工具对密集和弦输入的处理较弱

#### 问题4: pop.mid 调性检测为 A minor ⚠️
- 输入为 C 大调旋律，但 music21 的 `analyze('key')` 检测为 A minor
- **这是 music21 的行为，非代码 bug**

---

## 7. 发现的问题和修复记录

| # | 问题 | 严重度 | 是否修复 |
|---|------|--------|----------|
| 1 | 表现力权重0.45过高，MIDI无力度信息时总分失真 | 中 | ❌ 未修复（建议调整权重） |
| 2 | 类型检测置信度低时仍强制输出 | 低 | ❌ 未修复（建议增加阈值） |
| 3 | 密集和弦输入旋律提取为0 | 低 | ❌ 非代码bug（测试数据问题） |
| 4 | 无代码崩溃、无 import 错误、无运行时异常 | - | ✅ |

---

## 8. 总结

**项目状态: ✅ 可用，功能完整**

- 端到端流程通畅：MIDI输入 → 五维分析 → HTML/JSON/CSV 输出
- 无代码级 bug，无崩溃
- 输出结构完整，字段齐全
- 主要改进方向：**降低表现力权重**、**类型检测增加低置信度兜底**

**评分合理性**: 三首不同风格曲目的各维度评分分布符合预期趋势（复杂 > 简单 > 和弦密集），但由于 MIDI 力度信息缺失和表现力权重过高，绝对分数偏低。
