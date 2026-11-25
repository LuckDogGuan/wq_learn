# 广州服务器爬山算法与历史人机协同研发对话深度洞察

> **文档版本**：v1.0  
> **数据来源**：对本地 253 个 Codex 会话与 202 个 Antigravity 会话全量文本扫描，专项萃取“广州服务器”、“全自动爬山算法”、“hill_climbing_v4.7”、“金字塔乘数与塔缺口补齐”等实战对话语料。  
> **编写目的**：真实还原量化研究员在指挥广州服务器运行全自动爬山时的底层交互意图、参数决策逻辑与高频运维经验。

---

## 1. 历史对话核心关注焦点与人机协同演进

在实际研发会话中，研究员对全自动爬山算法的指挥与介入呈现出高度体系化的**三阶段特征**：
1. **任务下达与种子源筛选阶段**：
   - 重点关注**“最近 30 天未提交或被拒的失败 Alpha”**作为优化种子；
   - 强制绑定**“金字塔缺口（Pyramid Gap）与倍数加成（Multiplier）”**，优先爬取能够拿满 1.3x~2.0x 乘数的赛道（如 GLB/D1/MODEL、GLB/D1/PV）；
   - 强调**“单数据集与字段类型纯度”**，防止跨数据集过度拟合。
2. **过程监控与并发调优阶段**：
   - 面对频繁触发的平台 **429 Too Many Requests** 速率限制，研究员明确要求引入**“全局冷却 5 分钟 + 本地只读对账”**机制，杜绝盲目重发引发封禁；
   - 严格要求每个父批次由 `1 个父 Multi-Simulation × 8 个子模拟` 构成，严格禁止碎片化提交单模拟。
3. **成果验收与合规终检阶段**：
   - 严厉重申**“绝对禁止自动提交”**，算法产出仅作为 Stage 3 候选存入 checkpoint，最终提交权必须保留在研究员手中；
   - 重点审核 **Prod Correlation (PC < 0.70)** 与 **Self Correlation (SC < 0.40)**。

---

## 2. 真实对话实录与研究员指令精选 (Empirical Dialogue Excerpts)

### 2.1 广州服务器后台部署与长周期守护指令
```text
【研究员核心诉求】：
“在广州服务器上后台运行 hill_climbing_v4.7，挂起 nohup 或后台守护任务，保证网络中断后自动恢复重试。定期抓取 checkpoint_v4.7.json 和 log 进行断点续传。”
```
- **底层技术回应**：爬山系统在 `state_store.py` 中采用 SQLite 事务（`source_state_v6.sqlite3`）实现原子状态持久化。每轮迭代自动写入 `*_checkpoint_v4.7.json`，即使服务器重启也能无缝接续当前批次。

### 2.2 429 速率限制与网络中断容错指令
```text
【研究员指令】：
“如果遇到 429 报错或者 connection reset 10054，禁止频繁轮询平台 API。要求休眠 300 秒，进入本地缓存只读模式，对已有 Location 的批次做只读对账。”
```
- **技术落地机理**：算法状态机严格划分 `PENDING_RATE_LIMIT` 与 `RESULTS_UNOBSERVED`。针对未确认结果，先向只读端发起精确 Alpha ID 对账；确认无果后才进入重跑队列，严格避免算力浪费与黑名单风险。

### 2.3 针对不同地区/Universe 的指令差异
在历史对话中，研究员对不同市场的调参指令存在鲜明的分野：
- **GBR 指令**：*“GBR TOP700 必须把单票持仓上限压低，不能被巨头绑架，中性化别用太细的 subindustry，用 MARKET 或 INDUSTRY 保住有效标的数。”*
- **EUR 指令**：*“欧洲市场重点跑 Fundamental 和 Model 字段，用 ts_ir 惩罚异常毛刺，利用非线性对数模量压平 EP yield 的厚尾极端值，中性化必须用 SUBINDUSTRY 切除跨国差异。”*
- **GLB 指令**：*“全球大宇宙必须搭配 SLOW_AND_FAST，必须用 vec_avg 降维向量字段，首选用 min_estimate 打碎生产池相关性。”*

---

## 3. 人机协同指导全自动爬山的高效 Prompt 模板

### 模板 1：爬山种子源筛选与缺口诊断 Prompt
```markdown
# Task: 爬山算法种子源与金字塔缺口定向扫描
1. 读取最近 30 天所有回测记录中 Status 为 FAIL 或 UNSUBMITTED 的 Alpha。
2. 关联当前金字塔倍数（Pyramid Multipliers），重点筛选缺口最大的 Region/Universe（如 GLB/MINVOL1M 或 EUR/TOP2500）。
3. 过滤出基础 Sharpe > 1.20 但因 Margin 偏低（< 5bp）或换手率偏高（> 50%）导致未达标的“潜力种子”，注入爬山 Stage 1 候选池。
```

### 模板 2：爬山过程状态诊断与路由调度 Prompt
```markdown
# Task: 爬山 Stage 演进与变异路由干预
当前 Alpha ID: {ALPHA_ID}, 当前 Stage: {STAGE_NUM}, 当前缺陷: {DEFICIT, 如 margin_bp / turnover / pc}
1. 若当前缺陷为 turnover: 强制分配 `smooth` 路由 (`ts_decay_linear`, `ts_target_tvr_decay`)；
2. 若当前缺陷为 margin: 触发 `MARGIN_REPAIR` 专属 8 候选生成；
3. 若当前缺陷为 pc (生产相关性超标): 强制分配 `cross` 路由，注入正交量价或切换 SLOW_AND_FAST 中性化；
4. 生成新一组 1 父 × 8 子 Multi-Simulation 配置。
```

### 模板 3：爬山终极成果验收与防雷合规 Prompt
```markdown
# Task: Stage 3 爬山通关因子终极质量核验
1. 校验 Stage 3 硬门槛：Sharpe ≥ 1.58, Fitness ≥ 1.00, P2Y Sharpe ≥ 1.60, Margin ≥ 10bp, Turnover 5%~30%；
2. 校验平台风控：CONCENTRATED_WEIGHT 必须 PASS, IS_LADDER_SHARPE 必须 PASS；
3. 校验排他性：SC < 0.40, PC < 0.70；
4. 输出达标报告并生成平台提交卡片（严禁自动调用提交接口，等待研究员手动提交）。
```