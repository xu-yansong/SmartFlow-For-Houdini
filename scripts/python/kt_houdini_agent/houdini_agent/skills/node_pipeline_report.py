# -*- coding: utf-8 -*-
"""节点管线分析报告 Skill

对任意节点（尤其是 subnet / 用户自定义 HDA）做分层剖析，自动进入内部逐层分析，
截图每个环节视口结果，输出两份 HTML：
  index.html    —— 交互式节点图报告（左右可拖拽分栏：左上截图 + 左下详情 + 右侧节点图），主入口
  pipeline.html —— 三级目录长文档版，适合通读打印

侧栏信息顺序：节点功能 → 基本信息 → 输入依赖的属性 → 输出属性变化 → 输入源
           → 可能的坑点 → 下游节点 → 已修改参数 → VEX 代码
输出属性只记增量：+ 新增 / ~ 修改 / - 清除，不全量罗列。

方法论来源：KT RoadSys 道路系统分析实践。
"""

SKILL_INFO = {
    "name": "analyze_node_pipeline",
    "description": (
        "【节点分析报告生成器】对指定节点做完整的分层管线剖析并输出可视化 HTML 报告。"
        "自动递归进入 subnet 与用户自定义 HDA 内部，逐环节提取：节点功能说明、几何统计（点数/面数）、"
        "输入依赖的属性、输出属性变化、输入源、可能的坑点、下游节点、已修改参数、VEX 代码，"
        "并按指定相机为每个环节在 Houdini 视口截图。"
        "\n\n【输出属性只记增量】输出属性一栏不全量罗列，只显示本环节相对其输入端的变化，分三类："
        "绿色“+ 新增”（输入端没有、本节点新产生的属性）、"
        "橙色“~ 修改”（输入端已有、本节点重新写入的属性）、"
        "红色“- 清除”（本节点删除的属性，超过 12 项自动折叠）。"
        "无变化时显示“无属性变化（仅几何/拓扑处理）”。"
        "侧栏区块顺序固定为：节点功能 → 基本信息 → 输入依赖的属性 → 输出属性变化 → 输入源 → "
        "可能的坑点 → 下游节点 → 已修改参数 → VEX 代码。"
        "\n\n【产出两个网页，入口是 index.html】"
        "① index.html（返回值 report 指向它，主入口）：交互式节点图报告，左右分栏——"
        "左栏上部固定显示当前选中环节的视口截图（带节点名/类型/点面数标注，点击全屏放大），"
        "左栏下部显示该环节详细信息；右栏是可缩放拖拽的节点图，支持单击看详情、双击进入子网、"
        "面包屑逐级返回、F 键复位、Esc 返回上层，foreach 循环区用紫色虚线框标出。"
        "左右分割线、左栏上下分割线均可用鼠标拖动调整比例。"
        "② pipeline.html：同一份内容的三级目录长文档版（1 / 1.1 / 1.1.1 编号），左侧为可跳转目录，"
        "点击任意环节截图会打开灯箱，可用「◀ 上一张 / 下一张 ▶」按钮或 ←→ 方向键在全部环节截图间翻页对比，"
        "Esc 关闭；适合通读与打印。"
        "两个网页已双向互链：index.html 顶栏右侧「☰ 文档版报告」跳到 pipeline.html，"
        "pipeline.html 左上「◀ 节点图视图」跳回 index.html。"
        "\n\n当用户说“帮我分析 xxx 节点功能 / 看懂这个节点 / 生成节点报告”时使用。"
        "\n\n【重要·调用前必须先询问用户】本 Skill 支持把分析结论写回 Houdini 节点（add_comments 参数）。"
        "调用前你必须先用一句话问用户：“是否需要同时把分析说明写入节点备注？"
        "（wrangle 节点会在代码开头加注释块，其余节点加 comment；涉及解锁 HDA）”，"
        "得到用户明确答复后再调用，不要自作主张传 add_comments=true。"
    ),
    "parameters": {
        "node_path": {
            "type": "string",
            "description": "要分析的节点路径，如 /obj/geo1/RoadGenerator",
            "required": True,
        },
        "output_dir": {
            "type": "string",
            "description": (
                "报告输出目录。留空则自动输出到 $HIP/NodeAnalysis/<节点名>/ ，"
                "用户指定路径时则输出到指定位置（支持 $HIP 等环境变量）。"
            ),
        },
        "camera": {
            "type": "string",
            "description": "截图使用的相机路径，如 /obj/cam1。留空则用当前视角并自动 frameAll",
        },
        "max_depth": {
            "type": "integer",
            "description": "递归进入子网的最大层级，默认 3（1=只看直属，3=可到孙层）",
            "default": 3,
        },
        "screenshots": {
            "type": "boolean",
            "description": "是否截图，默认 True。关掉可快速出纯文字报告",
            "default": True,
        },
        "shot_width": {
            "type": "integer",
            "description": "截图宽度，默认 1280",
            "default": 1280,
        },
        "max_nodes": {
            "type": "integer",
            "description": "最多分析多少个环节，默认 40，防止超大网络耗时过久",
            "default": 40,
        },
        "add_comments": {
            "type": "boolean",
            "description": (
                "是否把分析说明写回 Houdini 节点，默认 False。"
                "【必须先征得用户同意才可设为 true】开启后："
                "① 自动解锁途经的用户 HDA（会使该实例脱离 HDA 定义同步）；"
                "② wrangle 类节点在 snippet 最开头插入四段式注释块"
                "（功能介绍/必要的引用属性/输出属性/可能的坑点），"
                "★绝不修改任何原始代码★，且不为其设置 comment；"
                "③ 非 wrangle 节点写入 comment 并开启视口显示。"
                "全程自动备份、幂等跳过、写入后校验原码，异常自动回滚。"
            ),
            "default": False,
        },
        "open_browser": {
            "type": "boolean",
            "description": (
                "分析完成后是否用系统默认浏览器自动打开报告网页，默认 True。"
                "设为 False 则只生成文件不弹窗。"
            ),
            "default": True,
        },
        "unlock_hda": {
            "type": "boolean",
            "description": (
                "add_comments 为 true 时，是否允许解锁被锁定的用户 HDA，默认 True。"
                "解锁会让该 HDA 实例脱离定义同步（库文件更新时不再自动跟随）。"
                "设为 False 则跳过锁定的 HDA 内部，不做修改。"
            ),
            "default": True,
        },
    },
}

# ---------- 内部工具 ----------

_BUILTIN_HINT = ("oplibsop", "oplibvop", "oplibscripted", "oplibobj",
                 "oplibdop", "oplibcop", "oplibchop", "houdini/otls")


def _is_user_hda(node):
    """判断是否用户自定义 HDA（排除 Houdini 内置节点）"""
    try:
        d = node.type().definition()
        if d is None:
            return False
        lib = (d.libraryFilePath() or "").replace("\\", "/").lower()
        for h in _BUILTIN_HINT:
            if h in lib:
                return False
        return True
    except Exception:
        return False


def _kind_of(node):
    """返回节点类别标签"""
    try:
        if _is_user_hda(node):
            return "hda"
        if node.type().name() == "subnet":
            return "subnet"
    except Exception:
        pass
    return ""


def _geo_stat(node):
    """安全获取几何统计"""
    try:
        g = node.geometry()
        if g is None:
            return None
        return {
            "pts": len(g.points()),
            "prims": len(g.prims()),
            "pt_attrs": sorted([a.name() for a in g.pointAttribs()]),
            "pr_attrs": sorted([a.name() for a in g.primAttribs()]),
            "det_attrs": sorted([a.name() for a in g.globalAttribs()]),
            "pt_groups": [x.name() for x in g.pointGroups()],
            "pr_groups": [x.name() for x in g.primGroups()],
        }
    except Exception:
        return None


def _get_vex(node):
    """提取节点的 VEX / Python 代码"""
    out = []
    try:
        p = node.parm("snippet")
        if p and p.eval().strip():
            cls = node.parm("class").eval() if node.parm("class") else None
            cm = {0: "Detail", 1: "Primitives", 2: "Points", 3: "Vertices", 4: "Numbers"}
            out.append(("VEX (%s)" % cm.get(cls, "?"), p.eval().strip()))
    except Exception:
        pass
    try:
        if node.type().name() == "python":
            p = node.parm("python")
            if p and p.eval().strip():
                out.append(("Python SOP", p.eval().strip()))
    except Exception:
        pass
    return out


def _walk(root, max_depth, max_nodes):
    """按真实执行顺序（拓扑序）遍历节点树，收集分析环节

    规则:
      1. 从输出锚点回溯，用 post-order DFS 保证每个节点的所有上游先输出
      2. 遇到 for-each 循环(block_end)：循环体内部节点整体降一级(lv+1)
      3. 遇到 subnet / 用户 HDA：内部节点降一级(lv+1)
    返回 [{lv, node, path, name, kind, nkids, stat, vex, in_loop}]
    """
    items = []
    emitted = set()

    def _anchor_of(parent):
        """找容器的输出锚点：output 节点 > display 节点 > 无下游的末端 > 最后一个"""
        try:
            kids = list(parent.children())
        except Exception:
            return None, []
        if not kids:
            return None, []
        anchor = None
        for c in kids:
            if c.type().name() == "output":
                anchor = c
                break
        if anchor is None:
            try:
                d = parent.displayNode()
                if d is not None and d.parent() is not None \
                        and d.parent().path() == parent.path():
                    anchor = d
            except Exception:
                anchor = None
        if anchor is None:
            tails = []
            for c in kids:
                try:
                    outs = [o for o in c.outputs()
                            if o is not None and o.parent() is not None
                            and o.parent().path() == parent.path()]
                    if not outs:
                        tails.append(c)
                except Exception:
                    pass
            if tails:
                anchor = tails[-1]
        if anchor is None:
            anchor = kids[-1]
        return anchor, kids

    def _loop_body(end_node, parent):
        """收集 for-each 循环体：从 block_end 回溯到 block_begin（含两端）"""
        body = set()
        stack = [end_node]
        while stack:
            n = stack.pop()
            if n is None or n.path() in body:
                continue
            body.add(n.path())
            if n.type().name().startswith("block_begin"):
                continue
            try:
                for i in n.inputs():
                    if (i is not None and i.path() not in body
                            and i.parent() is not None
                            and i.parent().path() == parent.path()):
                        stack.append(i)
            except Exception:
                pass
        return body

    def _add(node, lv, loop_name):
        """输出一个环节"""
        if len(items) >= max_nodes:
            return False
        tname = node.type().name()
        if tname in ("output", "subinput", "indirect"):
            return True
        kind = _kind_of(node)
        nk = 0
        try:
            nk = len(node.children())
        except Exception:
            pass
        items.append({
            "lv": lv,
            "node": node,
            "path": node.path(),
            "name": node.name(),
            "type": tname,
            "kind": kind,
            "nkids": nk,
            "stat": _geo_stat(node),
            "vex": _get_vex(node),
            "in_loop": loop_name,
        })
        # subnet / HDA：内部降一级
        if kind in ("subnet", "hda") and nk > 0 and lv < max_depth:
            _emit_container(node, lv + 1)
        return True

    def _emit_node(node, parent, lv, loop_name, scope):
        """post-order：先递归所有上游输入，再输出自身 —— 保证严格执行顺序"""
        if node is None or len(items) >= max_nodes:
            return
        pth = node.path()
        if pth in emitted:
            return
        if scope is not None and pth not in scope:
            return
        if node.parent() is None or node.parent().path() != parent.path():
            return
        emitted.add(pth)

        tname = node.type().name()
        # for-each 循环：整个循环体降一级，先出循环体，再出 block_end 本身
        if tname.startswith("block_end") and lv < max_depth:
            body = _loop_body(node, parent)
            body.discard(pth)
            # 循环入口的上游（循环外的数据源）先输出，保持执行顺序
            begins = []
            for bp in body:
                bn = hou.node(bp)
                if bn is not None and bn.type().name().startswith("block_begin"):
                    begins.append(bn)
            for bn in begins:
                try:
                    for i in bn.inputs():
                        if (i is not None and i.parent() is not None
                                and i.parent().path() == parent.path()
                                and i.path() not in body):
                            _emit_node(i, parent, lv, loop_name, scope)
                except Exception:
                    pass
            # 循环体按拓扑序输出，级别 +1
            lname = node.name()
            for bn in begins:
                _emit_node(bn, parent, lv + 1, lname, body)
            for bp in sorted(body):
                _emit_node(hou.node(bp), parent, lv + 1, lname, body)
            _add(node, lv, loop_name)
            return

        # 普通节点：先所有输入（上游）
        try:
            for i in node.inputs():
                if (i is not None and i.parent() is not None
                        and i.parent().path() == parent.path()):
                    _emit_node(i, parent, lv, loop_name, scope)
        except Exception:
            pass
        _add(node, lv, loop_name)

    def _emit_container(parent, lv):
        """输出一个容器内部的全部节点，按执行顺序"""
        if lv > max_depth or len(items) >= max_nodes:
            return
        anchor, kids = _anchor_of(parent)
        if anchor is None:
            return
        _emit_node(anchor, parent, lv, "", None)
        # 补上不在主链上的旁支（同样走 post-order，保证其上游在前）
        for c in kids:
            if c.path() not in emitted:
                _emit_node(c, parent, lv, "", None)

    import hou  # type: ignore
    _emit_container(root, 1)
    return items


def _diff_attrs(cur, prev):
    """对比属性变化，返回 (新增, 清除)"""
    if not cur:
        return [], []
    if not prev:
        return [], []
    new, gone = [], []
    for k, tag in (("pt_attrs", "pt"), ("pr_attrs", "pr"), ("det_attrs", "det")):
        for a in cur.get(k, []):
            if a not in prev.get(k, []):
                new.append(a + " <sub>" + tag + "</sub>")
        for a in prev.get(k, []):
            if a not in cur.get(k, []):
                gone.append(a)
    return new, gone


def _display_chain(node):
    """点亮从 node 到最外层 obj 的整条显示链，保证内部节点能真正显示在视口"""
    import hou  # type: ignore
    restore = []
    cur = node
    try:
        cur.setDisplayFlag(True)
    except Exception:
        return None, restore
    par = cur.parent()
    while par is not None:
        try:
            if par.type().category().name() != "Sop":
                break
            old = par.displayNode()
            restore.append((par, old))
            par.setDisplayFlag(True)
        except Exception:
            pass
        cur = par
        par = par.parent()
    return cur, restore


def _img_sig(fpath):
    """取图像内容指纹，用于检测截图是否重复"""
    import hashlib
    try:
        d = open(fpath, "rb").read()
        return hashlib.md5(d).hexdigest()
    except Exception:
        return None


def _all_graph_nodes(root, max_depth=None):
    """收集 root 内部【所有层级】的全部节点，保证每个 Houdini 节点都有截图。

    max_depth 保留仅为兼容旧调用，截图阶段一律无视深度限制做全量递归。
    """
    out = []
    seen = set()

    def _grab(parent):
        try:
            kids = list(parent.children())
        except Exception:
            return
        for n in kids:
            pth = n.path()
            if pth in seen:
                continue
            seen.add(pth)
            out.append(n)
            try:
                if n.children():
                    _grab(n)
            except Exception:
                pass

    _grab(root)
    return out


def _rel_shot_name(node, root):
    """截图文件名 = 节点相对源节点的路径名，如 clean_overlap__copytopoints1.jpg"""
    import re as _re
    try:
        npth = node.path()
        rpth = root.path()
    except Exception:
        return "unknown"
    if npth.startswith(rpth + "/"):
        rel = npth[len(rpth) + 1:]
    elif npth == rpth:
        rel = root.name()
    else:
        rel = npth.lstrip("/")
    rel = rel.replace("/", "__")
    rel = _re.sub(r"[^0-9A-Za-z_.\-]", "_", rel)
    return rel or "unknown"


def _shoot(items, out_dir, camera, width, host_geo, extra_nodes=None, root=None):
    """为每个环节（以及节点图中的所有节点）截图，返回 {path: 文件名}

    关键点（踩过的坑）：
      1. 必须用 sv.setPwd(node.parent()) 把 Scene Viewer 的当前网络切进节点
         所在的内部网络（等同用户双击进入 subnet），再 setDisplayFlag(True)。
         否则视口始终停留在最外层，看到的永远是最终输出，所有截图雷同。
      2. 用户指定了相机就【始终】用该相机机位截图，绝不做任何自适应取景，
         保证所有环节同机位可比。只有未指定相机时才 frameAll 建立一次取景。
    """
    import hou  # type: ignore
    import time
    import os as _os

    shots = {}
    sv = None
    for pane in hou.ui.paneTabs():
        if pane.type() == hou.paneTabType.SceneViewer:
            sv = pane
            break
    if sv is None:
        return shots
    vp = sv.curViewport()

    orig_pwd = None
    try:
        orig_pwd = sv.pwd()
    except Exception:
        pass

    cam = hou.node(camera) if camera else None
    if cam:
        try:
            vp.setCamera(cam)
            hou.ui.triggerUpdate()
            time.sleep(0.2)
        except Exception:
            cam = None

    shot_dir = _os.path.join(out_dir, "shots")
    if not _os.path.isdir(shot_dir):
        _os.makedirs(shot_dir)
    else:
        # 清理历史遗留的旧式序号截图，避免与相对路径命名混杂
        import re as _re2
        for _f in _os.listdir(shot_dir):
            if _re2.match(r"^s\d{3}\.jpg$", _f):
                try:
                    _os.remove(_os.path.join(shot_dir, _f))
                except Exception:
                    pass

    targets = []
    seen = set()
    info_of = {}
    for it in items:
        pth = it["path"]
        if pth in seen:
            continue
        seen.add(pth)
        targets.append((pth, it["node"]))
        info_of[pth] = it
    for n in (extra_nodes or []):
        try:
            pth = n.path()
        except Exception:
            continue
        if pth in seen:
            continue
        seen.add(pth)
        targets.append((pth, n))

    orig_disp = {}
    height = int(width * 9 / 16)
    tmp_nodes = []
    sig_map = {}
    dup_count = 0
    framed = False
    used_names = set()

    for idx, (pth, node) in enumerate(targets):
        if root is not None:
            fname = _rel_shot_name(node, root) + ".jpg"
        else:
            fname = "s%03d.jpg" % idx
        if fname in used_names:
            fname = "%s_%03d.jpg" % (fname[:-4], idx)
        used_names.add(fname)
        fpath = _os.path.join(shot_dir, fname)
        target = node
        ok = True
        try:
            par = node.parent()
            if par is not None:
                if par.path() not in orig_disp:
                    try:
                        orig_disp[par.path()] = par.displayNode()
                    except Exception:
                        pass
                # 核心：把视口当前网络切进该节点所在网络，等同双击进入
                try:
                    sv.setPwd(par)
                except Exception:
                    pass
            node.setDisplayFlag(True)
        except Exception:
            ok = False
        if not ok:
            try:
                nm = "TMP_RPT_%03d" % idx
                t = host_geo.node(nm) or host_geo.createNode("object_merge", nm)
                t.parm("objpath1").set(pth)
                t.parm("xformtype").set(1)
                try:
                    sv.setPwd(host_geo)
                except Exception:
                    pass
                t.setDisplayFlag(True)
                tmp_nodes.append(t)
                target = t
            except Exception:
                continue
        try:
            target.cook(force=True)
        except Exception:
            pass
        try:
            hou.ui.triggerUpdate()
        except Exception:
            pass
        time.sleep(0.35)

        if cam:
            # 用户指定相机：始终锁定该机位，不做任何自适应
            try:
                if vp.camera() is None or vp.camera().path() != cam.path():
                    vp.setCamera(cam)
            except Exception:
                pass
        elif not framed:
            try:
                vp.frameAll()
                hou.ui.triggerUpdate()
                time.sleep(0.2)
                framed = True
            except Exception:
                pass

        try:
            st = sv.flipbookSettings().stash()
            st.output(fpath)
            st.frameRange((hou.frame(), hou.frame()))
            st.outputToMPlay(False)
            st.resolution((width, height))
            st.useResolution(True)
            sv.flipbook(vp, st)
            time.sleep(0.18)
            if _os.path.exists(fpath):
                sig = _img_sig(fpath)
                if sig is not None:
                    if sig in sig_map:
                        dup_count += 1
                        it = info_of.get(pth)
                        if it is not None:
                            it["shot_dup_of"] = sig_map[sig]
                    else:
                        sig_map[sig] = pth
                shots[pth] = "shots/" + fname
        except Exception:
            pass

    for t in tmp_nodes:
        try:
            t.destroy()
        except Exception:
            pass
    for pth, oldn in orig_disp.items():
        try:
            if oldn is not None:
                oldn.setDisplayFlag(True)
        except Exception:
            pass
    try:
        if orig_pwd is not None:
            sv.setPwd(orig_pwd)
    except Exception:
        pass
    shots["__dup__"] = dup_count
    return shots


_CSS = """
:root{--bg:#0f1115;--pan:#161920;--card:#1b1f27;--fg:#d8dee9;--dim:#8a95a5;--acc:#6cb6ff;
--ok:#a3d977;--warn:#ffb454;--err:#ff6b6b;--bd:#2a2f39;--pur:#c792ea;--cy:#4dd0e1;--pink:#ff9ecd}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}
#side{position:fixed;left:0;top:0;bottom:0;width:288px;background:var(--pan);border-right:1px solid var(--bd);overflow-y:auto;padding:15px 0 40px;z-index:40}
#side h1{font-size:14px;color:var(--acc);margin:0 14px 3px}
#side .sub{font-size:11px;color:var(--dim);margin:0 14px 12px;line-height:1.5}
.backbtn{display:inline-flex;align-items:center;gap:5px;margin:0 14px 12px;padding:4px 11px;background:#22384d;color:var(--acc);border:1px solid #2f4d68;border-radius:4px;font-size:11.5px;text-decoration:none}
.backbtn:hover{background:#2b4661}
.ol-i{display:block;padding:5px 12px 5px 14px;color:var(--dim);text-decoration:none;font-size:12.2px;border-left:3px solid transparent;line-height:1.4}
.ol-i:hover{background:#1f242c;color:var(--fg)}
.ol-i.on{background:#212832;color:var(--acc);border-left-color:var(--acc)}
.ol-i .n{display:inline-block;min-width:17px;height:17px;border-radius:3px;background:var(--bd);color:var(--fg);font-size:9.5px;text-align:center;line-height:17px;margin-right:5px}
.ol-i.on .n{background:var(--acc);color:#0f1115;font-weight:700}
.ol-i .nd{display:block;font-size:10px;color:#5f6875;font-family:Consolas,monospace;margin-left:22px}
.lv1{font-weight:600;font-size:12.8px;color:#b9c4d2;border-top:1px solid var(--bd);margin-top:5px;padding-top:9px}
.lv2{padding-left:30px;font-size:11.8px}
.lv3{padding-left:48px;font-size:11.3px;color:#79838f}
.lv2 .nd,.lv3 .nd{margin-left:0}
.bdg{font-size:9px;padding:1px 5px;border-radius:7px;margin-left:5px}
.bdg.h{background:#4a2a3c;color:var(--pink)}
.bdg.s{background:#23323f;color:var(--cy)}
main{margin-left:288px;padding:0 28px 90px}
header{position:sticky;top:0;z-index:30;background:rgba(15,17,21,.97);border-bottom:1px solid var(--bd);padding:13px 0 11px;margin-bottom:18px}
header h2{margin:0;font-size:17px;color:var(--acc)}
header .m{font-size:11.5px;color:var(--dim);margin-top:2px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:9px;margin-bottom:15px;overflow:hidden;scroll-margin-top:70px}
.card.l1{border-left:4px solid var(--acc)}
.card.l2{margin-left:28px;border-left:4px solid var(--cy)}
.card.l3{margin-left:56px;border-left:4px solid var(--pink)}
.hd{display:flex;align-items:center;gap:9px;padding:10px 15px;background:var(--pan);border-bottom:1px solid var(--bd);flex-wrap:wrap}
.hd .num{padding:2px 8px;border-radius:10px;background:var(--acc);color:#0f1115;font-weight:700;font-size:10.5px}
.card.l2 .hd .num{background:var(--cy)}
.card.l3 .hd .num{background:var(--pink)}
.hd h4{margin:0;font-size:14.5px;flex:1;min-width:170px}
.hd .nn{font-family:Consolas,monospace;font-size:11.5px;color:var(--ok);background:#16241a;padding:2px 8px;border-radius:4px;border:1px solid #2c4534}
.np{font-family:Consolas,monospace;font-size:10.5px;color:var(--dim);background:var(--bg);padding:2px 7px;border-radius:4px;border:1px solid var(--bd)}
.stat{font-size:11px;color:var(--ok);font-family:Consolas,monospace}
.sumbox{background:#14202b;border-bottom:1px solid var(--bd);padding:10px 16px;font-size:12.6px}
.body{display:grid;grid-template-columns:410px 1fr}
@media(max-width:1120px){.body{grid-template-columns:1fr}}
.shot{background:#000;border-right:1px solid var(--bd);padding:8px;position:relative}
.shot img{width:100%;border-radius:4px;display:block;cursor:zoom-in}
.noshot{color:#4a525e;font-size:12px;text-align:center;padding:40px 0}
.info{padding:13px 16px}
.row{margin-bottom:10px}
.lb{font-size:10.4px;letter-spacing:.6px;color:var(--dim);text-transform:uppercase;margin-bottom:3px;font-weight:600}
.lb.in{color:var(--cy)}.lb.do{color:var(--ok)}.lb.oa{color:var(--acc)}.lb.pit{color:var(--err)}
.tx{font-size:12.8px}
.attr{display:inline-block;margin:2px 3px 2px 0;font-family:Consolas,monospace;font-size:11px;background:var(--bg);padding:1.5px 6px;border-radius:3px;border:1px solid var(--bd);color:var(--warn)}
.attr.new{color:#0f1115;background:var(--ok);border-color:var(--ok);font-weight:600}
.attr.g{color:var(--pur);border-color:#4a3358}
pre{background:var(--bg);border:1px solid var(--bd);border-left:3px solid var(--acc);padding:9px 12px;border-radius:4px;overflow-x:auto;font-size:11.2px;margin:5px 0}
pre code{color:#c8d3e0}
details summary{cursor:pointer;font-size:11.5px;color:var(--dim)}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.95);display:none;z-index:99;flex-direction:column;align-items:center;justify-content:center}
#lb img{max-width:92%;max-height:80%;border-radius:5px}
#lbbar{display:flex;align-items:center;gap:18px;margin-top:13px}
#lbbar button{background:var(--card);border:1px solid var(--bd);color:var(--fg);padding:7px 17px;border-radius:5px;cursor:pointer}
#lbtitle{font-size:13.5px;min-width:330px;text-align:center}
#lbtitle span{color:var(--dim);font-size:11.5px;display:block}
#lbclose{position:absolute;top:18px;right:26px;font-size:27px;color:var(--dim);cursor:pointer}
"""


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _collect_graph(root, items, shots, max_depth):
    """采集 Houdini 节点图数据：每个容器一张图，含节点位置/连线/颜色/标志

    返回 {container_path: {name, path, nodes:[...], edges:[...]}}
    """
    import hou  # type: ignore

    info = {}
    for it in items:
        info[it["path"]] = it

    graphs = {}

    def _node_color(n):
        try:
            c = n.color().rgb()
            return "#%02x%02x%02x" % (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))
        except Exception:
            return "#3d4450"

    def _grab(parent, depth):
        if depth > max_depth + 1:
            return
        try:
            kids = list(parent.children())
        except Exception:
            return
        if not kids:
            return
        nodes = []
        edges = []
        idx_of = {}
        for n in kids:
            idx_of[n.path()] = len(nodes)
            try:
                pos = n.position()
                px, py = float(pos[0]), float(pos[1])
            except Exception:
                px, py = 0.0, 0.0
            it = info.get(n.path())
            tname = n.type().name()
            nk = 0
            try:
                nk = len(n.children())
            except Exception:
                pass
            flags = []
            try:
                if n.isDisplayFlagSet():
                    flags.append("display")
            except Exception:
                pass
            try:
                if n.isRenderFlagSet():
                    flags.append("render")
            except Exception:
                pass
            try:
                if n.isBypassed():
                    flags.append("bypass")
            except Exception:
                pass
            err = ""
            try:
                if n.errors():
                    err = "error"
                elif n.warnings():
                    err = "warn"
            except Exception:
                pass
            # ---- 与线性报告一致的分析信息 ----
            _vex_raw = (it or {}).get("vex") or _get_vex(n)
            # _get_vex 返回 [(标题, 代码), ...]，需拼成纯文本供分析与展示
            _body = ""
            _vex = ""
            try:
                if isinstance(_vex_raw, (list, tuple)):
                    _segs = []
                    for _e in _vex_raw:
                        if isinstance(_e, (list, tuple)) and len(_e) >= 2:
                            _segs.append("// ---- %s ----\n%s" % (_e[0], _e[1]))
                            _body += str(_e[1]) + "\n"
                        else:
                            _segs.append(str(_e))
                            _body += str(_e) + "\n"
                    _vex = "\n\n".join(_segs)
                elif _vex_raw:
                    _vex = str(_vex_raw)
                    _body = _vex
            except Exception:
                _vex = str(_vex_raw)
                _body = _vex
            _st = (it or {}).get("stat") or _geo_stat(n)
            _tmp_it = it or {"node": n, "type": tname, "kind": _kind_of(n),
                             "stat": _st, "nkids": nk}
            try:
                _desc = _desc_of(_tmp_it)
            except Exception:
                _desc = tname + " 节点"
            if _vex:
                try:
                    _rd, _wr = _extract_attrs(_body)
                except Exception:
                    _rd, _wr = "", ""
                try:
                    _pit = _guess_pitfall(_body, n)
                except Exception:
                    _pit = ""
            else:
                _rd, _wr, _pit = "", "", ""
            # 输入源（上游节点 + 端口）
            _srcs = []
            try:
                for _ii, _up in enumerate(n.inputs()):
                    if _up is None:
                        continue
                    _ust = _geo_stat(_up)
                    _srcs.append({
                        "i": _ii,
                        "n": _up.name(),
                        "p": _up.path(),
                        "t": _up.type().name(),
                        "st": _ust,
                    })
            except Exception:
                pass
            # 相对第一输入的属性增减
            _newa, _gonea = [], []
            try:
                if _srcs:
                    _prev = _srcs[0]["st"]
                    _newa, _gonea = _diff_attrs(_st, _prev)
            except Exception:
                pass
            _parms = []
            try:
                for _pm in n.parms():
                    if _pm.name() in ("snippet", "vexsnippet"):
                        continue
                    try:
                        if _pm.isAtDefault():
                            continue
                        _pv = _pm.eval()
                    except Exception:
                        continue
                    if isinstance(_pv, str) and len(_pv) > 90:
                        _pv = _pv[:90] + "..."
                    _parms.append({"n": _pm.name(), "v": str(_pv)})
                    if len(_parms) >= 18:
                        break
            except Exception:
                pass
            nodes.append({
                "desc": _desc,
                "reads": _rd,
                "writes": _wr,
                "pit": _pit,
                "srcs": _srcs,
                "newa": _newa,
                "gonea": _gonea,
                "parms": _parms,
                "n": n.name(),
                "p": n.path(),
                "t": tname,
                "x": px,
                "y": py,
                "c": _node_color(n),
                "k": _kind_of(n),
                "nk": nk,
                "fl": flags,
                "er": err,
                "no": (it or {}).get("no", ""),
                "lv": (it or {}).get("lv", 0),
                "loop": (it or {}).get("in_loop", ""),
                "st": (it or {}).get("stat") or _geo_stat(n),
                "vex": _vex,
                "shot": shots.get(n.path(), ""),
                "inloop": bool((it or {}).get("in_loop")),
            })
            if nk > 0 and _kind_of(n) in ("subnet", "hda") and depth <= max_depth:
                _grab(n, depth + 1)
            elif nk > 0 and tname.startswith("block_"):
                pass
        for n in kids:
            try:
                for i, up in enumerate(n.inputs()):
                    if up is None:
                        continue
                    if up.path() in idx_of and n.path() in idx_of:
                        edges.append({
                            "f": idx_of[up.path()],
                            "t": idx_of[n.path()],
                            "i": i,
                        })
            except Exception:
                pass
        # ---- 1) 重算 for-each 循环分组：只框住 block_begin ~ block_end 之间的节点 ----
        try:
            for n in kids:
                tn = n.type().name()
                if not tn.startswith("block_end"):
                    continue
                body = set()
                stack = [n]
                while stack:
                    c = stack.pop()
                    if c is None or c.path() in body:
                        continue
                    if c.parent() is None or c.parent().path() != parent.path():
                        continue
                    body.add(c.path())
                    if c.type().name().startswith("block_begin"):
                        continue
                    try:
                        for up in c.inputs():
                            if up is not None and up.path() not in body:
                                stack.append(up)
                    except Exception:
                        pass
                # block_begin 的 metadata 伴随节点也纳入框内
                for c in kids:
                    try:
                        if c.type().name().startswith("block_begin") and c.path() in body:
                            for o in c.outputs():
                                if (o is not None and o.parent() is not None
                                        and o.parent().path() == parent.path()
                                        and o.type().name().startswith("block_begin")):
                                    body.add(o.path())
                    except Exception:
                        pass
                lname = n.name()
                for nd in nodes:
                    if nd["p"] in body:
                        nd["loop"] = lname
                        nd["inloop"] = True
            # 未被任何 block_end 收编的节点，清掉线性分析阶段带来的不准确 loop 标记
            _real = set()
            for nd in nodes:
                if nd.get("inloop"):
                    _real.add(nd["p"])
            for nd in nodes:
                if nd["p"] not in _real:
                    nd["loop"] = ""
                    nd["inloop"] = False
            # block_begin / block_end 单独打黄色标识
            for nd in nodes:
                _t = nd.get("t", "")
                nd["blk"] = bool(_t.startswith("block_begin") or _t.startswith("block_end"))
        except Exception:
            pass

        # ---- 2) subnet 的 Input1~Input4 指示节点 ----
        try:
            iis = list(parent.indirectInputs())
        except Exception:
            iis = []
        for k, ii in enumerate(iis):
            try:
                ipos = ii.position()
                ix, iy = float(ipos[0]), float(ipos[1])
            except Exception:
                ix, iy = float(k) * 3.0, 10.0
            fake_path = "%s/__input%d__" % (parent.path(), k + 1)
            idx_of[fake_path] = len(nodes)
            nodes.append({
                "desc": "子网第 %d 个输入端口（对应父级 %s 的 input%d）" % (
                    k + 1, parent.name(), k),
                "reads": [], "writes": [], "pit": [], "srcs": [],
                "newa": [], "gonea": [], "parms": [],
                "n": "Input%d" % (k + 1),
                "p": fake_path,
                "t": "subnet input",
                "x": ix, "y": iy,
                "c": "#2c3a4a",
                "k": "", "nk": 0, "fl": [], "er": "",
                "no": "", "lv": 0, "loop": "", "st": None,
                "vex": "", "shot": "", "inloop": False,
                "blk": False, "isin": True,
            })
            try:
                for conn in ii.outputConnections():
                    dn = conn.outputNode()
                    if dn is not None and dn.path() in idx_of:
                        edges.append({
                            "f": idx_of[fake_path],
                            "t": idx_of[dn.path()],
                            "i": conn.inputIndex(),
                        })
            except Exception:
                pass

        graphs[parent.path()] = {
            "name": parent.name(),
            "path": parent.path(),
            "type": parent.type().name(),
            "nodes": nodes,
            "edges": edges,
        }

    _grab(root, 1)
    return graphs


def _build_html(root_path, items, shots, meta):
    """生成 HTML 报告"""
    n1 = n2 = n3 = 0
    ol = []
    cards = []
    imgs = []
    tits = []
    prev_stat = None

    for it in items:
        lv = it["lv"]
        if lv == 1:
            n1 += 1; n2 = 0; n3 = 0; no = str(n1)
        elif lv == 2:
            n2 += 1; n3 = 0; no = "%d.%d" % (n1, n2)
        else:
            n3 += 1; no = "%d.%d.%d" % (n1, n2, n3)
        it["no"] = no

        kind = it["kind"]
        bdg = ""
        if kind == "hda":
            bdg = '<span class="bdg h">HDA</span>'
        elif kind == "subnet":
            bdg = '<span class="bdg s">subnet</span>'
        if it.get("in_loop"):
            bdg += ('<span class="bdg s" style="background:#3a2b4d;color:#c792ea">'
                    'loop %s</span>' % _esc(it["in_loop"]))

        ol.append('<a class="ol-i lv%d" href="#n%s" data-id="n%s"><span class="n">%s</span>%s%s<span class="nd">%s</span></a>'
                  % (lv, no, no, no, _esc(it["name"]), bdg, _esc(it["type"])))

        st = it["stat"]
        statxt = ("%d 点 / %d 面" % (st["pts"], st["prims"])) if st else "无几何输出"
        # 综合职能
        sumb = ""
        if kind in ("subnet", "hda") and it["nkids"] > 0:
            label = "用户自定义 HDA" if kind == "hda" else "子网络"
            sumb = ('<div class="sumbox"><b>综合职能</b>：这是一个 %s，内部封装了 <b>%d</b> 个节点。'
                    '下方子章节按数据流顺序逐层拆解其内部实现。</div>' % (label, it["nkids"]))
        # 输入源
        ins = []
        try:
            for i, inp in enumerate(it["node"].inputs()):
                if inp is not None:
                    ins.append("input%d = <code>%s</code>" % (i, inp.name()))
        except Exception:
            pass
        intxt = "，".join(ins) if ins else "无上游输入（数据源或容器入口）"
        # 属性变化
        new, gone = _diff_attrs(st, prev_stat)
        oa = ""
        if new:
            oa += '<div><span style="font-size:11px;color:#a3d977">新增：</span>'
            for a in new[:24]:
                oa += '<span class="attr new">%s</span>' % a
            oa += "</div>"
        if gone:
            oa += ('<div style="margin-top:4px"><span style="font-size:11px;color:#ff6b6b">清除：</span>'
                   '<span style="font-size:11.5px;color:#8a95a5;font-family:Consolas">%s%s</span></div>'
                   % (", ".join(gone[:12]), (" … 共%d个" % len(gone)) if len(gone) > 12 else ""))
        if st:
            grp = ""
            for x in st["pt_groups"]:
                grp += '<span class="attr g">%s <sub>ptGrp</sub></span>' % x
            for x in st["pr_groups"]:
                grp += '<span class="attr g">%s <sub>primGrp</sub></span>' % x
            if grp:
                oa += '<div style="margin-top:4px"><span style="font-size:11px;color:#c792ea">组：</span>%s</div>' % grp
            det = '<details><summary>全部属性 (point %d / prim %d / detail %d)</summary><div style="margin-top:5px">' % (
                len(st["pt_attrs"]), len(st["pr_attrs"]), len(st["det_attrs"]))
            for a in st["pt_attrs"]:
                det += '<span class="attr">%s</span>' % a
            det += "</div></details>"
            oa += det
        if not oa:
            oa = '<span style="color:#8a95a5;font-size:12px">属性无变化</span>'
        # VEX
        codeblk = ""
        for tag, code in it["vex"]:
            c = code if len(code) < 2600 else code[:2600] + "\n...(截断)"
            codeblk += '<div class="row"><div class="lb">%s</div><pre><code>%s</code></pre></div>' % (tag, _esc(c))
        # 截图
        img = shots.get(it["path"])
        if img:
            imgs.append(img)
            tits.append("%s %s @%s" % (no, it["name"], it["type"]))
            shotblk = ('<div class="shot"><img src="%s" onclick="openLb(%d)"></div>'
                       % (img, len(imgs) - 1))
        else:
            shotblk = '<div class="shot"><div class="noshot">（无截图）</div></div>'

        cards.append(
            '<div class="card l%d" id="n%s"><div class="hd"><span class="num">%s</span>'
            '<h4>%s</h4><span class="nn">%s</span><span class="np">%s</span>'
            '<span class="np">%s</span><span class="stat">%s</span></div>%s'
            '<div class="body">%s<div class="info">'
            '<div class="row"><div class="lb in">输入源</div><div class="tx">%s</div></div>'
            '<div class="row"><div class="lb do">节点类型 / 处理</div><div class="tx">'
            '类型 <code>%s</code>%s</div></div>'
            '<div class="row"><div class="lb oa">输出属性</div><div class="tx">%s</div></div>'
            '%s</div></div></div>'
            % (lv, no, no, _esc(it["name"]), _esc(it["name"]),
               _esc(it["type"]), _esc(it["path"]), statxt, sumb, shotblk,
               intxt, _esc(it["type"]),
               ("，内部 %d 个节点" % it["nkids"]) if it["nkids"] else "",
               oa, codeblk))
        if st:
            prev_stat = st

    import json as _json
    html = (
        '<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>%s 节点分析报告</title><link rel="stylesheet" href="style.css"></head><body>'
        '<div id="side"><h1>%s</h1><div class="sub">%s<br>%d 个环节 · 三级目录</div>'
        '<a class="backbtn" href="index.html" title="切换到交互式节点图视图">&#9664; 节点图视图</a>'
        '%s</div>'
        '<main><header><h2>%s · 节点管线分析报告</h2><div class="m">%s</div></header>%s</main>'
        '<div id="lb"><span id="lbclose" onclick="closeLb()">&times;</span><img id="lbi">'
        '<div id="lbbar"><button onclick="nav(-1)">&#9664; 上一张</button>'
        '<div id="lbtitle"></div><button onclick="nav(1)">下一张 &#9654;</button></div></div>'
        '<script>var IMGS=%s;var TITS=%s;var ci=0;'
        'function openLb(i){ci=i;render();document.getElementById("lb").style.display="flex";}'
        'function render(){document.getElementById("lbi").src=IMGS[ci];'
        'document.getElementById("lbtitle").innerHTML=TITS[ci]+"<span>"+(ci+1)+" / "+IMGS.length+"　←→ 键切换</span>";}'
        'function nav(d){ci=(ci+d+IMGS.length)%%IMGS.length;render();}'
        'function closeLb(){document.getElementById("lb").style.display="none";}'
        'document.addEventListener("keydown",function(e){var b=document.getElementById("lb");'
        'if(b.style.display!=="flex")return;if(e.key==="ArrowLeft")nav(-1);'
        'else if(e.key==="ArrowRight")nav(1);else if(e.key==="Escape")closeLb();});'
        'var cs=document.querySelectorAll(".card");var ls=document.querySelectorAll(".ol-i");'
        'window.addEventListener("scroll",function(){var p=window.scrollY+130;var cur="";'
        'cs.forEach(function(c){if(c.offsetTop<=p)cur=c.id;});'
        'ls.forEach(function(l){if(l.dataset.id===cur){l.classList.add("on");'
        'l.scrollIntoView({block:"nearest"});}else l.classList.remove("on");});});'
        '</script></body></html>'
        % (_esc(meta["name"]), _esc(meta["name"]), _esc(root_path), len(items),
           "".join(ol), _esc(meta["name"]), _esc(meta["desc"]), "".join(cards),
           _json.dumps(imgs), _json.dumps(tits, ensure_ascii=False))
    )
    return html


# ---------- 写回节点备注 ----------

_NOTE_MARK = "===== 节点说明"
_NOTE_END = "===================== */\n\n"


def _extract_attrs(body):
    """从 VEX 代码里提取读/写属性与组操作

    返回 (reads_str, writes_str)
    """
    import re

    re_w = re.compile(r'(?:^|\s)([ifvsp2putd]?\[?\]?@)([A-Za-z_][A-Za-z0-9_]*)\s*(?:=[^=]|\+=|-=|\*=|/=)')
    re_set = re.compile(r'set(?:point|prim|vertex|detail)attrib\s*\(\s*\d+\s*,\s*["\']([^"\']+)["\']')
    re_grpw = re.compile(r'set(?:point|prim|vertex)group\s*\(\s*\d+\s*,\s*["\']([^"\']+)["\']')
    re_all = re.compile(r'[ifvsp2putd]?\[?\]?@([A-Za-z_][A-Za-z0-9_]*)')
    re_fn = re.compile(r'(?:point|prim|vertex|detail)\s*\(\s*[^,]+,\s*["\']([^"\']+)["\']')
    re_ingrp = re.compile(r'in(?:point|prim|vertex)group\s*\(\s*\d+\s*,\s*["\']([^"\']+)["\']')

    writes = set()
    for m in re_w.finditer(body):
        writes.add(m.group(2))
    for m in re_set.finditer(body):
        writes.add(m.group(1))
    grpw = set()
    for m in re_grpw.finditer(body):
        grpw.add(m.group(1))
    alls = set()
    for m in re_all.finditer(body):
        alls.add(m.group(1))
    for m in re_fn.finditer(body):
        alls.add(m.group(1))
    reads = set()
    for a in alls:
        if a not in writes:
            reads.add(a)
    ingrp = set()
    for m in re_ingrp.finditer(body):
        ingrp.add(m.group(1))
    # 去掉内置只读变量噪音
    for a in ("ptnum", "primnum", "numpt", "numprim", "vtxnum",
              "Frame", "elemnum", "Time", "SimFrame"):
        if a in reads and len(reads) > 1:
            reads.discard(a)

    rd = "、".join(sorted(reads)[:10]) if reads else "无（不读取属性）"
    if ingrp:
        rd += "；读取组: " + "、".join(sorted(ingrp)[:5])
    wr = "、".join(sorted(writes)[:10]) if writes else ""
    if grpw:
        wr += ("；" if wr else "") + "写入组: " + "、".join(sorted(grpw)[:5])
    if not wr:
        wr = "无新增属性"
        if "removeprim" in body or "removepoint" in body:
            wr += "（仅删除元素）"
    return rd, wr


def _guess_pitfall(body, node):
    """从代码特征推断常见坑点"""
    tips = []
    if "detail(" in body:
        tips.append("依赖 detail 级属性，若上游未用 attribpromote 提升会取到 0 导致逻辑静默失效")
    if "removeprim" in body or "removepoint" in body:
        tips.append("含删除操作，判断条件不成立时会静默删光数据且不报错")
    if "nearpoint" in body or "nearpoints" in body:
        tips.append("按空间距离查找，半径参数不当会误判相邻元素")
    if "chf(" in body or "chi(" in body or "chramp(" in body:
        tips.append("引用了节点参数，脱离 HDA 环境时参数引用可能失效并退化为默认值")
    if "@P.y" in body or "P.y" in body:
        tips.append("修改高度分量，需确认是否与压平/还原节点成对使用")
    if not tips:
        tips.append("暂无已知坑点，修改前请确认下游是否依赖其输出属性")
    return "；".join(tips[:3])


def _make_note(func, reads, writes, pit):
    """生成四段式注释块"""
    return ("/* ===== 节点说明 =====\n"
            " 功能介绍：%s\n"
            " 必要的引用属性：%s\n"
            " 输出属性：%s\n"
            " 可能的坑点：%s\n"
            "===================== */\n\n") % (func, reads, writes, pit)


def _desc_of(it):
    """根据节点信息生成功能介绍文字"""
    n = it["node"]
    t = it["type"]
    kind = it["kind"]
    st = it["stat"]
    parts = []
    if kind == "hda":
        parts.append("用户自定义 HDA，内部封装 %d 个节点" % it["nkids"])
    elif kind == "subnet":
        parts.append("子网络，内部封装 %d 个节点" % it["nkids"])
    else:
        parts.append("%s 节点" % t)
    if st:
        parts.append("输出 %d 点 / %d 面" % (st["pts"], st["prims"]))
    ins = []
    try:
        for i, inp in enumerate(n.inputs()):
            if inp is not None:
                ins.append("input%d=%s" % (i, inp.name()))
    except Exception:
        pass
    if ins:
        parts.append("输入 " + "、".join(ins[:3]))
    return "；".join(parts)


def _apply_comments(root, items, unlock_hda=True):
    """把分析结论写回节点

    规则：
      - wrangle 类（有 snippet 参数）：在代码最开头插入四段式注释块，
        绝不修改原始代码；且不设置 comment
      - 其余节点：写入 comment 并开启视口显示
      - 遇到锁定的用户 HDA：按 unlock_hda 决定是否解锁
    """
    import hou  # type: ignore
    import json as _json
    import io as _io
    import os as _os

    stat = {"note_added": 0, "note_skipped": 0, "comment_added": 0,
            "unlocked": [], "rolled_back": [], "locked_skipped": 0}

    # 1) 备份
    backup = {}
    for it in items:
        n = it["node"]
        rec = {"comment": ""}
        try:
            rec["comment"] = n.comment()
        except Exception:
            pass
        p = n.parm("snippet")
        if p is not None:
            try:
                rec["snippet"] = p.eval()
            except Exception:
                pass
        backup[it["path"]] = rec

    # 2) 解锁途经的用户 HDA（只处理真正的用户 HDA，跳过内置节点）
    if unlock_hda:
        seen_lock = set()
        for it in items:
            n = it["node"]
            # 2a. 向上解锁所有祖先 HDA（必须先解外层才能改内层）
            chain = []
            par = n.parent()
            while par is not None:
                chain.append(par)
                if par.path() == root.path():
                    break
                par = par.parent()
            chain.reverse()
            for par in chain:
                if par.path() in seen_lock:
                    continue
                seen_lock.add(par.path())
                try:
                    if _is_user_hda(par) and par.isLockedHDA():
                        par.allowEditingOfContents()
                        stat["unlocked"].append(par.path())
                except Exception:
                    pass
            # 2b. 节点自身若是用户 HDA 也解锁
            try:
                if _is_user_hda(n) and n.isLockedHDA():
                    n.allowEditingOfContents()
                    if n.path() not in stat["unlocked"]:
                        stat["unlocked"].append(n.path())
            except Exception:
                pass

    # 3) 逐节点写入
    for it in items:
        n = it["node"]
        p = n.parm("snippet")
        if p is not None:
            # --- wrangle 类：写代码注释，不写 comment ---
            try:
                orig = p.eval()
            except Exception:
                continue
            if _NOTE_MARK in orig:
                stat["note_skipped"] += 1
                continue
            if not orig.strip():
                stat["note_skipped"] += 1
                continue
            rd, wr = _extract_attrs(orig)
            func = _desc_of(it)
            cm = ""
            try:
                cm = n.comment().strip()
            except Exception:
                pass
            if cm:
                func = cm.split("\n")[0].replace("【", "").replace("】", "·").replace("★", "") + "。" + func
            pit = _guess_pitfall(orig, n)
            note = _make_note(func, rd, wr, pit)
            try:
                p.set(note + orig)
                # 校验：原始代码必须完整保留
                if orig not in p.eval():
                    p.set(orig)
                    stat["rolled_back"].append(it["path"])
                else:
                    stat["note_added"] += 1
                    # wrangle 不留 comment
                    try:
                        n.setComment("")
                        n.setGenericFlag(hou.nodeFlag.DisplayComment, False)
                    except Exception:
                        pass
            except Exception:
                stat["locked_skipped"] += 1
        else:
            # --- 非 wrangle：写 comment ---
            lines = [_desc_of(it)]
            st = it["stat"]
            if st:
                if st["pt_groups"]:
                    lines.append("点组: " + "、".join(st["pt_groups"][:4]))
                if st["pr_groups"]:
                    lines.append("面组: " + "、".join(st["pr_groups"][:4]))
            if it["kind"] in ("subnet", "hda"):
                lines.append("（可进入内部查看逐环节实现）")
            try:
                n.setComment("\n".join(lines))
                n.setGenericFlag(hou.nodeFlag.DisplayComment, True)
                stat["comment_added"] += 1
            except Exception:
                stat["locked_skipped"] += 1

    return stat, backup


# ---------- 入口 ----------

def run(node_path, output_dir=None, camera=None, max_depth=3,
        screenshots=True, shot_width=1280, max_nodes=80,
        add_comments=False, unlock_hda=True, open_browser=True):
    """生成节点管线分析报告

    Args:
        node_path: 要分析的节点路径
        output_dir: 报告输出目录
        camera: 截图相机路径
        max_depth: 递归深度
        screenshots: 是否截图
        shot_width: 截图宽度
        max_nodes: 最大环节数
        add_comments: 是否把分析说明写回节点（需先征得用户同意）
        unlock_hda: 是否允许解锁锁定的用户 HDA
        open_browser: 完成后是否自动用默认浏览器打开报告
    """
    import hou  # type: ignore
    import os as _os
    import io as _io

    root = hou.node(node_path)
    if not root:
        return {"success": False, "error": "节点不存在: %s" % node_path}

    try:
        max_depth = int(max_depth)
        shot_width = int(shot_width)
        max_nodes = int(max_nodes)
    except Exception:
        max_depth, shot_width, max_nodes = 3, 1280, 40

    if not root.children():
        return {"success": False,
                "error": "节点 %s 内部没有子节点，不是容器类节点（subnet/HDA），无需管线分析。"
                         "如需查看单节点属性请用 analyze_geometry_attribs。" % node_path}

    # 输出目录：用户指定则用指定路径，否则默认 $HIP/NodeAnalysis/<节点名>
    if output_dir:
        output_dir = _os.path.expandvars(str(output_dir).strip())
    else:
        hip = hou.getenv("HIP") or _os.path.expanduser("~")
        output_dir = _os.path.join(hip, "NodeAnalysis", root.name())
    if not _os.path.isdir(output_dir):
        _os.makedirs(output_dir)

    # 找一个可创建临时节点的 geo 容器（用于锁定 HDA 截图代理）
    host_geo = root
    p = root
    while p is not None:
        try:
            if p.type().name() == "geo":
                host_geo = p
                break
        except Exception:
            pass
        p = p.parent()

    # 1. 遍历
    items = _walk(root, max_depth, max_nodes)
    if not items:
        return {"success": False, "error": "未能收集到任何可分析的子节点"}

    # 2. 截图
    shots = {}
    if screenshots:
        try:
            extra = _all_graph_nodes(root)
            shots = _shoot(items, output_dir, camera, shot_width, host_geo, extra, root)
        except Exception as e:
            import traceback as _tb
            _tb.print_exc()
            shots = {"__err__": str(e)[:300]}
    dup_shots = shots.pop("__dup__", 0) if isinstance(shots, dict) else 0

    # 2.5 写回节点备注（可选）
    cmt_stat = None
    if add_comments:
        try:
            cmt_stat, cmt_backup = _apply_comments(root, items, unlock_hda)
            bp = _os.path.join(output_dir, "_node_backup.json")
            import json as _json
            _io.open(bp, "w", encoding="utf-8").write(
                _json.dumps(cmt_backup, ensure_ascii=False, indent=1))
            cmt_stat["backup_file"] = bp
        except Exception as e:
            cmt_stat = {"error": str(e)[:200]}

    # 3. 统计
    n_hda = n_sub = 0
    for it in items:
        if it["kind"] == "hda":
            n_hda += 1
        elif it["kind"] == "subnet":
            n_sub += 1
    first = items[0]["stat"]
    last = None
    for it in reversed(items):
        if it["stat"]:
            last = it["stat"]
            break
    flow = ""
    if first and last:
        flow = "%d 点 / %d 面 → %d 点 / %d 面" % (
            first["pts"], first["prims"], last["pts"], last["prims"])
    desc = "%s ｜ %d 个环节（含 %d 个子网、%d 个用户 HDA） ｜ 截图 %d 张 ｜ %s" % (
        root.type().name(), len(items), n_sub, n_hda, len(shots), flow)

    # 4. 生成网页
    html = _build_html(node_path, items, shots,
                       {"name": root.name(), "desc": desc})
    _io.open(_os.path.join(output_dir, "style.css"), "w", encoding="utf-8").write(_CSS)
    # 线性流程报告作为副页
    _io.open(_os.path.join(output_dir, "pipeline.html"), "w", encoding="utf-8").write(html)
    # 主页：还原 Houdini 节点图的交互式视图
    graphs = {}
    try:
        graphs = _collect_graph(root, items, shots, max_depth)
        import importlib.util as _ilu
        _gp = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_graph_ui.py")
        _sp = _ilu.spec_from_file_location("_graph_ui", _gp)
        _gm = _ilu.module_from_spec(_sp)
        _sp.loader.exec_module(_gm)
        ghtml = _gm.build(node_path, items, shots, graphs,
                          {"name": root.name(), "desc": desc})
        _io.open(_os.path.join(output_dir, "index.html"), "w",
                 encoding="utf-8").write(ghtml)
    except Exception as _e:
        import traceback as _tb
        _io.open(_os.path.join(output_dir, "_graph_error.txt"), "w",
                 encoding="utf-8").write(_tb.format_exc())
        _io.open(_os.path.join(output_dir, "index.html"), "w",
                 encoding="utf-8").write(html)

    # 5. 恢复显示标志
    try:
        d = root.displayNode()
        if d:
            d.setDisplayFlag(True)
    except Exception:
        pass

    outline = []
    for it in items:
        outline.append("%s %s (%s)%s" % (
            it.get("no", ""), it["name"], it["type"],
            (("  [%s %d节点]" % (it["kind"], it["nkids"])) if it["kind"] else "")
            + (("  <loop:%s>" % it["in_loop"]) if it.get("in_loop") else "")))

    result = {
        "success": True,
        "report": _os.path.join(output_dir, "index.html"),
        "output_dir": output_dir,
        "node": node_path,
        "node_type": root.type().name(),
        "sections": len(items),
        "subnets": n_sub,
        "user_hdas": n_hda,
        "screenshots": len(shots),
        "duplicate_shots": dup_shots,
        "graph_networks": len(graphs),
        "loop_sections": sum(1 for _i in items if _i.get("in_loop")),
        "data_flow": flow,
        "outline": outline,
        "hint": "报告已生成，用浏览器打开 index.html（交互式节点图：左上截图+左下详情+右侧节点图，分割线可拖拽）。顶栏「☰ 文档版报告」可切到 pipeline.html（三级目录长文档，点击截图放大后可用 ←→ 键翻页对比），该页左上「◀ 节点图视图」可切回。",
    }
    # 6. 自动用默认浏览器打开报告
    if open_browser:
        rp = result["report"]
        opened = False
        try:
            import webbrowser
            url = "file:///" + _os.path.abspath(rp).replace("\\", "/")
            opened = webbrowser.open(url)
        except Exception:
            opened = False
        if not opened:
            try:
                _os.startfile(_os.path.abspath(rp))
                opened = True
            except Exception:
                opened = False
        result["opened_in_browser"] = opened
        if not opened:
            result["hint"] = "报告已生成，但自动打开浏览器失败，请手动打开: " + rp

    if cmt_stat is not None:
        result["comments"] = cmt_stat
        if not cmt_stat.get("error"):
            result["comment_summary"] = (
                "wrangle 代码注释 %d 个（跳过 %d）｜其余节点 comment %d 个｜"
                "解锁 HDA %d 个｜回滚 %d 个｜原始代码零改动"
                % (cmt_stat.get("note_added", 0), cmt_stat.get("note_skipped", 0),
                   cmt_stat.get("comment_added", 0), len(cmt_stat.get("unlocked", [])),
                   len(cmt_stat.get("rolled_back", []))))
    return result
