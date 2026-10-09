## Why

现有的 `create_biome_package` Skill 是一个"一次性传参"的原子操作，Agent 必须在调用前就知道所有参数。这导致：
1. **缺乏领域引导**：用户需要自己清楚生物群系分类、命名规范等专业知识，Agent 无法基于知识库主动引导。
2. **无项目感知**：HDA 固定存到 `SharePrj`，不能按项目隔离；无法自动检测当前工作项目。
3. **命名不规范**：parm JSON 文件命名不统一（现有包中存在 `kt_desert_parm.json`、`kt_biome_desert_grass.json` 等多种风格）。
4. **信息记录不完整**：密度、生物群系等关键植被特征不会被记录到配置文件中，后续算法搭建阶段缺少上下文。
5. **无算法搭建接口**：创建完空壳后没有后续衔接，算法搭建流程断裂。

## What Changes

- **增强 Skill Description**：重写 description 以引导 Agent 进行多轮对话，逐步收集生物群系、密度、项目名、植被包名、分类目录、资产分类等信息，全部收齐后一次性调用 Skill
- **新增生物群系知识文件**：在 `skills/doc/biome_knowledge.md` 提供结构化的群系选项及描述，Agent 读取后展示给用户选择
- **新增项目检测逻辑**：读取 `%USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json` 自动获取当前项目名；若不存在则扫描 `ArtData/ArtHDAs/` 子目录让用户选择
- **HDA 存储路径按项目隔离**：从 `ArtData/ArtHDAs/SharePrj/otls/` 改为 `ArtData/ArtHDAs/{项目名}/otls/`，目录不存在时自动创建
- **统一命名规范**：parm JSON 统一为 `kt_biome_{snake_case}_parm.json`；新增 PascalCase→snake_case 智能转换（连续大写视为同一个词，如 `PCGBiome` → `pcg_biome`）
- **增强根目录发现**：`_find_artdata()` 升级为 `_find_root()`，判定条件改为目录下同时包含 `ArtData` 和 `HouTools`，并且必须是当前脚本的父目录
- **`package_baseinfo.json` 预填充**：将用户描述写入 `package description`，将群系类型、密度等级等写入 `Tags`
- **新增 Skill 参数**：`project_name`（必填）、`biome_type`（必填）、`density`（必填，high/medium/low）、`description`（选填）、`tags`（选填）
- **返回值增加 Phase 3 上下文**：输出 `hda_path`、`biome_type`、`density`、`options`、`algorithm_pending: true` 等字段，供后续算法搭建 Skill 使用
- **新建算法搭建 Skill 占位**：创建 `build_biome_algorithm` Skill 的骨架文件，定义输入参数，实现留空待后续补充

## Capabilities

### New Capabilities

- `biome-knowledge-loading`: 从 `skills/doc/biome_knowledge.md` 加载生物群系知识，供 Agent 对话阶段向用户展示群系选项及描述
- `project-detection`: 自动检测当前工作项目名（读取 `project_info.json` 或扫描 `ArtData/ArtHDAs/` 子目录），并将 HDA 存储路径按项目隔离
- `smart-naming`: PascalCase→snake_case 智能转换（处理连续大写缩写），统一所有生成文件的命名规范
- `biome-package-creation`: 重构后的植被包创建核心流程，包含增强的参数集、预填充的 baseinfo、完整的上下文返回值
- `biome-algorithm-scaffold`: 算法搭建 Skill 的骨架（`build_biome_algorithm`），定义接口参数，具体实现后续补充

### Modified Capabilities

（无已有 spec 需要修改）

## Impact

- **代码文件**：
  - `houdini_agent/skills/create_biome_package.py` — 主要重构目标，大部分逻辑重写
  - `houdini_agent/skills/build_biome_algorithm.py` — 新文件，算法搭建 Skill 骨架
  - `houdini_agent/skills/doc/biome_knowledge.md` — 新文件，群系知识库（内容由用户手动填充）
- **数据文件**：新创建的植被包中 `biome_info.json` 的 HDA 路径格式变化（`/ArtHDAs/{项目名}/otls/...`），parm JSON 命名格式变化
- **兼容性**：已存在的植被包不受影响；新建植被包将使用新的命名规范和路径结构
- **依赖**：无新增外部依赖，仅使用 Python 标准库 + hou API