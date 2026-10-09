## ADDED Requirements

### Requirement: PascalCase 转 snake_case 智能拆分

Skill SHALL 提供 `_pascal_to_snake(name: str) -> str` 函数，将 PascalCase 植被包名转换为 snake_case，用于 HDA 和 parm JSON 的文件命名。

#### Scenario: 标准 PascalCase 转换
- **WHEN** 输入为 `DesertGrass`
- **THEN** 输出 SHALL 为 `desert_grass`

#### Scenario: 连续大写视为同一个词
- **WHEN** 输入为 `PCGBiome`
- **THEN** 输出 SHALL 为 `pcg_biome`（连续大写 `PCG` 不做拆分）

#### Scenario: 多段连续大写
- **WHEN** 输入为 `ForestHTMLTree`
- **THEN** 输出 SHALL 为 `forest_html_tree`

#### Scenario: 含数字的名称
- **WHEN** 输入为 `ForestTreeV2`
- **THEN** 输出 SHALL 为 `forest_tree_v2`

### Requirement: 统一文件命名规范

所有植被包生成的文件 SHALL 遵循统一的命名规范。

#### Scenario: HDA 文件命名
- **WHEN** 植被包名为 `DesertGrass`
- **THEN** HDA 文件名 SHALL 为 `kt_biome_desert_grass.hda`

#### Scenario: Parm JSON 文件命名
- **WHEN** 植被包名为 `DesertGrass`
- **THEN** 参数文件名 SHALL 为 `kt_biome_desert_grass_parm.json`（统一前缀 `kt_biome_` + snake_case + `_parm`）

#### Scenario: 植被包目录命名
- **WHEN** 植被包名为 `DesertGrass`
- **THEN** 植被包目录名 SHALL 保持 PascalCase 原样：`BiomeTypes/{分类}/DesertGrass/`

### Requirement: 转换结果校验

转换后的 snake_case 名称 SHALL 通过 `[a-z0-9_]+` 正则校验。

#### Scenario: 含非法字符时报错
- **WHEN** 转换结果包含 `[a-z0-9_]` 以外的字符
- **THEN** Skill SHALL 返回错误信息，提示用户修改植被包名称