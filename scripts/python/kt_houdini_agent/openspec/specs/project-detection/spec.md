## ADDED Requirements

### Requirement: 从 project_info.json 自动检测项目名

Skill SHALL 优先读取 `%USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json` 文件中的 `project` 字段来获取当前项目名。

#### Scenario: project_info.json 存在且有效
- **WHEN** `%USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json` 存在，且 JSON 中包含非空的 `project` 字段
- **THEN** Skill SHALL 使用该字段值作为项目名，无需用户手动选择

#### Scenario: project_info.json 不存在
- **WHEN** `%USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json` 文件不存在
- **THEN** Skill SHALL 回退到扫描 `ArtData/ArtHDAs/` 子目录的方案

#### Scenario: project_info.json 缺少 project 字段
- **WHEN** 文件存在但 JSON 中无 `project` 字段或字段值为空
- **THEN** Skill SHALL 回退到扫描 `ArtData/ArtHDAs/` 子目录的方案

### Requirement: 扫描 ArtData 子目录作为项目候选

当 `project_info.json` 不可用时，Skill SHALL 扫描 `ArtData/ArtHDAs/` 下的一级子目录（排除 `SharePrj`），每个子目录名视为一个项目名。

#### Scenario: 仅有一个项目目录
- **WHEN** `ArtData/ArtHDAs/` 下仅有一个非 `SharePrj` 的子目录
- **THEN** Skill SHALL 自动使用该目录名作为项目名

#### Scenario: 存在多个项目目录
- **WHEN** `ArtData/ArtHDAs/` 下存在多个非 `SharePrj` 的子目录
- **THEN** Skill SHALL 返回候选项目列表，由 Agent 引导用户选择

#### Scenario: 无项目目录
- **WHEN** `ArtData/ArtHDAs/` 下无任何非 `SharePrj` 的子目录
- **THEN** Skill SHALL 要求 Agent 让用户手动输入项目名

### Requirement: HDA 存储路径按项目隔离

HDA 文件 SHALL 存储到 `ArtData/ArtHDAs/{项目名}/otls/` 目录下，而非固定的 `SharePrj`。

#### Scenario: 目标目录不存在时自动创建
- **WHEN** `ArtData/ArtHDAs/{项目名}/otls/` 目录不存在
- **THEN** Skill SHALL 自动创建该目录路径（包含中间目录）

#### Scenario: HDA 路径写入 biome_info.json
- **WHEN** HDA 创建成功
- **THEN** `biome_info.json` 中的 `hda_name` 字段 SHALL 使用相对于 ArtData 的路径：`/ArtHDAs/{项目名}/otls/kt_biome_{snake_case}.hda`