# 升级指南

本仓库基于开源项目 [Kazama-Suichiku/Houdini-Agent](https://github.com/Kazama-Suichiku/Houdini-Agent) 并包含内部定制修改。

**仓库结构说明：**
- `github-upstream` 分支：镜像 GitHub 最新代码，不含任何内部修改
- `master` 分支：在 `github-upstream` 基础上叠加内部定制提交

每次升级 = 把 GitHub 的新代码拉进来，再把内部定制提交重新应用上去。

---

## 每次升级步骤

### 第 1 步：确保工作区干净

```bash
git status
```

输出应为 `nothing to commit, working tree clean`。如果有未提交的改动，先 stash 或 commit，再继续。

---

### 第 2 步：备份当前 master

```bash
git branch master-backup-$(date +%Y%m%d) master
```

> 这会创建一个形如 `master-backup-20260420` 的备份分支，出问题随时可以恢复。

---

### 第 3 步：拉取 GitHub 最新代码

```bash
git fetch upstream
```

---

### 第 4 步：更新 github-upstream 分支

```bash
git checkout github-upstream
git reset --hard upstream/main
git push origin github-upstream
```

---

### 第 5 步：将定制提交 rebase 到最新版本

```bash
git checkout master
git rebase github-upstream
```

**如果出现冲突**，不要强行解决，执行：

```bash
git rebase --abort
```

然后联系仓库维护负责人处理。

---

### 第 6 步：推送更新后的 master

```bash
git push origin master --force-with-lease
```

> `--force-with-lease` 比 `--force` 更安全，如果有人在你之后推送了新提交，这条命令会主动报错而不是覆盖。

---

### 完成验证

```bash
git log --oneline -5
```

正常结果应为：内部定制提交在最顶部，其下方跟着 GitHub 的最新提交。

---

## 同步到 Kaitian 仓库

HoudiniAgent 以 subtree 的方式嵌入到 Kaitian 仓库，prefix 为：

```
HouTools/KaiTian/scripts/python/kt_houdini_agent
```

完成上面对 HoudiniAgent 的升级后，切换到 **Kaitian 仓库**执行以下步骤。

---

### 第 1 步：确认 houdini-agent remote 存在

```bash
git remote get-url houdini-agent
```

如果报错 `No such remote`，先添加：

```bash
git remote add houdini-agent ssh://git@git-internal.nie.netease.com:32200/Gestalt/Tools/KaitianParts/SubParts/HoudiniAgent.git
```

---

### 第 2 步：切出开发分支

从 Kaitian 仓库的当前主干分支切出一个开发分支（分支命名规范参考 Kaitian 项目约定），在该分支上进行后续操作。

---

### 第 3 步：更新 subtree

```bash
git subtree pull --prefix=HouTools/KaiTian/scripts/python/kt_houdini_agent houdini-agent master --squash
```

**如果出现冲突**，不要强行解决，执行：

```bash
git merge --abort
```

然后联系仓库维护负责人处理。

---

## 出问题怎么恢复

如果升级过程出错，使用第 2 步创建的备份分支恢复：

```bash
git checkout master
git reset --hard master-backup-20260420   # 替换为实际备份分支名
git push origin master --force-with-lease
```

---

## 快速参考（熟练后使用）

**HoudiniAgent 仓库：**

```bash
git status
git branch master-backup-$(date +%Y%m%d) master
git fetch upstream
git checkout github-upstream
git reset --hard upstream/main
git push origin github-upstream
git checkout master
git rebase github-upstream
git push origin master --force-with-lease
```

**Kaitian 仓库（切到开发分支后执行）：**

```bash
git subtree pull --prefix=HouTools/KaiTian/scripts/python/kt_houdini_agent houdini-agent master --squash
```

---

## 2026-09-19：实际运行目录与新版界面启动修复

实际使用的副本是 `K:\Rocket\rocketbox_git\PanguToolKit\Kaitian\HouTools\KaiTian`。
`K:\Rocket\PanguToolKit_Git\HouTools\KaiTian` 是另一份检出；只修改后者不会更新前者。
本次已将升级后的代码和入口修复同步到两份检出，未同步用户配置、cache 或 lib。
合入源代码基线为本地 `K:\Houdini-Agent` 的 `39ec178`（VERSION=2.0.15）。

### 启动策略

- 菜单明确调用 `launcher.show_tool(ui="external")`：Houdini 中启动 Bridge，
  用独立 Python/PySide6 进程打开新版 QML 界面，与独立仓库的 standalone 界面一致。
- Houdini 20.5 的 Qt 5.15.2 实际无法加载新版 QML 的无版本 import，
  即使 Python 模块能 import，也不代表 QML 能显示。本机已实测 Qt6 的 QML root 创建成功。
- 新入口不再使用通用名字 `import main`，也不把 QML 启动失败静默降级为旧界面。
  旧界面仅在显式调用 `launcher.show_tool(ui="legacy")` 时使用。
- `bootstrap.py` 统一菜单与 Start MCP 的代码来源，并处理此前由独立仓库 Bridge
  预先导入的 `houdini_agent` / `shared` 模块。若另一份 UI 已经加载，则要求重启
  Houdini，不冒险卸载仍在使用的 Qt 对象。
- `external_launcher.py` 清除子进程中的 Houdini Python/Qt 环境污染，
  自动查找带 PySide6、numpy 的独立 Python，requests 可由本包 lib 提供。
  可通过 `HAGENT_EXTERNAL_PYTHON` 显式指定独立 `python.exe`。
- `external_runner.py` 优先使用独立 Python 的 site-packages，再以本包 lib 作为后备，
  避免把面向 Houdini Python 3.11 的二进制依赖强行覆盖到 Python 3.12。
- 从 KaiTian 启动的窗口不再自动改写 Houdini 用户目录里的 Agent package JSON，
  而是直接连接启动它的 Houdini Bridge。启动日志在
  `%LOCALAPPDATA%\HoudiniAgent\kaitian-ui.log`。

### 依赖随包分发（`lib/` + `lib_deps.py`），不再建 `.venv`

早期方案是首次运行时在包目录里建 `.venv` 并 `pip install`（本机实测要下 ~250MB、
还因为包路径本身接近 260 字符而必须用临时盘符兜底）。现在改成**依赖全部随包放在
`lib/`**，用户机器只要有一个 64 位 Python 3.10+ 就行 —— 不装任何库、不联网、不跑 pip。

**目录约定**

```
lib/                   版本无关的依赖，所有 Python 版本共用
                       PySide6-Essentials 6.11.1 / shiboken6 6.11.1 是 cp310-abi3
                       轮子，一份就管 3.10~3.14；requests 2.32.5
lib/py3.12/            按小版本编译的依赖（numpy 2.5.1）
                       只有 3.12 解释器看得见，免得 3.11 去加载 cp312 的 numpy
tools/requirements-lib.txt
                       依赖清单 —— "lib/ 里该有哪些包"的唯一来源，
                       两份消费者都读它：tools/fetch_lib.py（装包）和
                       lib_deps.py（运行时自检）
tools/fetch_lib.py     维护者用：按上面的清单把依赖装进 lib/
```

- 路径解析/自检集中在 `lib_deps.py`：`apply()` 把 `lib/pyX.Y` 和 `lib` 挂到
  `sys.path` 最前（版本目录在前），`diagnose()` 给人看的自检报告，
  `require()` 缺依赖时抛带报告的错误。
- 依赖清单只有一份，行格式 `[ver] <pip 需求>  # import: <导入名>[, optional]`：
  `fetch_lib.py` 取前半段喂 pip，`lib_deps.required_modules()/optional_modules()`
  取 `import:` 那半段做运行时自检。**以后加包只改清单，自检自动跟上**
  （早先 `lib_deps.py` 里另有一份硬编码的模块名，已经去掉）。
- 调用点：`bootstrap.prepare_runtime()`（Houdini 内侧，额外挂 `lib/win32` 等
  pywin32 老布局 + `add_dll_directory`）、`external_runner.py`（外部 Qt6 进程）、
  `launcher.launch_external_agent()`（不带 Houdini 时在本进程开窗口）。
- 只需 PySide6-Essentials：界面用到的是 QtCore/QtGui/QtWidgets/QtQuickWidgets
  和 QtQuick(.Controls/.Layouts/.Dialogs)，Addons 那 ~400MB 不装。
- `external_launcher.find_python()` 的探针改成：候选解释器必须**不能** import `hou`、
  必须是 64 位 3.10+、能 import `lib/` 里的 `PySide6.QtQuickWidgets` 和 `requests`
  （不再要求 numpy），优先 `pythonw.exe`。候选顺序 `HAGENT_EXTERNAL_PYTHON` →
  当前解释器 → PATH → 注册表 → `py -3`。
- `launcher.bat` 只负责找 `python` / `py -3`（或 `HAGENT_PYTHON`）来跑 `launcher.py`；
  如果这个解释器不达标，`launcher.py` 自己用同一个探针换一个能跑的重启一次
  （`HAGENT_ENV_REEXEC=1` 防重入）。
- numpy 是唯一按小版本编译的依赖，缺了不影响界面启动（长期记忆/向量检索会不可用），
  `external_runner.py` 会打印一行提示。给别的 Python 版本补齐：
  `python tools/fetch_lib.py --for 3.11 3.13`（用 pip 的 `--python-version/--only-binary`
  直接下对应轮子，本机不需要装那个版本）。
- lib 内最长路径约 249 字符，`LongPathsEnabled=0` 也能正常装卸，不再需要 subst 兜底。

**实测**：系统 Python 3.12、以及 Houdini 自带的裸 Python 3.11（本机只装了 numpy，
没有 PySide6/requests）都能直接跑起新版界面，QML `Status.Ready`、0 错误；
`import PySide6` 解析到 `lib\PySide6`，不会用到系统里那份。

### 本次验证

- Houdini 20.5 hython 中先加载独立仓库模块，再启动 KaiTian MCP：
  server 与 shared 都切回本 package，重复 setup 不会重建服务模块。
- FastMCP 实际注册 20 项工具（其中 flipbook 默认禁用），所有工具签名无裸 `*args` / `**kwargs`。
- HTTP initialize / list_tools / health 调用成功。
- 创建无连接的节点网络能返回成功字典；保留两个 KaiTian Biome skills。
- 菜单显式 external 路由优先于已有 `HAGENT_UI=legacy` 设置。
- 从 hython 的真实 Qt5 环境启动隔离 Qt6 子进程：新版 ExternalWindow 离屏创建成功，
  QML root 就绪；聊天后端在禁用凭据读取的测试中完成构造。此测试未调用 LLM。
- 实测子进程参数、环境清理和重复点击防重复启动；没有关闭用户当前 Houdini。
  更新后需保存场景并重启 Houdini，让菜单定义及旧 Python 模块缓存一起刷新。

## KaiTian 定制补丁清单（2026-09-19 合入 2.0.15 时整理）

`kt_houdini_agent` 是「上游代码 + KaiTian 定制补丁」的产物。上游升级时，
整包替换之后必须把这些补丁重新贴回去，否则会丢功能。

### 合入记录

- 2026-09-19：上游 `1.5.5` → `2.0.15`。KaiTian 菜单默认启动独立 Qt6 QML 窗口，
  显式调用 `launcher.show_tool(ui="legacy")` 可回退旧界面。
- 做法：用上游 2.0.15 的 `houdini_agent/`、`houdini_agent_backup/` 覆盖，
  根目录同步 `launcher.py` / `VERSION` / `.gitignore` / `README.md` / `README_CN.md`；
  `lib/`（本地依赖库）、`Doc/`、`config/`、`rules/`、`plugins/`、`shared/`、
  `trainData/`、`openspec/` 保持不动（与上游内容一致或为 KaiTian 专有数据）。

### 必须重贴的补丁

| # | 文件 | 内容 |
|---|------|------|
| 1 | `houdini_agent/skills/build_biome_algorithm.py` | KaiTian 专有 skill（植被包算法），上游没有，直接保留/复制 |
| 2 | `houdini_agent/skills/create_biome_package.py` | KaiTian 专有 skill（植被包创建），上游没有 |
| 3 | `Doc/pcg_package/`（10 个文件） | PCG / Biome 知识库文档 |
| 4 | `rules/pcg_package_concepts.md` | PCG 概念规则 |
| 5 | `houdini_agent/utils/doc_rag.py` | 知识库支持 `.md`（新增 `_parse_md_sections`，含代码块感知）+ `_KB_HINTS` 增补 PCG/Biome/植被 关键词 |
| 6 | `houdini_agent/utils/mcp/server.py` | ①`tool_wrapper` 加 `functools.wraps`；②修复 `create_node_network` 尾部逻辑被错误缩进到外层作用域（旧版会导致该工具返回 `None`，且注册时抛 NameError） |
| 7 | `launcher.py`、`launcher.bat`、`bootstrap.py`、`external_launcher.py`、`external_runner.py`、`lib_deps.py`、`tools/requirements-lib.txt`、`tools/fetch_lib.py` | 统一代码和依赖来源；独立 Qt6 UI 启动、环境隔离、Bridge 连接；依赖随包放在 `lib/`（清单单一来源 + 版本目录约定 + 运行时自检） |
| 8 | `houdini_agent/ui/context_mixin.py` | Token 用量显示支持 M（百万）级格式化（`_update_context_stats`） |
| 9 | `houdini_agent/ui/header.py` | 旧 QtWidgets UI 的 CodeMaker 支持：Provider 下拉项、🔑 一键登录按钮、`_CodemakerLoginThread`、CodeMaker 模型表与 1M 上下文/特性 |

> 说明：CodeMaker 的客户端能力（`utils/codemaker_auth.py`、Provider 注册、
> 默认模型等）上游 2.0.x 已内置且更强（token 过期自动静默刷新），直接使用上游版本即可，
> 不需要再自己维护。默认的 QML UI 自带 CodeMaker 入口与登录流程，
> 第 9 项只服务于显式 `ui="legacy"` 这条回退路径。

### 不需要改动的部分

- KaiTian 菜单入口 `MainMenuCommon.xml` 已改为显式调用 `launcher.show_tool(ui="external")`。
- MCP 启动脚本 `scripts/python/start_mcp_server.py` 依赖的 `utils/mcp` 公共 API
  （`ensure_mcp_running` / `stop_mcp_server` / `get_mcp_status`）上游保持兼容。

### 合入后建议验证

```python
# 在 Houdini 20.5 中
from kt_houdini_agent import launcher
launcher.show_tool(ui="external")
```

- MCP：`start_mcp_server.start_in_houdini()` 应成功启动；`create_node_network` 必须返回 dict（不是 None）。
- 知识库：`Doc/pcg_package/*.md` 要能被索引（看 `[DocIndex]` 日志里的 `md=` 计数）。
- skills：`list_skills()` 结果应包含 `create_biome_package` 与 `build_biome_algorithm`。
