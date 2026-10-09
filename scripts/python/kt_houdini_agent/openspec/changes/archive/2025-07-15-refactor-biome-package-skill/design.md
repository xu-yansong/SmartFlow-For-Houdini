## Context

当前 `houdini_agent/skills/create_biome_package.py` 是一个 ~280 行的单文件 Skill，接收 4 个参数一次性创建植被包。Agent 对话能力未被利用——用户必须事先知道所有参数才能触发创建。

工程目录结构（根目录判定条件：同时包含 `ArtData/` 和 `HouTools/`）：

```
{root}/
├── ArtData/
│   ├── ArtHDAs/{项目名}/otls/    ← HDA 存储（按项目隔离）
│   │   └── kt_biome_template.hda ← 在 SharePrj/otls/ 下，只读模板
│   └── BiomeTypes/{分类}/{包名}/  ← 植被包配置目录
└── HouTools/**/                   ← Houdini 插件目录（排除 installPackage）
```

Skill 系统约束：
- Skill 文件放在 `houdini_agent/skills/` 下，定义 `SKILL_INFO` dict + `run()` 函数即可自动注册
- `SKILL_INFO.description` 是 Agent 决策调用的唯一依据，需要足够详细地引导 Agent 对话行为
- 所有 `hou.*` 调用必须在 Skill `run()` 内部（由主线程分发执行）
- Skill 是无状态的原子操作，每次调用独立

## Goals / Non-Goals

**Goals:**

- Skill Description 引导 Agent 在调用前完成多轮对话，收集全部 6 项信息（群系、密度、项目、名称、分类、资产）
- 自动检测当前项目名，HDA 按项目隔离存储
- 统一所有生成文件的命名规范（`kt_biome_{snake_case}_parm.json`）
- `package_baseinfo.json` 预填充群系/密度等关键信息到 Tags
- 返回值包含完整上下文，供后续 `build_biome_algorithm` Skill 衔接
- 创建 `build_biome_algorithm` Skill 骨架（仅定义接口，不实现算法逻辑）

**Non-Goals:**

- 不实现 Phase 3 算法搭建逻辑（留给后续 change）
- 不迁移/修改已有的植被包数据
- 不修改 `biome_knowledge.md` 的内容（由用户手动填充）
- 不改变 Skill 系统框架本身（不修改 `__init__.py` 加载器或 `tool_registry.py`）

## Decisions

### D1: Agent 对话 + Skill 原子执行模式

**选择**：Skill 保持无状态原子操作，由 Skill Description 引导 Agent 多轮对话收集参数后一次性调用。

**备选方案**：
- Skill 内部状态机（多次调用）→ 复杂，违反 Skill 无状态约定
- 拆成多个 Skill（init/set/create）→ 增加调用链复杂度，Agent 容易搞错顺序

**理由**：最简单，利用 Agent 天然的对话能力，Skill 保持纯粹的"工具"角色。Description 中明确列出对话步骤和每步获取的信息，Agent 会照做。

### D2: 根目录发现算法

**选择**：从 `__file__` 向上逐级遍历，查找同时包含 `ArtData/` 和 `HouTools/` 子目录的最近祖先目录。

```python
def _find_root() -> Optional[Path]:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "ArtData").is_dir() and (p / "HouTools").is_dir():
            return p
        p = p.parent
    return None
```

返回 `(root, artdata_path)` 元组，`artdata = root / "ArtData"`。

### D3: PascalCase → snake_case 转换规则

**选择**：使用正则 `re.sub` 两步转换：
1. 在"连续大写→大写小写"边界插入下划线（如 `PCG|Biome` → `PCG_Biome`）
2. 在"小写/数字→大写"边界插入下划线（如 `Desert|Grass` → `Desert_Grass`）
3. 全部转小写

```
规则示例:
  DesertGrass     → desert_grass
  PCGBiome        → pcg_biome
  ForestHTMLTree  → forest_html_tree
  ForestTreeV2    → forest_tree_v2
```

连续大写被视为一个缩写词，不做额外拆分。

### D4: 项目名检测优先级

**选择**：
1. 优先读 `%USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json` 的 `project` 字段
2. 若文件不存在或无 `project` 字段，扫描 `ArtData/ArtHDAs/` 下的子目录（排除 `SharePrj`），每个子目录视为一个项目名
3. 若只有一个项目，自动使用；若有多个，由 Agent 让用户选择（通过 Skill 返回错误提示和候选列表）

### D5: Skill Description 结构

**选择**：Description 采用结构化文本，明确列出 Agent 在调用前应执行的对话步骤：

```
description: (
    "创建一个新的PCG植被包(BiomeTypes)。"
    "调用前必须通过对话收集以下信息：\n"
    "1. 读取 skills/doc/biome_knowledge.md 展示生物群系选项，让用户选择\n"
    "2. 询问植被密度(high/medium/low)\n"
    "3. 检测项目名：先读取 project_info.json，无则扫描 ArtData 让用户选\n"
    "4. 为植被包起英文名(PascalCase)\n"
    "5. 查看 ArtData/BiomeTypes/ 下已有分类让用户选择或新建\n"
    "6. 确认资产分类(默认模板9种 或 自定义)\n"
    "全部信息确认后再调用此工具。"
)
```

### D6: 两个 Skill 的交接面

**选择**：`create_biome_package` 的 `run()` 返回值中包含 `build_biome_algorithm` 所需的全部上下文：

```python
return {
    "success": True,
    "package_dir": str(package_dir),       # 植被包目录绝对路径
    "hda_path": str(new_hda_path),         # 新 HDA 绝对路径
    "project_name": project_name,
    "biome_type": biome_type,
    "density": density,                     # high/medium/low
    "options": options,                     # 资产分类列表
    "algorithm_pending": True,             # 标记算法未搭建
    "created_files": [...],
    "summary": "..."
}
```

`build_biome_algorithm` Skill 接收 `package_dir` + `hda_path` 定位文件，`biome_type` + `density` 指导算法搭建。

## Risks / Trade-offs

| 风险 | 影响 | 缓解 |
|------|------|------|
| Agent 不按 Description 引导的步骤对话 | 参数不完整导致创建失败 | Skill 内做参数校验，返回明确错误信息引导 Agent 补充 |
| `project_info.json` 路径在不同环境下不一致 | 项目检测失败 | 回退到扫描 ArtData 子目录方案 |
| PascalCase→snake_case 转换边界情况 | 极端命名产生异常文件名 | 转换后做正则校验（仅允许 `[a-z0-9_]`），不合法则报错 |
| `biome_knowledge.md` 不存在或为空 | Agent 无法展示群系选项 | Skill Description 中说明文件缺失时让 Agent 直接询问用户自行输入群系 |
| HDA 模板不存在 | 创建失败 | 保留现有的降级策略（文件复制回退），并在错误信息中给出模板路径提示 |