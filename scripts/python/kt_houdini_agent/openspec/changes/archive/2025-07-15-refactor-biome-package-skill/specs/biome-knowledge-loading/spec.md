## ADDED Requirements

### Requirement: Skill Description 引导 Agent 读取群系知识文件

Skill 的 `SKILL_INFO.description` 中 SHALL 包含明确指令，引导 Agent 在调用 Skill 前读取 `skills/doc/biome_knowledge.md` 文件并展示给用户选择生物群系。

#### Scenario: 知识文件存在时正常加载
- **WHEN** Agent 检测到用户意图创建植被包
- **THEN** Agent SHALL 读取 `houdini_agent/skills/doc/biome_knowledge.md` 文件内容，并向用户展示群系选项供选择

#### Scenario: 知识文件不存在时降级处理
- **WHEN** `skills/doc/biome_knowledge.md` 文件不存在或内容为空
- **THEN** Agent SHALL 直接询问用户输入生物群系名称，而非报错终止

### Requirement: 知识文件为 Markdown 格式

群系知识文件 SHALL 存放于 `houdini_agent/skills/doc/biome_knowledge.md`，使用 Markdown 格式，内容由用户手动维护。Skill 代码不负责生成或修改此文件。

#### Scenario: 文件路径和格式
- **WHEN** Skill 被安装部署
- **THEN** `houdini_agent/skills/doc/` 目录下 SHALL 存在 `biome_knowledge.md` 占位文件（可为空或含示例结构）