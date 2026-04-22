# kais-evolve: kais-music-score

## Goal
优化音乐五维质量评估系统的评分区分度——让好音乐得分高、烂音乐得分低，类似 kais-story-score 的优化路径。

## Metric
- Primary: 区分度 score gap（好曲 vs 烂曲的平均分差，higher is better）
- Secondary: 好曲最低分 vs 烂曲最高分（完美区分 = 好曲最低 > 烂曲最高）

### 评估脚本
```bash
python3 /tmp/crew-kais-music-score/kais-evolve/eval_music.py
```

评估脚本会：
1. 用 music21 生成 6 个测试 MIDI（3好3烂）
2. 对每个运行 CLI
3. 解析 report.json 提取五维评分和总分
4. 计算 score gap + 完美区分
5. 输出 TSV 格式结果

### 好曲标准
- 古典：巴赫风格（4声部合唱，和声丰富，调性变化）
- 爵士：复杂和弦（7th/9th/11th），切分节奏，即兴旋律
- 流行：ABAB结构，旋律好听，节奏稳定

### 烂曲标准
- 随机音符：无调性，无节奏规律
- 单音重复：一个音反复
- 全音符：全是全音符，无变化

## Scope
- Editable: src/music_scorer.py, src/harmony_complexity.py, src/melody_diversity.py, src/rhythm_innovation.py, src/structure_coherence.py, src/expressiveness.py, src/preprocess.py
- Read-only: src/cli.py, src/export.py, src/models.py, templates/
- No new dependencies: true

## Constraints
- Time budget: 120 seconds per experiment
- Simplicity: 倾向简洁的评分规则，避免过度拟合

## Baseline
- Command: python3 kais-evolve/eval_music.py
- Expected: gap ≈ 0-10, 烂曲可能因为 MIDI 特殊性得分不稳定

## Ideas
1. 增强和声复杂度：检测三和弦以上、调性变化的权重
2. 旋律多样性：惩罚重复音程、奖励大跳和变化
3. 节奏创新：惩罚均匀节奏、奖励切分和变化
4. 结构完整性：检测重复模式、惩罚全曲无结构
5. 表现力：惩罚无力度/速度变化的 MIDI
6. 评分权重调优：对不同维度找到最佳权重组合
7. 烂曲检测：随机音符应得极低分（<20），好曲应得高分（>60）

## Results TSV
commit	metric_gap	gap_improved	min_good_max_bad	status	description
baseline	0.0	0	0	keep	initial baseline
