# -*- coding: utf-8 -*-
"""植被包算法搭建 Skill（骨架）

在已创建的植被包 HDA 中搭建植被散布算法。
此 Skill 需要先通过 create_biome_package 创建植被包空壳后才能调用。

当前为骨架文件，仅定义接口参数，具体算法搭建逻辑后续补充。
"""

from typing import Dict, Any


SKILL_INFO = {
    "name": "build_biome_algorithm",
    "description": (
        "在已创建的植被包HDA中搭建植被散布算法。\n"
        "⚠️ 前置条件：需要先调用 create_biome_package 创建植被包空壳，获取返回的路径信息后再调用此工具。\n"
        "所需参数均来自 create_biome_package 的返回值。\n"
        "当前功能尚未实现，调用后会返回提示信息。"
    ),
    "parameters": {
        "package_dir": {
            "type": "string",
            "description": "植被包目录绝对路径（来自 create_biome_package 返回值）",
            "required": True,
        },
        "hda_path": {
            "type": "string",
            "description": "HDA 文件绝对路径（来自 create_biome_package 返回值）",
            "required": True,
        },
        "biome_type": {
            "type": "string",
            "description": "生物群系类型（来自 create_biome_package 返回值）",
            "required": True,
        },
        "density": {
            "type": "string",
            "description": "植被密度等级: high/medium/low（来自 create_biome_package 返回值）",
            "enum": ["high", "medium", "low"],
            "required": True,
        },
        "options": {
            "type": "string",
            "description": "逗号分隔的资产分类列表（来自 create_biome_package 返回值的 options 列表）",
            "required": True,
        },
    },
}


def run(package_dir: str, hda_path: str, biome_type: str,
        density: str, options: str, **kwargs) -> Dict[str, Any]:
    """在植被包 HDA 中搭建散布算法

    Args:
        package_dir: 植被包目录绝对路径
        hda_path: HDA 文件绝对路径
        biome_type: 生物群系类型
        density: 植被密度等级 (high/medium/low)
        options: 逗号分隔的资产分类列表
    """
    # TODO: Phase 3 — 算法搭建逻辑，后续补充
    return {
        "success": False,
        "error": "算法搭建功能尚未实现，请等待后续更新",
        "context": {
            "package_dir": package_dir,
            "hda_path": hda_path,
            "biome_type": biome_type,
            "density": density,
            "options": options,
        },
    }