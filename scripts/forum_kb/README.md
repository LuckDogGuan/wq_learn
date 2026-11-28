# forum_kb —— WQB 本地知识库（论坛帖 44557921849623 全链路落地）

把 `reference/forum` 的 Top100 论坛帖 + `docs/official_guides` 官方准则 + 管理员原创帖，
整理成 **LLM 原子化 QA → BGE 向量 → LanceDB 混合检索 → FastMCP 双工具** 的本地知识库，
供 Agent 在改因子表达式前查官方红线、排障时查社区经验。

```
reference/forum/top100_2026Q4/*.md ──atomize.py──▶ data/forum_kb/qa/{post_id}.qa.md ─┐
docs/official_guides/*.md ─┐                                                          ├─build_index.py──▶ LanceDB
reference/forum/admin_posts/*.md ─ingest_official.py──▶ data/forum_kb/official/*.jsonl ─┘   (wqb_official_guides
                                                                                             /wqb_forum_experiences)
                                                                                                   │
                                                                                          server.py (FastMCP stdio)
```

## 1. 论坛帖原子化（atomize.py / ingest_forum.py）

用 Antigravity CLI（`agy.exe`，弃用后的 Gemini CLI 继任者；旧 `gemini` npm CLI 报 IneligibleTierError）
的 `gemini-3.8-flash-medium` 把长帖整理成「痛点 Q + 答案 A」原子对。

```powershell
# 单篇
python scripts/forum_kb/atomize.py <md_path> <post_id> --out data/forum_kb/qa/<post_id>.qa.md
# 批量（默认 reference/forum/top100_2026Q4，可续跑、限并发、失败重试）
python scripts/forum_kb/ingest_forum.py --workers 6 --retries 1
```

- 输出格式对齐检索端：`posts/{id} 标题/作者/点赞` 头 + 成对 `Q:`/`A:`（BM25 词法 + 向量双通道）。
- **长帖切段**：Windows 命令行上限 32,767 字符，超过 `MAX_INPUT_CHARS=18_000` 的帖子按段落切段分别原子化，
  再按 Q 文本去重合并（上限 30 对/篇）。早期整段直传导致 15 篇长帖 `WinError 206`，切段后全部补齐。
- 已完成：**265 篇 QA**（Top100 全量 264 + 原帖 44557921849623），`data/forum_kb/ingest_state.json` 记录 done/failed。

## 2. 官方层切块（ingest_official.py）

```powershell
python scripts/forum_kb/ingest_official.py   # → data/forum_kb/official/chunks.jsonl
```

- `docs/official_guides/*.md`：代码保护型切块（`##/###` 处切、代码块内严禁切）。
- `reference/forum/admin_posts/**/*.md`：单帖最多取 10 块、跳过 >300KB 的合辑，避免稀释官方层精度。
- 当前 **1,928 块**（官方准则 92 + 管理员帖 1,836）。

## 3. 建库（build_index.py）

```powershell
python scripts/forum_kb/build_index.py               # 双表重建 + 混合检索自检
python scripts/forum_kb/build_index.py --only forum  # 只重建论坛经验表
```

- 嵌入：`BAAI/bge-small-zh-v1.5`（512 维，CPU；1,928 块约 100s）。
- 表：`wqb_official_guides` / `wqb_forum_experiences`（字段 doc_id/post_id/kind/title/source/text/vector）。
- 落盘：`data/forum_kb/lancedb_data/`（已 gitignore，不入库）。

## 4. MCP 服务（server.py）

```powershell
python scripts/forum_kb/verify_mcp.py     # stdio 端到端验收（握手 + 两工具 + 全文反查）
```

两个工具（对齐原帖 `server.py`）：

| 工具 | 定位 | 机制 |
| --- | --- | --- |
| `search_wqb_official_guidelines(query, top_k=15)` | 最高优先级：官方红线/参数准则 | 先按 `kind='official_doc'` 检索官方准则，再补管理员帖；官方块始终排在前面；返回注入当日日期 |
| `search_wqb_forum_experience(query, top_k=10)` | 次高优先级：社区经验 | 候选池 `max(top_k*3,30)` 按帖子 ID 去重 → 前 7 篇核心命中 + 其余随机采样 → 按 ID 回读 `reference/forum` 完整原文（6000 字符上限） |

挂载（`antigravity.json` / `claude_desktop_config.json`）：

```json
{"mcpServers": {"wqb-knowledge-base": {
  "command": "python",
  "args": ["C:/Wq/WorldQuant Brain/scripts/forum_kb/server.py"],
  "env": {"PYTHONUNBUFFERED": "1"}}}}
```

## 5. 三个实证坑（都已在代码里绕开）

1. **LanceDB 0.41 API**：`db.table_names()` → `db.list_tables()`；hybrid 检索必须
   `table.search(query_type="hybrid").text(q).vector(qv)`（勿传位置参数）；FTS 用
   `create_index("text", config=FTS(...))`，`create_fts_index` 已弃用。
2. **中文 BM25 零命中**：LanceDB 默认 `simple` 分词器把整句中文当一个 token，中文查询 FTS 直接 0 结果。
   改 `FTS(base_tokenizer="ngram", ngram_min_length=2, ngram_max_length=3)` 后中文可召回；`jieba`/`ngram`
   传 `tokenizer_name=` 会报 `Invalid tokenizer name`，必须走 `FTS(base_tokenizer=...)`。
3. **Windows MCP 懒加载死锁（本机实测）**：进入 anyio 事件循环后，工具线程/预热线程再 `import numpy/scipy/torch`
   会永久卡在扩展 DLL 加载（faulthandler 栈停在 `importlib create_module`，>300s 无返回）。
   Windows 上因此在**进入事件循环前**预导入 `numpy/scipy.sklearn/torch/sentence-transformers/lancedb`
   （冷启动 ≈13s），模型权重与建表仍保持懒加载；Linux/macOS 可 `WQB_KB_PRELOAD=0` 恢复纯懒加载（原帖环境即如此）。

## 6. 测试

```powershell
python -m pytest scripts/forum_kb/tests -q    # 15 passed：切块/QA 校验/批量计划/MCP 装配/AST 懒加载红线
```
