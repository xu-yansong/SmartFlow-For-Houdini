## 1. 基础工具函数

- [x] 1.1 实现 `_find_root()` 函数：从 `__file__` 向上遍历，查找同时含 `ArtData/` 和 `HouTools/` 的祖先目录，返回 `(root, artdata)` 元组；替换原有的 `_find_artdata()`
- [x] 1.2 实现 `_pascal_to_snake(name: str) -> str` 函数：两步正则拆分（连续大写→大写小写边界 + 小写/数字→大写边界），全部转小写；验证 `DesertGrass→desert_grass`、`PCGBiome→pcg_biome`、`ForestHTMLTree→forest_html_tree`、`ForestTreeV2→forest_tree_v2`
- [x] 1.3 实现 `_detect_project(artdata: Path) -> dict` 函数：优先读 `%USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json` 的 `project` 字段；失败则扫描 `ArtData/ArtHDAs/` 子目录（排除 `SharePrj`）；返回 `{"project": "TX3"}` 或 `{"candidates": [...]}` 或 `{"error": "..."}`

## 2. 重构 SKILL_INFO

- [x] 2.1 重写 `SKILL_INFO.description`：包含 6 步对话引导（读取 biome_knowledge.md → 密度 → 项目名 → 包名 → 分类 → 资产分类），以及调用前需确认全部信息的说明
- [x] 2.2 更新 `SKILL_INFO.parameters`：新增 `project_name`（必填）、`biome_type`（必填）、`density`（必填，enum: high/medium/low）、`description`（选填）、`tags`（选填）；保留原有 `package_name`、`category`、`options_mode`、`custom_options`

## 3. 重构 run() 核心逻辑

- [x] 3.1 替换 `_find_artdata()` 调用为 `_find_root()`，获取 root 和 artdata 路径
- [x] 3.2 新增参数校验：检查 `project_name`、`biome_type`、`density` 必填项，`density` 值必须在 `{"high", "medium", "low"}` 中
- [x] 3.3 使用 `_pascal_to_snake()` 生成 snake_case 名称，并做 `[a-z0-9_]+` 正则校验
- [x] 3.4 修改 HDA 输出路径：从 `ArtData/ArtHDAs/SharePrj/otls/` 改为 `ArtData/ArtHDAs/{project_name}/otls/`，目录不存在时 `mkdir(parents=True)`
- [x] 3.5 修改 `_copy_hda_template()` 函数签名：接收 `artdata`、`project_name`、`snake_name`，模板路径不变（SharePrj），输出路径使用项目目录
- [x] 3.6 统一 parm JSON 命名为 `kt_biome_{snake_case}_parm.json`
- [x] 3.7 更新 `_make_biome_info()`：`hda_name` 使用 `/ArtHDAs/{project_name}/otls/kt_biome_{snake}.hda`，`hda_parm` 使用 `/BiomeTypes/{category}/{package_name}/kt_biome_{snake}_parm.json`
- [x] 3.8 更新 `_make_package_baseinfo()`：接收 `description`、`biome_type`、`density`、`tags` 参数，预填充 `package description` 和 `Tags` 字段
- [x] 3.9 增强返回值：新增 `hda_path`、`project_name`、`biome_type`、`density`、`options`（列表）、`algorithm_pending: True` 字段

## 4. 创建知识文件占位

- [x] 4.1 创建 `houdini_agent/skills/doc/` 目录
- [x] 4.2 创建 `houdini_agent/skills/doc/biome_knowledge.md` 占位文件（含基本 Markdown 结构和使用说明注释，内容留空待用户填充）

## 5. 创建算法搭建 Skill 骨架

- [x] 5.1 创建 `houdini_agent/skills/build_biome_algorithm.py`，包含 `SKILL_INFO` dict（name、description、parameters 定义 5 个必填参数：package_dir、hda_path、biome_type、density、options）
- [x] 5.2 实现 `run()` 函数签名和 TODO 占位返回：`{"success": False, "error": "算法搭建功能尚未实现，请等待后续更新"}`
- [x] 5.3 `SKILL_INFO.description` 中注明前置依赖：需要先调用 `create_biome_package` 创建植被包

## 6. 验证与清理

- [x] 6.1 删除旧的 `_find_artdata()` 函数（已被 `_find_root()` 替代）
- [x] 6.2 确认现有 `_generate_options()` 和 `_write_json()` 函数无需修改，保持复用
- [x] 6.3 端到端测试：用 `DesertShrub` / `Desert` / `TX3` 参数模拟调用，验证目录创建、文件生成、命名规范、返回值完整性
