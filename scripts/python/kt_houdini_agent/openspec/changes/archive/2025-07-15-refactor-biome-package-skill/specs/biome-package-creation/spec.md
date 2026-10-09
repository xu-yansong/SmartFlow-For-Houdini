## ADDED Requirements

### Requirement: 增强的根目录发现

Skill SHALL 使用 `_find_root()` 函数替代原有的 `_find_artdata()`，从 `__file__` 向上遍历，查找同时包含 `ArtData/` 和 `HouTools/` 子目录的最近祖先目录。

#### Scenario: 正常发现根目录
- **WHEN** Skill 文件位于根目录的子路径下，且根目录同时包含 `ArtData/` 和 `HouTools/`
- **THEN** `_find_root()` SHALL 返回该根目录路径，`artdata = root / "ArtData"`

#### Scenario: 找不到根目录
- **WHEN** 向上遍历到文件系统根仍未找到满足条件的目录
- **THEN** Skill SHALL 返回 `{"success": False, "error": "找不到工程根目录..."}`

### Requirement: 增强的 SKILL_INFO 参数集

`SKILL_INFO.parameters` SHALL 包含以下参数定义：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `package_name` | string | ✅ | 植被包名称（PascalCase） |
| `category` | string | ✅ | BiomeTypes 下的分类目录名 |
| `project_name` | string | ✅ | 项目名（决定 HDA 存储路径） |
| `biome_type` | string | ✅ | 生物群系类型 |
| `density` | string | ✅ | 植被密度（high/medium/low） |
| `options_mode` | string | ✅ | 资产分类方式（template/manual） |
| `custom_options` | string | ❌ | manual 模式的自定义分类列表 |
| `description` | string | ❌ | 用户对植被的自然语言描述 |
| `tags` | string | ❌ | 逗号分隔的附加标签 |

#### Scenario: 必填参数缺失
- **WHEN** 调用时缺少任一必填参数
- **THEN** Skill SHALL 返回错误信息，明确说明缺少哪个参数

### Requirement: 多轮对话引导的 Skill Description

`SKILL_INFO.description` SHALL 包含结构化的对话步骤指引，引导 Agent 在调用前依次收集：群系选择、密度、项目名、植被包名、分类目录、资产分类。

#### Scenario: Agent 按步骤引导
- **WHEN** Agent 识别到用户意图创建植被包
- **THEN** Agent SHALL 按 description 中描述的步骤逐项收集信息，全部确认后一次性调用 Skill

### Requirement: 创建植被包目录结构

Skill SHALL 在 `ArtData/BiomeTypes/{category}/{package_name}/` 下创建完整的目录和文件。

#### Scenario: 目录已存在时报错
- **WHEN** `BiomeTypes/{category}/{package_name}/` 目录已存在
- **THEN** Skill SHALL 返回错误，不覆盖已有植被包

#### Scenario: 目录不存在时创建
- **WHEN** 目标目录不存在
- **THEN** Skill SHALL 自动创建完整路径（含中间目录）

### Requirement: 复制 HDA 模板

Skill SHALL 从 `ArtData/ArtHDAs/SharePrj/otls/kt_biome_template.hda` 复制并重命名为 `ArtData/ArtHDAs/{project_name}/otls/kt_biome_{snake_case}.hda`。

#### Scenario: 使用 Houdini API 复制
- **WHEN** `hou` 模块可用
- **THEN** Skill SHALL 使用 `hou.hda.definitionsInFile()` + `copyToHDAFile()` 复制并重命名 HDA 内部类型名

#### Scenario: Houdini API 不可用时回退
- **WHEN** `hou` 模块不可用或 API 调用失败
- **THEN** Skill SHALL 回退到 `shutil.copy2` 文件复制，并在返回值中附带警告信息

### Requirement: 生成标准配置文件集

Skill SHALL 在植被包目录下生成以下 7 个文件：

1. `kt_biome_{snake_case}_parm.json` — 空 JSON 对象 `{}`
2. `biome_info.json` — 含 HDA 路径和 parm 路径（相对于 ArtData）
3. `biome_options.json` — 资产分类列表
4. `biome_asset.json` — 按资产分类生成空骨架
5. `subsys_layers.json` — 空 JSON 对象 `{}`
6. `subsys_info.json` — 空结构模板
7. `package_baseinfo.json` — 预填充 description 和 Tags

#### Scenario: biome_info.json 路径格式
- **WHEN** 项目名为 `TX3`，植被包名为 `DesertGrass`，分类为 `Desert`
- **THEN** `biome_info.json` SHALL 包含：
  - `hda_name`: `/ArtHDAs/TX3/otls/kt_biome_desert_grass.hda`
  - `hda_parm`: `/BiomeTypes/Desert/DesertGrass/kt_biome_desert_grass_parm.json`

#### Scenario: package_baseinfo.json 预填充
- **WHEN** 用户提供了 description 和 biome_type/density 信息
- **THEN** `package_baseinfo.json` SHALL 将 description 写入 `package description` 字段，将 biome_type、density 等写入 `Tags` 数组

#### Scenario: 资产分类使用模板模式
- **WHEN** `options_mode` 为 `template`
- **THEN** `biome_options.json` SHALL 包含 9 个分类：`{PackageName}_Tree_L/M/S`、`{PackageName}_Bush_L/M/S`、`{PackageName}_Grass_L/M/S`

### Requirement: 返回值包含 Phase 3 上下文

`run()` 的返回值 SHALL 包含后续算法搭建 Skill 所需的全部上下文信息。

#### Scenario: 成功创建时的返回值
- **WHEN** 植被包创建成功
- **THEN** 返回值 SHALL 包含：`success`、`package_dir`（绝对路径）、`hda_path`（绝对路径）、`project_name`、`biome_type`、`density`、`options`（列表）、`algorithm_pending: True`、`created_files`、`summary`