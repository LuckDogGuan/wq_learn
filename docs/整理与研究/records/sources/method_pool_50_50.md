# D1 5:5 方法与模板池（Gold 84 算子 + Decision #3 严守版）

> [!CAUTION]
> **两大不可违背硬红线（`wq_research_v2/expr_validator.py` 强制拦截）**：
> 1. **D1-Only 硬锁**：全池模板仅用于 `settings.delay == 1 (D1)`，严禁用于 D0。
> 2. **Decision #3 算子禁令（100% 强制执行）**：
>    - **`add (+)`、`multiply (*)`、`trade_when` 维持永久禁用！**
>    - **严禁生成 `rank(x) + rank(y)`、`-1 * expr`、`x * y`、`1 + x`！**
>    - 取反统一使用 Gold 84 算子 **`reverse(expr)`**（或一元负号 `-expr`）；
>    - 双字段组合统一采用**表达式级 `min(rank(expr_A), rank(expr_B))`**、**`reverse(min(rank(expr_A), rank(expr_B)))`**（及逻辑证成时的 **`max(rank(expr_A), rank(expr_B))`**），每个分支均为完整单字段表达式 `operators(field)`——严格对齐用户核心范式：
>      ```fastexpr
>      reverse(min(rank(ts_delta(ts_backfill(vec_avg(snt26_top50pctranking),500),55)), rank(ts_decay_linear(ts_backfill(mad_underweight_rating_score,5),378))))
>      ```
> 3. **Gold 84 实测权限红线（2026-11-25 `get_operators` 实核）**：
>    - **确认无权限（严禁出现）**：`ts_median`、`left_tail`、`right_tail`、`generalized_rank`、`hump_decay`、`ts_decay_exp_window`。
>    - **强制签名规范**：`hump(x, hump=0.01)` 必须关键字传参；`ts_step(1)` 固定参数 `1`；`ts_target_tvr_decay(x, lambda_min=0, lambda_max=1, target_tvr=0.1)` 严禁 `lambda_max > 1`；API 中性化必须传 `REVERSION_AND_MOMENTUM`（禁 `RAM`）；**`ts_decay_linear(rank(x), d)` 默认 `dense=false` 会把缺失值当 `0` 拉偏 `[0,1]` 排名**（`WL13229` `43567319117079` 警示），必须要么先 `ts_decay_linear` 再 `rank`，要么显式传入 `dense=true`！

---

## 1. 严格 5:5 知识源治理与归属纠偏台账

每批 8 条实验队列强制打标 `source_side ∈ {ADMIN_ORIGINAL, TOP100_2026Q4}`，默认严格按 **`4 Admin : 4 Top100`** 分配，周度偏差不超过 `±10%`。同一原帖的镜像、Skill 转述与本地改编合并计数为 `1`。

### 1.1 50% 管理员原创侧（`ADMIN_ORIGINAL`，共 254 篇纯原创）
- **核实总量**：**`WL13229`（192 篇）+ `KH94146`（62 篇）= `254` 篇**（严禁把 `1,935` 篇 L2 关联帖或 `408` 篇回复帖中的普通社区用户发言算作管理员原创）。
- **本池收录核心原帖映射**：
  - `WL13229` `23906082201239`（L373）：提出 **`min(rank(A), rank(B))`** 替代同量级乘法，奠定 Decision #3 下双分支共振正源。
  - `WL13229` `43567319117079`（2026-11）：*USA and GLB D1: 15–30% Turnover*——`ts_decay_linear(rank(x), d)` `dense=false` 拉偏警告、交易频率 vs 收益兑现周期分离、4 类数据陷阱（财年滚动 period roll、时间戳非方向、buzz 非看多、缺新闻 vs 0 新闻）。
  - `WL13229` `43589077012759`（2026-11）：*如何提高 Value Factor*——禁止插噪声降 PC、子池 Sharpe 保留 `≥70%`。
  - `WL13229` `29085671898775` & Machine Alpha 1–13：`profit_to_size`（`25066216209687`）、`net_sentiment`（`25066287753367`）、`term_structure`（`32092606398999`）、`dupont_difference`（`32198029389207`）、`group_residual`（`25329078901911`）、`group_beta`（`25526497127959`）。
  - `KH94146` `26120715229463` / `27928747887383`：单数据集 ATOM 构建技巧与 Human Alpha 经济逻辑。

### 1.2 50% 实证 `2026Q4` Top 100 顾问侧（`TOP100_2026Q4`，15 位核实入榜领袖）
> **准入与归属纠偏记录（必留痕）**：
> - **剔除 4 位非 `2026Q4` 前 100 顾问**：原 `wq-top-advisors-skill` 10 人中仅 6 人入榜；未入榜的 **`ZH78994`、`AY17279`、`FX25214`、`MZ45384`** 一律清出 50% 配额。
> - **2 处错误署名纠偏**：① 帖 `38980270292631` 实为未入榜作者 `SD17531`，严禁归属 `LW67640`；② `YW82626` 本地目录混有 `KK82709` 与官方帖，所有引用须逐帖核对原作者。
> - **人数口径说明**：核实纳入全部 **15 位** `2026Q4` 前百实证领袖（原 `04_分方向优化与模板.md` 标题写作 14 位，表内实录 15 位，全部经 `reference/benchmarks/TopUser_2026Q4.txt` 验真）：

| 2026Q4 排名与 ID | 核心可复用 D1 技法（均已适配 Gold 84 + Decision #3） | 原帖/资料证据 | 主要落地环节 |
| --- | --- | --- | --- |
| **`ES81271` #4** | 单数据集 ATOM 轮询 + 1–2 字段 + AST/白名单前置校验 + 遇限即停 | `42184733027991` (L2) | 引擎校验与队列调度 |
| **`JL71699` #9** | 稳定性校验；`if_else(group_count(x, market) > N, x, 0)` 门控解权重集中（以 `if_else` 替代禁用 `trade_when`） | `28328131324823` | Stage-2/3 权重急救 |
| **`JR23144` #12** | **同向极值对齐**（外 `min`/`ts_min` 配 `vec_min`，外 `max`/`ts_max` 配 `vec_max`）；1 阶厂字型（`≥200` 天）剪枝；候选两两 SC 矩阵 | `38561233060631` / `33948316726807` | Stage-0/2 & SC 防互撞 |
| **`LD22811` #13** | 选低拥挤集 → 仅用 `rank`/`ts_rank`/`ts_delta`/`log` 跑 0 阶基线 + 一句话经济直觉 | `40929650605207` (L2) | Stage-0 探针 |
| **`JX79797` #15** | 三阶段 Robust 优化；每父式限 30 变体 + 5 算子族熵守卫；`ts_target_tvr_decay` `lambda_max ≤ 1` 红线 | `37388646548119` / `39699176860439` | Stage-2/3 降 TVR & Robust |
| **`ZS59763` #32** | ATLAS L1→L6（禁前置 `rank`）；初筛 `decay=0` + 单 Neut；`Sh < -1.2` 自动 `reverse(...)` 翻号；提交前 `[0,1,3,5,10,20]` 断崖测 + 9 Neut 扫频；`0.68` SC 线；`bucket(rank)` 降 PC | 王哥 Skill 全集（225 文件 SHA256 核验） | 全流程主干纪律 |
| **`YW82626` #35** | 低换手（`<10%`）+ 低 op 优先；用 `ts_std_dev(returns, 20)` 波动率状态切分动量/反转（`if_else` 实现） | `33601363405591` | Stage-2 状态门控 |
| **`QP72475` #39** | 价量/预期背离短期反转骨架 `reverse(ts_corr(rank(f1), rank(f2), 10))`；追求低 PC + 高 Fitness | `33683334474647` | Stage-0/2 相关性骨架 |
| **`RM49262` #45** | 低拥挤情绪/事件集用极简 `ts_covariance(f1, f2, d)` 拿低 PC、低 op 一阶 Alpha | `35294898626711` (L2) | Stage-0/2 低 op 协方差 |
| **`SZ83096` #47** | **五步 D1 晋级链**：**2Y ≥ 1.58 先行** → 嵌套分组救 Sub → 平滑微调 → 穷尽换池 → **`signed_power(x, p)` 保序降 PC** | `42509573118999` (L2) | Stage-2/3/4 诊断急救 |
| **`ZH87224` #51** | 提交前语义等价算子消融，拆冗余 `ts_backfill`/`winsorize`/`abs`，压低 `OpCount < 6` | `41105918774807` (L2) | Stage-3 末期化简 |
| **`SM63503` #57** | **内外算子目标对齐**（极值配极值、稳态配均值、变化配差分），0 新增 op 提 Sharpe | `40035350729495` | Stage-2 算子对齐 |
| **`SJ65808` #78** | **`tail` 必先套 `[0,1]` 排名**：`tail(rank(x), lower=0.2, upper=0.8, newval=0)`（注：Gold 84 无 `left_tail`/`right_tail`/`generalized_rank`，改用 `tail` 或 `if_else` 等价实现） | `36915505477271` (L2) | Stage-2/3 去中间噪声 |
| **`LW67640` #79** | 5 年以上多周期经济逻辑；负 Sharpe 历史库 `reverse` 再挖掘；二阶差分须配外层行业结构 `group_rank` | `35926078666263` | 选题与二阶结构 |
| **`JX14975` #100** | **伪 VECTOR 识别**（单值只测 `vec_avg` 省 80% 额度）；`dateCoverage ≥ 5yr` 准入闸门 | `36514324978583` / `37581194344215` | Stage-0 前置闸门 |

---

## 2. 算子计数口径说明（Genius Tiebreaker & PP 8-op）

- **排除计数（免费不计 op）**：`ts_backfill`、`group_backfill`（按 `7GNvo8y` 官方确认，不计入 PP 8 算子上限与常规精简负担；但仍遵循防陈旧窗口 `≤ 252` 原则，除超稀疏事件字段实证需要外禁止 `1200` 5 年回填）。
- **常规目标**：**计费独立算子数（`Distinct Counted Ops`）`< 6`**，总计费算子调用数（`Total Counted Calls`）尽量 `≤ 6`（PP 支线硬顶 `≤ 8`）。
- **矢量输入预处理记号**：下文 `{X}` 代表已就绪的 `MATRIX` 表达式——若原始字段为 `MATRIX` 则 `{X} = field`；若为 `VECTOR` 则 `{X} = vec_avg(field)`（或按同向对齐选 `vec_min`/`vec_max`/`vec_sum`/`vec_count`，增加 `+1` 计费算子）。

---

## 3. Stage-0 快速探针模板组（严格 `4 Admin : 4 Top100`，用于 24–40 样本初筛）

> **执行纪律（`ZS59763 #32` / `LD22811 #13`）**：固定 `delay=1`、`decay=0`、单一中性化（常规 `INDUSTRY` 或 `SUBINDUSTRY`，ASI 必配 `maxTrade=ON`）；每批 8 条严格对应 4 条 Admin + 4 条 Top100；遇厂字型（`<8` 有效年或 `≥200–250` 天平直）立即 `FAST_DEMOTED`；遇 `IS Sharpe < -1.2` 单立 1 条 `reverse(...)` 翻号对照。

| 编号 | `source_side` & 精确出处 | 模板名 | D1 FASTEXPR 骨架（100% Gold 84 + 无 `+`/`*`/`trade_when`） | 计费算子数（Distinct / Total，不含 `ts_backfill`） | 适用字段与经济直觉 |
| :---: | --- | --- | --- | :---: | --- |
| **S0-A1** | `ADMIN_ORIGINAL`<br>`WL13229` 基础截面骨架 | 截面基准排名 | `rank(ts_backfill({X}, {bf}))` | `1 / 1` | 现成比率/模型概率/得分（无须除规模），测纯横截面排序信号（密集 MATRIX 可省 `ts_backfill`） |
| **S0-A2** | `ADMIN_ORIGINAL`<br>`WL13229` `25066216209687` | 规模标准化比率 (`profit_to_size` 单集版) | `ts_rank(if_else({SIZE} > 0, divide({NUM}, {SIZE}), NaN), {d})` | `4 / 4` (`ts_rank, if_else, >, divide`) | 财务金额/盈利/负债类字段（如 `CHN/other496`、`GLB/fundamental23`、`DEU/fundamental6`），`d=66` 或 `126` |
| **S0-A3** | `ADMIN_ORIGINAL`<br>`WL13229` `25066287753367` | 净情绪/差值时序位置 (`net_sentiment`) | `ts_rank(subtract(ts_backfill({POS}, {bf}), ts_backfill({NEG}, {bf})), {d})` | `2 / 2` (`ts_rank, subtract`) | 同数据集正负情绪或双端指标对（如 `ASI/ai_news_scores`、`GBR/other696`、`ASI/mmp_nlp_sentiment`），`d=22` 或 `66` |
| **S0-A4** | `ADMIN_ORIGINAL`<br>`WL13229` `25329078901911` / `KH94146` `26120715229463` | 行业内去极值排名 | `group_rank(winsorize(ts_backfill({X}, {bf}), std=4), industry)` | `2 / 2` (`group_rank, winsorize`) | 跨行业量纲/均值差异大的基本面、分析师预测意外或模型分，剥离行业共性 |
| **S0-T1** | `TOP100_2026Q4`<br>`LD22811 #13` (`40929650605207`) | 零阶自身历史位置 | `ts_rank(ts_backfill({X}, {bf}), {d})` | `1 / 1` (`ts_rank`) | 任何连续时序字段（`d ∈ {20, 63, 126}`），检验个股相对自身历史所处高位/低位 |
| **S0-T2** | `TOP100_2026Q4`<br>`LD22811 #13` & `ZS59763 #32` | 边际变动截面排名 | `rank(ts_delta(ts_backfill({X}, {bf}), {d}))` | `2 / 2` (`rank, ts_delta`) | 捕捉预期修正、财报边际改善、评论/销量加速（`d ∈ {5, 22, 66}`；警惕分析师 period roll） |
| **S0-T3** | `TOP100_2026Q4`<br>`ZS59763 #32` (ATLAS L2B→L4) | 时序标准分截面映射 | `rank(ts_zscore(ts_backfill({X}, {bf}), {d}))` | `2 / 2` (`rank, ts_zscore`) | 模型预测分/情绪分/应计比率（`d ∈ {63, 126, 252}`），严守先时序后 `rank` 铁律 |
| **S0-T4** | `TOP100_2026Q4`<br>`RM49262 #45` (`35294898626711`) & `LW67640 #79` (`35926078666263`) | 行业内波动/均值偏离（单字段）或低 op 协方差（双字段） | 单字段：`group_rank(ts_av_diff(ts_backfill({X}, {bf}), {d}), subindustry)`<br>双字段：`rank(ts_covariance(ts_backfill({X1}, {bf}), ts_backfill({X2}, {bf}), {d}))` | `2 / 2` | 单字段抓细分行业内相对偏离（`d=66`）；双字段在低拥挤情绪/行为集抓协同运动（`d=60`） |

> **方向翻转规则（符合 Decision #3）**：当 S0 探针测得 `IS Sharpe < -1.2`（或如 `DEU/model264`“下跌概率”天然先验负向）时，直接套 **`reverse(...)`**（`+1` 算子，零乘法，严禁 `-1 * (...)`！）。

---

## 4. Stage-2 表达式级双分支组合包（100% 落实 Decision #3）

> **核心范式（严禁 `rank(A) + rank(B)` 与 `rank(A) * rank(B)`）**：
> - **核心结构 1（正向双强共振）**：`min(rank(expr_A), rank(expr_B))` — 源自管理员 `WL13229` `23906082201239` L373，要求两条独立经济证据**同时强劲**才给高分，天然惩罚单边跛脚（杜绝假组合）。
> - **核心结构 2（反向双强共振 / 排雷共振）**：`reverse(min(rank(expr_A), rank(expr_B)))` — 严格对齐用户实盘模板 `reverse(min(rank(ts_delta(ts_backfill(vec_avg(f1),500),55)), rank(ts_decay_linear(ts_backfill(f2,5),378))))`，特别适合 **“双风险/双下跌概率共振取反”** 或 **“短期过热 + 长期高估共振做空”**！
> - **核心结构 3（单侧触发共振，仅逻辑证成时启用）**：`max(rank(expr_A), rank(expr_B))` — 仅当经济逻辑支持“任一催化剂显著触发即成立”时单独建假设卡，重点核查尾部权重集中与换手。
> - **单变量五步对照流程（A → B → C1 / C2 → E，已彻底移除原 D 步 `add`！）**：
>   - **A 步**：单独验证 `rank(expr_A)`（确认信号真实有效且方向锁定）
>   - **B 步**：单独验证 `rank(expr_B)`（确认第二分支非噪声，排除单边无效假组合）
>   - **C1 步**：`min(rank(expr_A), rank(expr_B))`（正向双强共振）
>   - **C2 步**：`reverse(min(rank(expr_A), rank(expr_B)))`（若双分支均为风险/下跌/过热信号，或双强共振呈显著负 Sharpe 时）
>   - **E 步（可选）**：`max(rank(expr_A), rank(expr_B))`（仅事件催化型逻辑启用）

### 4.1 通用表达式级双分支骨架库（全 Gold 84，计费独立算子均 `< 6`）

| 模板编号 | 来源配比归属 | 组合模式与 FASTEXPR 骨架 | Distinct / Total 计费算子（不含 `ts_backfill`） | 适用场景与防坑要点 |
| :---: | :---: | --- | :---: | --- |
| **C2-M1** | `ADMIN_ORIGINAL`<br>(`WL13229` `23906082201239`) | `min(rank(ts_delta(ts_backfill({X1}, {bf1}), {d1})), rank(ts_decay_linear(ts_backfill({X2}, {bf2}), {d2})))` | `4 / 5` (`min, rank, ts_delta, ts_decay_linear`) | **边际变化 × 稳态水平共振**（先平滑再 `rank`，彻底规避 `ts_decay_linear(rank)` 的 `dense=false` 陷阱！） |
| **C2-M2** | `ADMIN_ORIGINAL` + 用户实盘范式 | `reverse(min(rank(ts_delta(ts_backfill({X1}, {bf1}), {d1})), rank(ts_decay_linear(ts_backfill({X2}, {bf2}), {d2}))))` | `5 / 6` (`reverse, min, rank, ts_delta, ts_decay_linear`) | **严格对齐用户实盘范式！** 适合双下跌概率/双负面评级/双过热共振做空；若 `{X1}` 为 VECTOR（`vec_avg`），则 `Distinct=6 / Total=7`，仍满足 PP `≤8`，进入第三关可消融去掉外层或精简支路至 `<6` |
| **C2-M3** | `ADMIN_ORIGINAL`<br>(`WL13229` 截面+时序双强) | `min(rank(ts_zscore(ts_backfill({X1}, {bf1}), {d1})), rank(ts_rank(ts_backfill({X2}, {bf2}), {d2})))` | `4 / 5` (`min, rank, ts_zscore, ts_rank`) | **双无量纲时序共振**（抗跨量纲干扰，适合不同单位但同向的两条强证据） |
| **C2-M4** | `TOP100_2026Q4`<br>(`JR23144 #12` + `SM63503 #57` 同向极值对齐) | `min(rank(ts_decay_linear(ts_backfill(vec_min({V1}), {bf1}), {d1})), rank(ts_decay_linear(ts_backfill(vec_min({V2}), {bf2}), {d2})))` | `4 / 7` (`min, rank, ts_decay_linear, vec_min`) *(精简版去掉一侧平滑则 `4 / 6`)* | **VECTOR 同向底线共振**：外层 `min` 对齐内层 `vec_min`，筛选“连最悲观分析师/最低评分都不差”的极致安全垫标的！ |
| **C2-M5** | `TOP100_2026Q4`<br>(`ZS59763 #32` + `WL13229` 行业+全局双强) | `min(group_rank(ts_backfill({X1}, {bf1}), industry), rank(ts_delta(ts_backfill({X2}, {bf2}), {d2})))` | `4 / 4` (`min, group_rank, rank, ts_delta`) | **低 op 黄金骨架（仅 4 op！）**：行业内绝对优等生 × 全市场边际加速（源自本地 `group_relative.py #103` 的双字段升级版） |
| **C2-M6** | `TOP100_2026Q4`<br>(`JR23144 #12` 单侧催化触发) | `max(rank(ts_delta(ts_backfill({X1}, {bf1}), {d1})), rank(ts_zscore(ts_backfill({X2}, {bf2}), {d2})))` | `4 / 5` (`max, rank, ts_delta, ts_zscore`) | **单侧催化触发**（仅当任一利好/异动事件出现即应建仓时启用；必查最大权重与 TVR） |

### 4.2 四大战区即插即用 D1 绑定示例（100% 实盘核验字段 ID，全部遵循 ATOM + 免额度优先！）

> 以下所有示例均已逐字符核验：**全部字段来自对应战区 Field Card**、**全部为 Gold 84 算子**、**零 `+` / `*` / `trade_when`**、**单数据集 ATOM**！

1. **`DEU / TOP500 / D1` · `model264`（`1.8×` 空白塔，100% `Alphas=0` FREE + ATOM）**
   - *经济假设*：资金流（Chaikin Money Flow）下跌概率边际走弱 + 1M 评级扩散下跌概率稳态走低 → 双重下跌风险共振取反（即锁定“资金流未恶化且评级未走弱”的双强标的）。
   - *绑定表达式*（`Distinct = 5`, `Total = 6`, 零 `ts_backfill` 需要因 `cov=99.66%`）：
     ```fastexpr
     reverse(min(rank(ts_delta(mdl264_1l_fmc, 22)), rank(ts_decay_linear(mdl264_1l_m1d_cer_se, 66))))
     ```
   - *极简 `<6` Total 版*（`Distinct = 4`, `Total = 5`）：
     ```fastexpr
     reverse(min(rank(mdl264_1l_fmc), rank(ts_decay_linear(mdl264_1l_m1d_cer_se, 22))))
     ```

2. **`DEU / TOP500 / D1` · `analyst93`（`1.8×` 空白塔，100% `Alphas=0` FREE + ATOM，已避开 5 个纯 ID 字段）**
   - *经济假设*：覆盖该股的分析师过去 60 日跟单盈利能力强 × 机构预测误差一致性高（稳健精准）→ 双强共振。
   - *绑定表达式*（`Distinct = 5`, `Total = 6`，`ts_backfill` 不计 op）：
     ```fastexpr
     min(rank(ts_decay_linear(ts_backfill(vec_avg(anl93_profitabilityprev_analyst_profitability1_60d), 22), 66)), rank(ts_backfill(vec_avg(anl93_estimator_consistency), 22)))
     ```
   - *同向底线对齐版（`JR23144 #12` `vec_min` 对齐外 `min`）*（`Distinct = 4`, `Total = 6`）：
     ```fastexpr
     min(rank(ts_backfill(vec_min(anl93_profitabilityprev_analyst_profitability1_60d), 22)), rank(ts_backfill(vec_min(anl93_estimator_consistency), 22)))
     ```

3. **`ASI / MINVOL1M / D1` · `ai_news_scores`（唯一活跃 D1 Theme + `1.3×` 空白塔，100% `Alphas=0` FREE + `PPA+ATOM` 免配额！）**
   - *经济假设*：纯 ASI D1 正向新闻 95% 置信下界边际走强 × 纯 ASI D1 最低负向情绪分反序走高（即无负面拖累）→ 正向共振且无利空扯后腿（**必配 `maxTrade = ON`**）。
   - *绑定表达式*（`Distinct = 5`, `Total = 6`，`ts_backfill` 不计 op，满足 `PPA ≤ 8` 且接近 `<6`）：
     ```fastexpr
     min(rank(ts_delta(ts_backfill(positive_score_confidence_lower_bound_2, 10), 22)), rank(reverse(ts_decay_linear(ts_backfill(negative_score_minimum_value_2, 10), 22))))
     ```
   - *Normal 高覆盖冲榜备选（`price_signal_dl`, `cov=92%`, `PPA+ATOM`）*（`Distinct = 4`, `Total = 5`）：
     ```fastexpr
     min(rank(ts_decay_linear(normalized_trend_indicator_5, 10)), rank(ts_delta(normalized_volume_indicator_2, 22)))
     ```

4. **`CHN / TOP2000U / D1` · `other496`（全场最高 `1.9×` 空白塔，100% `Alphas=0` FREE + ATOM）**
   - *经济假设*：全免额度流动比率（流动性安全垫）强 × 上下游占款议价力（应付账款 / 应收账款）强 → 双重高质量资产负债表共振（低换手天然契合 CHN `Margin ≥ 20bp`！）。
   - *绑定表达式*（`Distinct = 3`, `Total = 5`，`ts_backfill` 不计 op，超精简仅 3 种算子！）：
     ```fastexpr
     min(rank(divide(ts_backfill(oth496_ard_total_cur_assets_282, 126), ts_backfill(oth496_ff_liabs_curr_nugget, 126))), rank(divide(ts_backfill(oth496_ard_accounts_payable_trade_333, 126), ts_backfill(oth496_q_ard_accts_receivable_trade, 126))))
     ```
   - *CHN `analyst45`（`1.8×` 空白塔，100% `Alphas=0` FREE + ATOM）*（`Distinct = 5`, `Total = 6`）：
     ```fastexpr
     min(rank(ts_decay_linear(ts_backfill(vec_avg(net_exposure_value), 10), 22)), rank(ts_backfill(vec_avg(risk_adjusted_performance_alpha), 10)))
     ```

5. **`P1 2→3 速赢示例`（`GBR/TOP700/D1` `dl_riskfree_returns` 100% `Alphas=0` FREE + ATOM，`1.6×`）**
   - *经济假设*：5 日看空尾概率 × 20 日看空尾概率双重走高取反（双周期排空共振）：
     ```fastexpr
     reverse(min(rank(ts_decay_linear(probability_label0_3quantile_5day_eur_ohlc_ma, 5)), rank(ts_decay_linear(probability_label0_3quantile_20day_eur_ohlc_ma, 20))))
     ```

---

## 5. Stage-2/3 按症状单变量诊断急救模板库（100% Gold 84 + Decision #3 合规）

> **铁律**：每次仅变更 **1 个诊断轴**，严禁同时叠加两套修复模板！

| 诊断症状 | 来源归属 | 急救模板（Gold 84 实核语法） | 新增计费 op | 操作约束与反例警戒 |
| --- | --- | --- | :---: | --- |
| **Sub-Universe 失败 / 跨国区域暴露过重（GLB/EUR/ASI）** | `TOP100_2026Q4`<br>`SZ83096 #47` (`42509573118999`) | ① 嵌套分组：`group_rank(group_rank({ALPHA}, subindustry), country)`<br>② 笛卡尔分组：`group_neutralize({ALPHA}, group_cartesian_product(country, industry))` | `+2` | 曾实测救 Sub `0.61→1.25`；优先在多国池（GLB/ASI/EUR）使用；单国池（DEU/GBR/CHN）改用 `group_rank({ALPHA}, subindustry)` 或 `group_neutralize(..., industry)` |
| **PC 卡在 `0.70–0.75`（信号好但临门一脚）** | `TOP100_2026Q4`<br>`SZ83096 #47` (`42509573118999`) | 保序分布重塑：`signed_power(normalize({ALPHA}), {p})`<br>参数档位：`p ∈ {0.5, 0.75, 1.5, 2.0}` | `+1~2` | 实测可把 PC 从 `0.751→0.69` 同时保住 Sharpe；必须保证输入以 0 为中心（故先 `normalize` 或 `group_neutralize`，防 `[0,1]` 排名单边挤压） |
| **SC/PC 仍偏高（且含低换手 MATRIX）** | `TOP100_2026Q4`<br>`ZS59763 #32` (王哥 Skill) | 离散分箱转分组：`group_neutralize({ALPHA}, bucket(rank({LOW_TVR_FIELD}), range="0.2, 1, 0.2"))` | `+3`（`group_neutralize, bucket, rank`） | 仅用于低换手基本面/市值辅助字段分箱；密切监控总 op `< 6` 限制，勿套在高频字段上以免换手暴涨 |
| **VECTOR 极值噪声 / 方向错配** | `TOP100_2026Q4`<br>`JR23144 #12` & `SM63503 #57` | ① 底线对齐：`ts_min` / `min` 内配 `vec_min({V})`<br>② 爆发对齐：`ts_max` / `max` 内配 `vec_max({V})`<br>③ 稳态对齐：`ts_mean` 内配 `vec_avg({V})` | `0`（同元替换） | **先经 `JX14975 #100` 排查伪 VECTOR**：若单值伪 VECTOR（如 `ASI/behavioral_signals`），只用 `vec_avg`，禁止无意义枚举 |
| **中间段噪音拖累 Sharpe / 尾部信号锐利** | `TOP100_2026Q4`<br>`SJ65808 #78` (`36915505477271`) | ① 必先 `[0,1]` 排名再 `tail`：`tail(rank({ALPHA}), lower=0.2, upper=0.8, newval=0)`<br>② 单边截断（替代缺失的 `right_tail`）：`if_else(rank({ALPHA}) > 0.2, rank({ALPHA}), 0)` | `+1~2` | **Gold 84 实核**：本账号有 `tail`，**无 `left_tail`/`right_tail`/`generalized_rank`**！`tail` 输入必先 `rank` 到 `[0,1]`；监控 `Weight < 10%` 与空头数防单边 |
| **换手偏高（`>30%`）或 Margin 偏薄** | `ADMIN_ORIGINAL` (`WL13229` `43567319117079`) + `TOP100_2026Q4` (`ZS59763 #32`, `JX79797 #15`) | 按顺序**单轴独立测试**：<br>① 平台 `decay`: `0 → 1 / 3 / 5`<br>② 内部平滑（**在 `rank` 之前！**）：`rank(ts_decay_linear({RAW}, 5))` 或 `ts_decay_linear(rank({RAW}), 5, dense=true)`<br>③ 阈值防抖：`hump({ALPHA}, hump=0.01)`（**必写 `hump=` 关键字**）<br>④ 目标换手衰减：`ts_target_tvr_decay({ALPHA}, lambda_min=0, lambda_max=1, target_tvr=0.1)` | `+0~1` | ① **严禁 `ts_decay_linear(rank(x), d)` 默认 `dense=false`**；<br>② **严禁 `lambda_max > 1`**（`JX79797 #15` 实测反增换手）；<br>③ **ASI `MINVOL1M` 慎用 `hump`**（易锁死权重集中）；<br>④ 同步监控 2Y 与 RN（防 `GreR9PXG→KPE1Z3zk` 反例） |
| **权重集中 / 覆盖不足门控** | `TOP100_2026Q4`<br>`JL71699 #9` (`28328131324823`) | `if_else(group_count({ALPHA}, market) > 100, {ALPHA}, 0)`（+ 调小 `truncation: 0.08→0.04` / `maxTrade=ON` / `maxPosition`） | `+2` | 严禁使用 `trade_when`；`if_else(rank(cap)>0.3, alpha, 0)` 救 Sub 仅作一次性应急（复用极易推高 SC，`XW23690 #42` 警示） |
| **阶段性波动率切换（动量 vs 反转）** | `TOP100_2026Q4`<br>`YW82626 #35` (`33601363405591`) | `if_else(ts_rank(ts_std_dev(returns, 20), 252) > 0.5, reverse({ALPHA}), {ALPHA})` | `+4` | 注意引入 `returns` 会打破单数据集 ATOM 资格（仅在非 ATOM 常规队列启用），且需查 `OpCount < 6` |
| **第三关末期：算子消融 + 防过拟合压测** | `TOP100_2026Q4`<br>`ZH87224 #51` (`41105918774807`) + `ZS59763 #32` | **必做三步终检工序**：<br>1. 逐一剥离冗余 `ts_backfill` / `winsorize` / `abs` / 内层 `rank`，确认无损则留精简版（目标 `< 6` op）；<br>2. Decay 防断崖扫频 `[0, 1, 3, 5, 10, 20]`（断崖下跌直接淘汰）；<br>3. 9 项中性化局部稳健复核（`NONE`, `MARKET`, `SECTOR`, `INDUSTRY`, `SUBINDUSTRY`, `CROWDING`, `FAST`, `SLOW`, `REVERSION_AND_MOMENTUM`，注意全拼禁 `RAM`） | `-1~-3`（减 op） | 严禁把 `SUBINDUSTRY` 当通用银弹（反例：GBR `qMNZ` 换 `SUBINDUSTRY` 致 RN Fitness 摔到 `0.89`） |

---

## 6. 42 条缺陷模板隔离清单与 `expr_validator.py` 自动拦截规范

为防止 `wq_research_v2` 误引入旧 `224个模板审核清单.md` 与 `all_operator_templates.py` 的历史缺陷，以下规则须由 `wq_research_v2/expr_validator.py` 自动加载拦截：

### 6.1 旧 224 模板库中强制隔离的 42 条静态缺陷分类清单

| 隔离类别 | 数量 | 精准模板序号与 ID（`224个模板审核清单.md`） | 缺陷根因与拦截规则 |
| --- | :---: | --- | --- |
| **1. Markdown 序号粘连 Bug** | **3** | `#152` `(3)-1 * (...)` (`edb19fdad84fd35c`)<br>`#169` `2.-ts_rank(...)` (`2d67ac5ab50962df`)<br>`#172` `(1)-rank(...)` (`921283dc7cfcc9ed`) | 爬虫解析正文列表序号时误拼入公式，导致表达式完全变味或报错。正则拦截：`^\s*(\(\d+\)|\d+\.)\s*-` |
| **2. 纯布尔 / 硬编码阈值残片** | **17** | `#11` (`5bdde2b0`), `#13` (`7d899f43`), `#25` (`64b9570e`), `#30` (`916baf05`), `#31` (`9fc2b549`), `#90` (`857d7c54`), `#105` (`e5c480d5`), `#114` (`1d33b0f5`), `#117` (`6548eba5`), `#138` (`7b8f904f`), `#142` (`cc7ae197`), `#144` (`d46c2df1`), `#181` (`78e60961`), `#186` (`e7c7ead2`), `#187` (`0465301f`), `#200` (`e2169017`), `#206` (`508f467b`) | 顶层返回 0/1 布尔值或把硬阈值（如 `>100`、`>0.7`、`!=0`）当独立 Alpha，引发无空头/权重集中/严重过拟合。AST 拦截：顶层比较节点禁止直接作为完整表达式 |
| **3. 全市场/全交易所零方差常量** | **5** | `#48` `group_mean(x,1,market)` (`829bd31f`)<br>`#55` `group_mean(x,1,densify(exchange))` (`4fc603ec`)<br>`#63` `group_count(x,market)` (`e918b390`)<br>`#83` `group_std_dev(x,market)` (`35d997f3`)<br>`#87` `group_count(x,densify(market))` (`486dea3a`) | 截面内所有股票取值完全相同，去均值中性化后全市场权重坍塌为 0。AST 拦截：顶层 `group_(mean|count|std_dev)(..., market)` 禁止独立输出 |
| **4. 冗余双套壳（无效叠 op）** | **4** *(+1 预警)* | `#86` `group_rank(ts_backfill(ts_backfill(x,120),120),subindustry)` (`484e8e14`)<br>`#102` `-group_rank(ts_delta(ts_backfill(ts_backfill(x,120),120),252),industry)` (`d5a91873`)<br>`#108` `group_neutralize(group_zscore(x,industry),industry)` (`fe3b6dc2`)<br>`#113` `ts_backfill(ts_backfill(x,120),66)` (`f37cf545`)<br>*(预警 `#93` `rank(group_rank(x,industry))` `98806ef0`)* | 数学幂等冗余套壳，白白消耗 Tiebreaker op 预算。AST 拦截：嵌套同名 `ts_backfill(ts_backfill)` 及同组 `group_neutralize(group_zscore)` |
| **5. 数值溢出 / 陈旧回填 / 量纲混加** | **5** *(+1 预警)* | `#51` `ts_product(1+group_mean(x,1,market),250)-1` (`15c3fed1`)<br>`#109` `ts_backfill(x,1200)` (`812d50a2`)<br>`#118` `ts_product(x+1,250)-1` (`aad2bf5b`)<br>`#208` `-ts_delta(x,5)-rank(ts_delta(x,5))` (`7091c264`)<br>`#209` `ts_product(x,122)+ts_delta(x,22)` (`918543c1`)<br>*(预警 `#159` `ts_scale(rank(x),660)` `c2d9cb64`)* | 5 年陈旧回填（`d>500` 非特批）、250 日连乘溢出、原始值与 `[0,1]` 排名直接混加减。AST 拦截：`ts_backfill` 窗口 `> 504` 标硬阻断、`ts_product` `d > 60` 标高危 |
| **6. 定义域敏感算子（仅人工特批严格正值）** | **8** | `#9` `sqrt(x)` (`4b1b453d`), `#14` `inverse(x)` (`969db6e6`), `#34` `log(x)` (`da7c4db8`), `#36` `log(x/ts_delay(x,1))` (`e4c1d3e4`), `#116` `rank(ts_mean(log(x),25))` (`3ddf50f0`), `#125` `log(ts_mean(x,44))-log(ts_mean(x,20))` (`fd5b4f3b`), `#145` `log(ts_mean(x,21))` (`d6855faf`), `#170` `ts_std_dev(x,21)*sqrt(252)` (`62b3e3de`) | 对负值/零值字段产生大面积 `NaN`/`Inf` 致覆盖崩塌。默认隔离，仅对经 Field Card 确认为严格正值的字段手动放行 |
| **合计** | **42** | 覆盖全部 6 类静态缺陷 | 另有 **28 条** 含 `+` / `*`（如 `#3, #18, #20, #35, #52, #59, #79, #153, #167, #175, #176, #188, #224` 等）由下方 **Decision #3 规则统一一刀切封禁**！ |

### 6.2 旧 `all_operator_templates.py` 4 处签名雷区 + Decision #3 引擎硬规则
`wq_research_v2/expr_validator.py` 必须同时内置以下 6 条硬断言：
1. **D1 硬断言**：`settings["delay"] == 1`，否则直接抛 `ValidationError`。
2. **Decision #3 禁用算子硬拦截**：AST 禁止任何 `BinOp(Add)`（`+`）、`BinOp(Mult)`（`*`）、函数调用 `add(...)`、`multiply(...)`、`trade_when(...)`（所有乘 `-1` 改用 `reverse(...)` 或一元 `-`；所有双分支组合改用 `min/max(rank(expr_A), rank(expr_B))`）。
3. **Gold 84 白名单硬校验**：只放行 2026-11-25 实核 84 算子减去上述 3 禁用算子后的 **81 个许可算子**，自动拦截 `ts_median`、`left_tail`、`right_tail`、`generalized_rank`、`hump_decay`、`ts_decay_exp_window`。
4. **4 处历史签名纠错**：
   - `hump(x, 0.01)` → **报错拦截**，强制 `hump(x, hump=0.01)`；
   - `ts_scale(x, scale=1)` → **报错拦截**，正确签名 `ts_scale(x, d, constant=0)`；
   - `ts_step(20)` → **报错拦截**，正确签名 `ts_step(1)`；
   - `ts_target_tvr_decay(..., lambda_max=2)` → **报错拦截**，强制 `lambda_max <= 1`。
5. **`ts_decay_linear(rank(...), d)` 陷阱拦截**：若 `ts_decay_linear` 第一参数根节点为 `rank`/`group_rank` 且未显式传 `dense=true`，发硬警告/拦截，提示改写为 `rank(ts_decay_linear(..., d))` 或补 `dense=true`。
6. **纯 ID / 废弃字段与 `Alphas=0` 纯度拦截**：
   - 拦截已知非数值陷阱字段（如 `anl93_*_analyst`、`anl10_*_det_analyst_*`、`anl10_*_anntime_*`、`anl10_*_flag_*`、`anl10_*_indicator_*`、`mdl307_cusip/sector/country/atlas_unit_name`、`fnd6_adesinda_curcd`、`adjusted_bias_return`、`*_currency_code_*`、`oth592_*_relatedii` 等）；
   - 当任务标记 `queue_type == "UNUSED_ALPHA0"` 时，AST 解析全部非关键字标识符，断言每一个经济字段（排除 9 个 PV1 辅助字段）均在当前 `Region × Universe × D1` 快照中满足 `alphaCount == 0`，否则自动降级至 `NORMAL` 队列，绝不误耗普通日额度！
