# PCG 包体系核心概念

## 什么是"包"

"包"是本项目 PCG 工作流的核心配置单元。整套 PCG 系统被拆分为多个模块，每个模块负责一种地貌/场景元素的程序化生成。每个模块下可以创建多个"包"，每个包是一组完整的算法配置 + 资产配置 + 渲染层配置的集合。

例如："沙漠荒草植被包"是 BiomeTypes（植被包模块）下的一个具体包，定义了在沙漠环境中荒草类植被的撒点算法、模型资产和渲染层信息。

## 八大模块

| 模块目录 | 中文名 | 说明                                         |
|---------|--------|--------------------------------------------|
| LandTypes | 地貌包 | 地形生成的主模块，决定了地形的造型、侵蚀效果、材质渲染等，可引用/组合其他所有子系统 |
| BiomeTypes | 植被包 | 植被撒点（草、灌木、树木等）                             |
| CliffTypes | 岩石包 | 岩石/崖壁生成                                    |
| HillTypes | 山丘包 | 山丘地形                                       |
| RoadTypes | 道路包 | 道路（含模型生成 + 地形影响两阶段）                        |
| WaterTypes | 水系包 | 水体/河流/湖泊                                   |
| StageTypes | 平台包 | 平台/人工地形结构                                  |
| CityTypes | 城市包 | 城市/建筑群                                     |

**地貌包(LandTypes)是主包**，它具有引用/组合其他模块包的能力（通过 `xxxsys_info.json` 配置）。其他模块是子系统，可被地貌包组合使用。

## 目录结构约定

```
ArtData/                              ← PCG 配置总根目录
├── ArtHDAs/                          ← Houdini HDA 算法库（是 Houdini Path 路径）
│   ├── <项目名>/otls/*.hda             ← 按分类存放的 HDA 文件
├── <Module>Types/                    ← 某模块的包总目录
│   ├── <分类>/                       ← 第一层：分类目录（按项目名或种类区分）
│   │   ├── <包名>/                   ← 第二层：具体的包（包含一组 JSON 配置文件）
│   │   │   ├── xxx_info.json         ← 算法信息（指定 HDA 和参数）
│   │   │   ├── xxx_options.json      ← 资产分类列表
│   │   │   ├── xxx_asset.json        ← 资产入库（按 options 分类）
│   │   │   ├── kt_xxx_parm.json      ← HDA 参数配置
│   │   │   ├── subsys_info.json      ← 渲染层映射信息
│   │   │   ├── subsys_layers.json    ← 渲染层详细定义
│   │   │   ├── package_baseinfo.json ← 包元信息（描述、缩略图、标签）
│   │   │   ├── feature_info.json     ← 特征描述（建议填写，非必需）
│   │   │   └── *.json.desc.json      ← 描述文件（自动生成，忽略）
```

**分类目录**的命名由项目自行决定，可以按项目名区分（如 `TX3`、`SharePrj`），也可以按种类区分（如 `Forest`、`Desert`）。

## 渲染层映射机制

- **layers_base**：HDA 中定义的逻辑层名（如 `B1_Slope_Rock_01`），代表一个功能语义。
- **layers_order**：实际使用的渲染层名（如 `SharePrj_Rock_common_a`），决定具体的材质贴图表现。
- 映射规则：每个 layers_base **必须**指定一个 layers_order，但**多个** layers_base 可以指向同一个 layers_order。
- 这套机制使得同一个 HDA 算法可在不同项目中使用不同的贴图材质。

## JSON 文件约定

- 所有以 `.json.desc.json` 结尾的文件是描述文件，不需要手动创建或修改。
- `xxx_info.json` 中的路径使用相对于 `ArtData` 的路径（以 `/` 开头），如 `"/ArtHDAs/TX3/otls/kt_biome_desert_grass.hda"`。

## PCG 包创建行为规范（必须遵守）
当用户要求创建任何 PCG 包（植被包、岩石包、地貌包等）时，必须遵循以下规则：
1. ***所有包的创建都有对应的skill，必须通过skill去创建***。比如创建植被包的skill是create_biome_package。
2. **文档优先原则**：必须通过 `search_local_doc` 查询 Doc/pcg_package/ 下的文档来获取包的创建规范、目录结构、JSON 文件格式等信息。文档是权威参考，优先级高于任何自主分析或推断。
3. **禁止依赖已有包推断规范**：不要通过扫描 ArtData 下已有的包目录来推断命名规范或文件格式。原因：
   - 新项目前期可能没有任何已有包，扫描结果为空会导致错误信息
   - 已有包可能有历史遗留的非标准格式，不应作为参考
   - 文档中定义的规范才是正确的标准
4. **search_local_doc 常用查询关键词**：
   - 查询植被包规范：`"植被包 BiomeTypes"`、`"biome_info"`、`"biome_asset"`
   - 查询岩石包规范：`"岩石包 CliffTypes"`、`"cliff_info"`
   - 查询地貌包规范：`"地貌包 LandTypes"`、`"land_info"`
   - 查询包体系总览：`"PCG 包体系 模块"`
   - 查询渲染层机制：`"渲染层 layers_base layers_order"`
   - 查询生物群系选项：`"生物群系 biome"`
5. **分类目录可参考已有目录**：查看 ArtData 下已有的分类目录供用户选择或新建，这是正确的。但不要打开已有包的 JSON 文件来推断新包应该怎么写。
6. **项目名检测**：优先读取 project_info.json，如果不存在则扫描 ArtData/ArtHDAs/ 子目录让用户选择。这个扫描是为了获取项目名列表，不是为了分析包格式。
