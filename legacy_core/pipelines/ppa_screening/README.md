# PPA 因子筛选与本地 PPAC 标记流水线

`filter_ppa_alphas.py` 拉取最近一个月的未提交候选，使用 `Core/sim/sc_engine.py` 的本地 PnL 缓存计算 PPAC，再按既有规则写回标签和别名。脚本不再调用平台 `/correlations/power-pool` 接口。

---

## 1. 核心功能与亮点

1. **精准门槛过滤与全选逻辑**
   - 严格支持 `TARGET_REGION`, `TARGET_UNIVERSE`, `TARGET_NEUTRALIZATION` 参数配置。
   - **`None = 全选` 逻辑**：如果将上述参数配置为 `None` 或 `[]`，脚本会自动忽略该限制（全选），绝不误杀。
   - **`TARGET_DELAY` 严格校验**：严禁无脑传 `None` 导致底层数据逻辑失控，配置时若未明确指定 Delay 将直接拦截报错。

2. **多层复合交叉过滤 (API + 内存防穿透)**
   - 针对平台原生 API 难以处理的多选参数（例如多个 Neutralization），脚本采取**“API 精准查询单参数 + 内存二次拦截多选参数”**策略。
   - **底层真值映射**：由于平台界面显示的名称（如 "Fast Factors"）与底层真实枚举名（如 `"FAST"`）存在差异，我们在内存拦截层建立了硬核级精准映射字典（`RAM -> REVERSION_AND_MOMENTUM`, `Fast Factors -> FAST`, `Slow Factors -> SLOW` 等），百分百对齐底层真实环境。

3. **Core 本地 PPAC 缓存**
   - 每次运行启动时只增量刷新一次 OS/PPA PnL 缓存，随后所有候选共用同一参考矩阵。
   - 缓存缺失、候选 PnL 失败、无有效重叠或结果为 NaN 时保持 Alpha 属性不变，不能当作通过。

4. **本地 PPAC 计算与实时标记**
   - 不再等待全部因子遍历结束后才打标，而是采用**边检边打**的极限实时处理流。
   - 单个候选只下载目标 PnL，相关性由 pandas 在本地计算。若 `<= 0.5`，添加 `PPA` 并写入 `PPC 0.xxxx` 别名；若 `> 0.5`，移除 `PPA`、保留其他标签并添加 `PPC_IS_HIGHT`。

---

## 2. 核心业务流程图 (Flowchart)

```mermaid
graph TD
    Start[1. 增量刷新 Core PPAC 缓存] --> APIFilter[2. 拉取最近一个月未提交 Alpha\n北京时间半开区间]
    APIFilter --> PPAFilter{3. 内存二次拦截\n校验 Universe/Neutralization/WARNING/FAIL}
    PPAFilter -->|不匹配| Drop1[剔除不符合要求的因子\n(如 Subindustry)]
    PPAFilter -->|完全匹配| PPC_Calc[4. 使用 Core 本地计算 PPAC]
    
    PPC_Calc --> PPC_Judge{5. PPAC 可判定且 > 0.5 ?}
    PPC_Judge -->|是 (超标)| Drop2[剔除并实时清除旧 PPA 标签]
    PPC_Judge -->|否 (优质)| Rename[保留并实时打上 'PPA' 标签\n修改别名: PPA(0.xx)]
    
    Rename --> Excel[超链接输出至 Excel\n持久化保存]
    Excel --> End[完成候选准备]
```

---

## 3. 全局配置设计 

直接修改 `filter_ppa_alphas.py` 顶部的配置区即可无缝切换战场：

```python
# ================= 全局执行参数配置 =================
CONFIG_DAYS_AGO = 30            # 默认拉取最近 N 天内的数据

# ================= 精准定向筛选门槛 =================
FILTER_SHARPE = 1.0             
FILTER_FITNESS = 0.5            

TARGET_REGION = "GLB"           # 填 None 表示全选
TARGET_DELAY = 1                # 严禁设置为 None！必须明确指定！
TARGET_UNIVERSE = ["TOPDIV3000"]# 填 None 或 [] 表示全选

# 中性化过滤：填 None 或 [] 表示不限制；填 "NONE" 表示精确筛选无中性化
TARGET_NEUTRALIZATION = [
    "Slow Factors",
    "Fast Factors",
    "Slow + Fast Factors",
    "Crowding Factors",
    "RAM"
]
# TARGET_NEUTRALIZATION = "NONE"  # 仅筛选平台中性化枚举 NONE

# PPC 计算前的 WARNING 排除：None 或 [] 表示不筛选，可填写多个关键词
PPC_EXCLUDED_WARNING_PATTERNS = ["High Turnover"]

# 是否在 PPC 前排除普通 RA（无 POWER_POOL_CORRELATION 检查项）
EXCLUDE_REGULAR_RA = False
```

## 4. 执行说明

执行脚本后，控制台会输出高度清晰的漏斗式对账日志，包括每一环节的：
1. 抓取总数
2. 因 Universe 不匹配被剔除的数量
3. 因 Neutralization 不匹配被剔除的数量
4. 因普通 RA 被剔除的数量
5. 实时打标/摘牌追踪及最终剩余量

日志完毕后，所有的结果将被输出到 `output` 文件夹的 Excel 表中供您留档阅览。
