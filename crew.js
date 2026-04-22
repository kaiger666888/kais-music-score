module.exports = {
  name: "kais-music-score",
  goal: "音乐五维质量评估系统 — 输入 MIDI/MusicXML，输出交互式 HTML 报告。对标 kais-story-score 的开发模式。",
  
  workdir: "/tmp/crew-kais-music-score",
  
  project: {
    lang: "python",
    github: "kaiger666888/kais-music-score",
    description: "音乐五维质量评估系统（和声复杂度/旋律多样性/节奏创新性/结构完整性/表现力）",
  },
  
  optimize: {
    enabled: true,
    maxRounds: 3,
    targetScore: 8.0,
  },

  architectureDiagrams: {
    enabled: true,
    diagrams: ["system"],
  },

  steps: [
    // === Phase 1: 研究与设计 ===
    {
      id: "research",
      skill: "deep-research",
      params: {
        topic: "Music evaluation dimensions and computational musicology metrics for MIDI analysis. Focus on: 1) harmony complexity (chord diversity, modulation frequency, voice leading), 2) melody diversity (interval variety, contour, range), 3) rhythmic innovation (syncopation, polyrhythm, groove), 4) structural coherence (repetition patterns, form analysis, phrase structure), 5) expressiveness (dynamics, articulation, tempo variation). Key tools: music21 Python library. Existing projects: MihailMiller/music-complexity.",
        depth: "medium",
      },
      output: "research.md",
      timeout: 300,
    },
    
    {
      id: "design",
      skill: "claude-code-via-openclaw",
      input: "research.md",
      params: {
        workflow: "direct",
        task: `设计 kais-music-score 项目架构。参考 kais-story-score 的项目结构（位于 ~/.openclaw/workspace/skills/kais-story-score/）。

要求：
1. 五维分析模块设计：
   - src/harmony_complexity.py — 和声复杂度（和弦多样性、调性变化、声部进行）
   - src/melody_diversity.py — 旋律多样性（音程多样性、轮廓变化、音域范围）
   - src/rhythm_innovation.py — 节奏创新性（切分音、多节奏、律动感）
   - src/structure_coherence.py — 结构完整性（重复模式、曲式分析、乐句结构）
   - src/expressiveness.py — 表现力（力度变化、 articulation、速度变化）

2. 核心依赖：music21 (MIT, pip install music21)

3. 输入格式：MIDI (.mid) 和 MusicXML (.xml/.mxl)

4. 输出格式：与 story-score 一致
   - report.html（交互式 Plotly 报告）
   - report.json（结构化数据）
   - CSV 文件（每维度一个）

5. CLI 接口：python -m src.cli --input song.mid --output-dir ./output

6. 评分系统：类型感知权重（古典/流行/爵士/电子/摇滚），类似 story-score 的类型检测

7. music_scorer.py：加权评分，支持不同音乐类型的理想特征

只输出设计文档 design.md 到 /tmp/crew-kais-music-score/，包含：
- 项目结构图
- 每个模块的输入/输出/核心算法
- 评分权重表
- 数据流图
不要写代码。`,
      },
      output: "design.md",
      timeout: 300,
    },

    // === Phase 2: 核心实现 ===
    {
      id: "implement",
      skill: "claude-code-via-openclaw",
      input: ["research.md", "design.md"],
      params: {
        workflow: "gsd",
        requirement: `实现 kais-music-score 音乐五维质量评估系统。

项目位置：/tmp/crew-kais-music-score/
参考项目：~/.openclaw/workspace/skills/kais-story-score/（克隆其架构模式）

核心要求：
1. 使用 music21 库解析 MIDI/MusicXML
2. 五个分析模块：harmony_complexity, melody_diversity, rhythm_innovation, structure_coherence, expressiveness
3. music_scorer.py：类型感知评分（古典/流行/爵士/电子/摇滚），每种类型有不同的理想特征和权重
4. CLI：python -m src.cli --input song.mid --output-dir ./output [--format html|json|csv|all]
5. HTML 报告：Plotly 交互式图表，单文件 HTML
6. 评分输出：总分 + 五维分项 + 类型检测 + 评级（S/A/B/C/D）

实现顺序：
1. 先实现 preprocess.py（MIDI/MusicXML 解析 → 统一内部格式）
2. 实现五个分析模块
3. 实现 music_scorer.py（类型检测 + 加权评分）
4. 实现 cli.py（参数解析 + 编排）
5. 实现 export.py（HTML/JSON/CSV 导出）

关键算法参考：
- 和声复杂度：和弦识别(music21.harmony) + 调性分析(music21.key) + 声部进行
- 旋律多样性：音程直方图 + 轮廓变化率 + 音域范围
- 节奏创新：切分音比例 + 节奏密度变化 + 节拍变化
- 结构完整性：重复模式检测 + 乐句分割 + 曲式识别(ABA/ABAC等)
- 表现力：力度变化范围 + 速度标记数 + articulation 多样性

测试数据：用 music21 内置的巴赫曲目做测试（music21.corpus.getBachChorales()[:3]）

完成后确保：python -m src.cli --input test.mid --output-dir /tmp/test-output 能正常运行。`,
      },
      output: ["src/", "templates/", "requirements.txt"],
      timeout: 600,
      retry: { max: 2 },
    },

    // === Phase 3: 验证 ===
    {
      id: "verify",
      skill: "claude-code-via-openclaw",
      input: "design.md",
      params: {
        workflow: "direct",
        task: `验证 /tmp/crew-kais-music-score/ 项目是否完整可用。

1. 检查所有文件是否存在：src/ 下所有 .py 文件、templates/、requirements.txt
2. 安装依赖：pip install music21
3. 创建测试 MIDI 文件（用 music21 生成一个简单旋律）
4. 运行 CLI：cd /tmp/crew-kais-music-score && python -m src.cli --input /tmp/test.mid --output-dir /tmp/test-music-output --format all
5. 检查输出：report.html 是否生成、report.json 结构是否完整、五维评分是否存在
6. 如果有错误，直接修复

修复完成后，在 /tmp/crew-kais-music-score/ 下生成一个验证报告 verify.md，包含：
- 测试结果（通过/失败）
- 生成的文件列表
- 五维评分截图（文字描述）
- 发现的问题和修复记录`,
      },
      output: "verify.md",
      timeout: 300,
      retry: { max: 2 },
    },

    // === Phase 4: 文档与发布 ===
    {
      id: "docs",
      skill: "claude-code-via-openclaw",
      input: ["design.md", "verify.md"],
      params: {
        workflow: "direct",
        task: `为 /tmp/crew-kais-music-score/ 创建完整文档。

1. README.md：项目介绍、安装、使用方法、五维说明、示例输出截图（文字描述）
2. SKILL.md：OpenClaw skill 格式，参考 ~/.openclaw/workspace/skills/kais-story-score/SKILL.md 的格式
3. 初始化 git：cd /tmp/crew-kais-music-score && git init && git add -A && git commit -m "feat: initial release — music five-dimension quality evaluation"
4. 创建 GitHub 仓库：gh repo create kaiger666888/kais-music-score --public --source=. --push

完成后输出 docs_done.md，记录所有创建的文件和 GitHub 仓库地址。`,
      },
      output: "docs_done.md",
      timeout: 180,
    },
  ],
};
