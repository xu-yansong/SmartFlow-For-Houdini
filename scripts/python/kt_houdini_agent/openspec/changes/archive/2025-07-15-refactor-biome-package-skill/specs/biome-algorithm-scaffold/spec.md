## ADDED Requirements

### Requirement: 算法搭建 Skill 骨架文件

SHALL 创建 `houdini_agent/skills/build_biome_algorithm.py`，包含 `SKILL_INFO` dict 和 `run()` 函数签名，实现体为 TODO 占位。

#### Scenario: Skill 自动注册
- **WHEN** Agent 启动并加载 skills 目录
- **THEN** `build_biome_algorithm` SHALL 被自动注册为可用 Skill（即使 `run()` 仅返回 "未实现" 提示）

### Requirement: 接口参数定义

`build_biome_algorithm` 的 `SKILL_INFO.parameters` SHALL 至少包含以下参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `package_dir` | string | ✅ | 植被包目录绝对路径 |
| `hda_path` | string | ✅ | HDA 文件绝对路径 |
| `biome_type` | string | ✅ | 生物群系类型 |
| `density` | string | ✅ | 植被密度（high/medium/low） |
| `options` | string | ✅ | 逗号分隔的资产分类列表 |

#### Scenario: 调用未实现的 Skill
- **WHEN** Agent 调用 `build_biome_algorithm`
- **THEN** `run()` SHALL 返回 `{"success": False, "error": "算法搭建功能尚未实现，请等待后续更新"}`

### Requirement: Skill Description 说明前置依赖

`SKILL_INFO.description` SHALL 明确说明此 Skill 需要先通过 `create_biome_package` 创建植被包空壳后才能调用。

#### Scenario: Description 包含前置说明
- **WHEN** Agent 读取 Skill 列表
- **THEN** `build_biome_algorithm` 的 description SHALL 包含 "需要先调用 create_biome_package 创建植被包" 的说明