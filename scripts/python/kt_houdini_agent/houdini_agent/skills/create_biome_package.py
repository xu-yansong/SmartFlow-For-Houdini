# -*- coding: utf-8 -*-
"""创建植被包 Skill

创建一个新的植被包（BiomeTypes），包含完整的目录结构和配置文件。
流程：
    0. 读取Doc/pcg_package/biome_knowledge.md,让用户做生态选择或自主输入生态描述
    1. 发现工程根目录（含 ArtData + HouTools）
    2. 检测项目名（project_info.json 或扫描 ArtData）
    3. PascalCase→snake_case 智能命名
    4. 新建植被包目录 ArtData/BiomeTypes/<分类>/<植被包名>
    5. 基于 kt_biome_template.hda 另存新 HDA 到项目目录
    6. 生成包内所有标准 JSON 配置文件
"""

import json
import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


SKILL_INFO = {
    "name": "create_biome_package",
    "description": (
        "创建一个新的植被包(BiomeTypes)。\n"
        "⚠️ 重要：了解植被包的目录结构、JSON文件格式、命名规范等信息时，"
        "必须通过 search_local_doc 查询 Doc/pcg_package/ 下的文档作为权威参考，"
        "不要通过分析已有包来推断规范（已有包可能不规范，新项目可能没有已有包）。\n\n"
        "⚠️ 对话规则（严格遵守）：\n"
        "调用前必须按顺序逐步收集信息，每次只问用户一个问题，等用户回答后再问下一个。\n"
        "禁止在一条消息中同时询问多个问题。\n"
        "能自动获取的信息（如项目名）先静默尝试，成功则跳过提问，失败再问用户。\n"
        "用户在之前对话中已明确提供的信息直接采用，不要重复询问。\n\n"
        "收集步骤（严格按此顺序，每步一轮对话）：\n"
        "步骤1 - 生物群系：读取 Doc/pcg_package/biome_knowledge.md，"
        "列出选项让用户选择。如果文档查询无结果，让用户自行描述生物群系。\n"
        "步骤2 - 植被密度：以带序号的列表形式询问密度等级，让用户可以直接回复序号选择：\n"
        "  1. high - 基本铺满\n"
        "  2. medium - 一半区域覆盖\n"
        "  3. low - 局部区域分布\n"
        "步骤3 - 项目名（静默检测）：调用_detect_project函数\n"
        "步骤4 - 植被包名：根据用户对植被生态的选择为植被包起一些贴近的英文名，以序号的方式让用户选择(PascalCase，首字母大写无下划线，如 DesertGrass)。也支持用户自定义输入\n"
        "步骤5 - 分类目录：查看 ArtData/BiomeTypes/ 下已有的分类目录，"
        "列出选项让用户选择或输入新分类名。\n"
        "步骤6 - 资产分类方式：询问使用 template(默认9种: Tree_L/M/S + Bush_L/M/S + Grass_L/M/S) "
        "还是 manual(手动指定)。如果用户选 manual，追问具体分类列表。\n\n"
        "全部信息收集完毕后，汇总所有参数让用户做最终确认，确认后再调用此工具。\n\n"
        "📖 如需了解植被包的目录结构、JSON 配置文件格式、渲染层映射等详细规范，"
        "直接阅读Doc/pcg_package/pcg_overview_knowledge_base.txt和pcg_biome_knowledge_base.txt两个文档\n"
    ),
    "parameters": {
        "package_name": {
            "type": "string",
            "description": "植被包名称(英文PascalCase)，如 ForestGrass、DesertTree",
            "required": True,
        },
        "category": {
            "type": "string",
            "description": "分类目录名，放在 BiomeTypes/<category>/ 下。选择已有目录或输入新名称",
            "required": True,
        },
        "project_name": {
            "type": "string",
            "description": "项目名称，决定 HDA 存储路径 ArtData/ArtHDAs/<project_name>/otls/",
            "required": True,
        },
        "biome_type": {
            "type": "string",
            "description": "生物群系类型，如 Tropical Rainforest、Chihuahuan Desert 等",
            "required": True,
        },
        "density": {
            "type": "string",
            "description": "植被密度等级",
            "enum": ["high", "medium", "low"],
            "required": True,
        },
        "options_mode": {
            "type": "string",
            "description": "资产分类方式: template(使用模板生成9种分类) 或 manual(手动指定)",
            "enum": ["template", "manual"],
            "required": True,
        },
        "custom_options": {
            "type": "string",
            "description": "仅 options_mode=manual 时需要。逗号分隔的资产分类名列表",
            "required": False,
        },
        "description": {
            "type": "string",
            "description": "用户对该植被包的自然语言描述，将写入 package_baseinfo.json",
            "required": False,
        },
        "tags": {
            "type": "string",
            "description": "逗号分隔的附加标签，将写入 package_baseinfo.json 的 Tags 字段",
            "required": False,
        },
    },
}


# ─────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────

def _find_root() -> Optional[Tuple[Path, Path]]:
    """向上搜索工程根目录（同时包含 ArtData/ 和 HouTools/ 的最近祖先）。

    Returns:
        (root, artdata) 元组，或 None（未找到）
    """
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "ArtData").is_dir() and (p / "HouTools").is_dir():
            return (p, p / "ArtData")
        p = p.parent
    return None


def _pascal_to_snake(name: str) -> str:
    """将 PascalCase 名称转换为 snake_case。

    连续大写字母视为同一个缩写词，不做额外拆分。
    示例:
        DesertGrass    → desert_grass
        PCGBiome       → pcg_biome
        ForestHTMLTree → forest_html_tree
        ForestTreeV2   → forest_tree_v2
    """
    # 步骤1: 在 "连续大写 + 大写小写" 边界插入下划线
    #   例: PCGBiome → PCG_Biome,  HTMLTree → HTML_Tree
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    # 步骤2: 在 "小写/数字 + 大写" 边界插入下划线
    #   例: Desert_Grass (已OK),  TreeV2 → Tree_V2 (如需), forest_tree → 不变
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    return s.lower()


def _detect_project(artdata: Path) -> Dict[str, Any]:
    """检测当前工作项目名。

    优先级:
      1. 读取 %USERPROFILE%/.pangu/KaiTian/ProjectConfig/project_info.json
      2. 扫描 ArtData/ArtHDAs/ 子目录（排除 SharePrj）

    Returns:
        {"project": "TX3"}            — 成功自动检测
        {"candidates": ["TX3", ...]}  — 需要用户选择
        {"error": "..."}              — 检测失败
    """
    # 方式1: 读取 project_info.json
    user_home = Path(os.path.expanduser("~"))
    project_info_path = user_home / ".pangu" / "KaiTian" / "ProjectConfig" / "project_info.json"
    if project_info_path.is_file():
        try:
            with open(str(project_info_path), "r", encoding="utf-8") as f:
                data = json.load(f)
            proj = data.get("project", "").strip()
            if proj:
                return {"project": proj}
        except Exception:
            pass  # 读取失败，回退到方式2

    # 方式2: 扫描 ArtData/ArtHDAs/ 子目录
    hdas_dir = artdata / "ArtHDAs"
    if not hdas_dir.is_dir():
        return {"error": "ArtData/ArtHDAs/ 目录不存在"}

    candidates = [
        d.name for d in hdas_dir.iterdir()
        if d.is_dir() and d.name != "SharePrj"
    ]

    if len(candidates) == 1:
        return {"project": candidates[0]}
    elif len(candidates) > 1:
        return {"candidates": sorted(candidates)}
    else:
        return {"error": "ArtData/ArtHDAs/ 下没有找到项目目录（SharePrj 除外），请手动指定 project_name"}


def _generate_options(package_name: str, mode: str, custom: str = "") -> List[str]:
    """生成资产分类列表"""
    if mode == "template":
        suffixes = [
            "Tree_L", "Tree_M", "Tree_S",
            "Bush_L", "Bush_M", "Bush_S",
            "Grass_L", "Grass_M", "Grass_S",
        ]
        return [f"{package_name}_{s}" for s in suffixes]
    else:
        return [s.strip() for s in custom.split(",") if s.strip()]


def _write_json(filepath: Path, data) -> None:
    """写入 JSON 文件（tab 缩进，与项目现有格式一致）"""
    with open(str(filepath), "w", encoding="utf-8") as f:
        json.dump(data, f, indent="\t", ensure_ascii=False)


def _copy_hda_template(artdata: Path, project_name: str,
                       snake_name: str) -> Dict[str, Any]:
    """基于 kt_biome_template.hda 另存新 HDA

    模板路径: ArtData/ArtHDAs/SharePrj/otls/kt_biome_template.hda (只读)
    输出路径: ArtData/ArtHDAs/{project_name}/otls/kt_biome_{snake_name}.hda

    优先使用 Houdini API（可重命名内部类型名），
    失败则回退到文件复制。
    """
    template_path = artdata / "ArtHDAs" / "SharePrj" / "otls" / "kt_biome_template.hda"
    output_dir = artdata / "ArtHDAs" / project_name / "otls"
    new_hda_name = f"kt_biome_{snake_name}.hda"
    new_hda_path = output_dir / new_hda_name

    if not template_path.exists():
        return {"success": False, "error": f"模板 HDA 不存在: {template_path}"}

    if new_hda_path.exists():
        return {"success": False, "error": f"HDA 文件已存在: {new_hda_path}"}

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 方式一：使用 Houdini API 复制并重命名 HDA 类型
    hou_error = ""
    try:
        import hou  # type: ignore
        defs = hou.hda.definitionsInFile(str(template_path))
        if defs:
            new_type_name = f"kt_biome_{snake_name}"
            defs[0].copyToHDAFile(str(new_hda_path), new_type_name)
            hou.hda.installFile(str(new_hda_path))
            return {
                "success": True,
                "hda_path": str(new_hda_path),
                "method": "hou_api",
            }
        else:
            raise RuntimeError("模板 HDA 中未找到定义")
    except Exception as e:
        hou_error = str(e)

    # 方式二：回退到文件复制
    try:
        shutil.copy2(str(template_path), str(new_hda_path))
        return {
            "success": True,
            "hda_path": str(new_hda_path),
            "method": "file_copy",
            "warning": f"Houdini API 复制失败({hou_error})，已使用文件复制，HDA 内部类型名仍为模板名",
        }
    except Exception as e2:
        return {"success": False, "error": f"HDA 复制失败: {e2}"}


# ─────────────────────────────────────────────────
# JSON 文件内容生成器
# ─────────────────────────────────────────────────

def _make_biome_info(snake_name: str, project_name: str,
                     package_name: str, category: str) -> dict:
    """biome_info.json — 路径均相对于 ArtData"""
    return {
        "hda_name": f"/ArtHDAs/{project_name}/otls/kt_biome_{snake_name}.hda",
        "hda_parm": f"/BiomeTypes/{category}/{package_name}/kt_biome_{snake_name}_parm.json",
        "PCGGraph": "",
    }


def _make_biome_asset(options: List[str]) -> dict:
    """biome_asset.json —— 按 options 生成空资产骨架"""
    asset = {}
    for opt in options:
        asset[opt] = {
            "type": opt,
            "assetlist": {},
        }
    return asset


def _make_subsys_info() -> dict:
    """subsys_info.json —— 默认空配置"""
    return {
        "TargetLayouts": [],
        "OverEnable": False,
        "SubsysType": "",
        "SubsysHda": [""],
        "SubsysParm": [""],
        "layers_base": ["_"],
        "layers_order": [""],
        "layers_biomesys": [""],
        "landtype_biomesys": [""],
        "layers_order_overrides": [],
    }


def _make_package_baseinfo(description: str = "",
                           biome_type: str = "",
                           density: str = "",
                           tags: str = "") -> dict:
    """package_baseinfo.json — 预填充描述和标签"""
    # 构建 Tags 列表
    tag_list = []
    if biome_type:
        tag_list.append(biome_type)
    if density:
        tag_list.append(f"density:{density}")
    # 合并用户自定义 tags
    if tags:
        for t in tags.split(","):
            t = t.strip()
            if t and t not in tag_list:
                tag_list.append(t)

    return {
        "package description": description,
        "package thumbnail": "",
        "reference_images": [],
        "Tags": tag_list,
    }


# ─────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────

def run(package_name: str, category: str, project_name: str,
        biome_type: str, density: str, options_mode: str = "template",
        custom_options: str = "", description: str = "",
        tags: str = "", **kwargs) -> Dict[str, Any]:
    """创建一个新的植被包

    Args:
        package_name: 植被包名称（PascalCase），如 ForestGrass
        category: 分类目录名，如 Desert、Forest、SharePrj
        project_name: 项目名称，如 TX3
        biome_type: 生物群系类型，如 Chihuahuan Desert
        density: 植被密度等级 - "high" / "medium" / "low"
        options_mode: 资产分类方式 - "template" 或 "manual"
        custom_options: 手动模式下逗号分隔的分类列表
        description: 用户对该植被包的自然语言描述
        tags: 逗号分隔的附加标签
    """

    # ── 0. 查找工程根目录 ──
    root_result = _find_root()
    if not root_result:
        return {"success": False, "error": "找不到工程根目录（需同时包含 ArtData/ 和 HouTools/），请确认工程路径正确"}
    root, artdata = root_result

    # ── 1. 参数校验 ──
    package_name = package_name.strip()
    category = category.strip()
    project_name = project_name.strip()
    biome_type = biome_type.strip()
    density = density.strip().lower()

    if not package_name:
        return {"success": False, "error": "植被包名称(package_name)不能为空"}
    if not category:
        return {"success": False, "error": "分类目录(category)不能为空"}
    if not project_name:
        return {"success": False, "error": "项目名称(project_name)不能为空"}
    if not biome_type:
        return {"success": False, "error": "生物群系类型(biome_type)不能为空"}
    if density not in {"high", "medium", "low"}:
        return {"success": False, "error": f"植被密度(density)必须为 high/medium/low，当前值: '{density}'"}

    # ── 2. 名称转换与校验 ──
    snake_name = _pascal_to_snake(package_name)
    if not re.fullmatch(r'[a-z0-9_]+', snake_name):
        return {"success": False, "error": f"植被包名称转换后不合法: '{package_name}' → '{snake_name}'，请使用纯英文 PascalCase"}

    # ── 3. 生成资产分类列表 ──
    options = _generate_options(package_name, options_mode, custom_options)
    if not options:
        return {"success": False, "error": "资产分类列表为空。manual 模式请提供 custom_options"}

    # ── 4. 检查目录是否已存在 ──
    package_dir = artdata / "BiomeTypes" / category / package_name
    if package_dir.exists():
        return {"success": False, "error": f"植被包目录已存在: {package_dir}"}

    # ── 5. 创建植被包目录 ──
    package_dir.mkdir(parents=True, exist_ok=True)

    # ── 6. 确保 HDA 项目目录存在 ──
    hda_output_dir = artdata / "ArtHDAs" / project_name / "otls"
    hda_output_dir.mkdir(parents=True, exist_ok=True)

    created_files = []
    warnings = []

    # ── 7. 复制 HDA 模板 ──
    hda_result = _copy_hda_template(artdata, project_name, snake_name)
    hda_path = ""
    if hda_result.get("success"):
        hda_path = hda_result["hda_path"]
        created_files.append(hda_path)
        if hda_result.get("warning"):
            warnings.append(hda_result["warning"])
    else:
        warnings.append(f"HDA 创建失败: {hda_result.get('error', '未知错误')}")

    # ── 8. 生成所有 JSON 配置文件 ──
    files_to_create = {
        "biome_info.json": _make_biome_info(snake_name, project_name, package_name, category),
        "biome_options.json": options,
        "biome_asset.json": _make_biome_asset(options),
        f"kt_biome_{snake_name}_parm.json": {},
        "subsys_info.json": _make_subsys_info(),
        "subsys_layers.json": {},
        "package_baseinfo.json": _make_package_baseinfo(
            description=description,
            biome_type=biome_type,
            density=density,
            tags=tags,
        ),
    }

    errors = []
    for filename, content in files_to_create.items():
        filepath = package_dir / filename
        try:
            _write_json(filepath, content)
            created_files.append(filename)
        except Exception as e:
            errors.append(f"{filename}: {e}")

    # ── 9. 汇总结果 ──
    total_ok = len(files_to_create) - len(errors) + (1 if hda_result.get("success") else 0)
    total_all = len(files_to_create) + 1

    result = {
        "success": len(errors) == 0,
        "package_dir": str(package_dir),
        "hda_path": hda_path,
        "project_name": project_name,
        "biome_type": biome_type,
        "density": density,
        "options": options,
        "algorithm_pending": True,
        "created_files": created_files,
    }

    if errors:
        result["errors"] = errors
    if warnings:
        result["warnings"] = warnings

    result["summary"] = (
        f"植被包 '{package_name}' 已创建完成\n"
        f"位置: BiomeTypes/{category}/{package_name}/\n"
        f"HDA: ArtHDAs/{project_name}/otls/kt_biome_{snake_name}.hda\n"
        f"群系: {biome_type} | 密度: {density}\n"
        f"文件: {total_ok}/{total_all} 成功"
        + (f"，{len(errors)} 个失败" if errors else "")
        + (f"\n警告: {'; '.join(warnings)}" if warnings else "")
        + f"\n资产分类({len(options)}种): {', '.join(options)}"
        + "\n\n⚠️ 算法搭建尚未完成(algorithm_pending=True)，可调用 build_biome_algorithm 继续"
    )

    return result