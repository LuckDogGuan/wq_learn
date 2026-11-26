# 43｜super alpha第二节

[原始转录](<../原始转录/43-super alpha第二节.txt>) · [原片截图索引](<../画面回看索引.txt>)

按 6 分钟编排为 6 个区间。旁注时间来自对应字幕或画面采样。

<a id="part-01"></a>
## 00:00:00–00:06:00　Super Alpha 第二节：数据核查与表达式构建

### 选择Alpha时的权重设定  

〔语音 00:00:30〕 讲师提到，选择Alpha时，Turnover被用作权重，目的是选出那些“爱做空”的Alpha。这种Alpha被认为具有较高的价值，因为它们可能在市场下跌时表现更好。  

〔语音 00:01:00〕 讲师指出，Turnover作为权重，不仅要求Alpha做空，还要求其频繁做空。因此，他将Turnover乘以某个系数，以确保最终结果能相对地保证这一特性。  

〔语音 00:01:30〕 然而，讲师也指出，这种表达方式并不“漂亮”，因为它忽略了Universe Size的影响。Universe Size指的是Alpha所覆盖的资产数量，如果Universe Size过小，即使Turnover高，也可能无法选出真正有价值的Alpha。  

**核对办法**：在选择Alpha时，应检查Universe Size是否合理，避免因Universe Size过小而引入Bias。  

### 表达式构建与Selection Handling  

〔语音 00:02:30〕 讲师强调，在构建表达式时，不能只依赖条件语句，还应考虑Selection Handling。例如，如果想选择Turnover最低的Alpha，可以加一个负号，或者用1减去Turnover，以实现数学上的等价。  

〔语音 00:03:00〕 此外，讲师还提到，选择Alpha时，应考虑多个条件，如OperatorCounts、Turnover等。例如，一个Alpha可能同时满足以下条件：  
- 在Model52中使用 〔语音 00:03:30〕  
- OperatorCounts小于50  
- Turnover小于某个阈值  

**核对办法**：在构建表达式时，应使用多个条件语句，并合理设置Selection Handling，以确保选出的Alpha符合预期。  

### 表达式中的Universe Size影响  

〔语音 00:01:30〕 讲师指出，Universe Size对最终结果有重要影响。如果Universe Size过小，即使Turnover高，也可能无法选出真正有价值的Alpha。因此，在选择Alpha时，应考虑Universe Size的合理性。  

**核对办法**：在选择Alpha时，应检查Universe Size是否合理，避免因Universe Size过小而引入Bias。  

### 表达式构建的注意事项  

〔语音 00:04:00〕 讲师强调，在构建表达式时，应避免只使用条件语句，还应考虑其他操作符，以确保选出的Alpha具有更高的特性和排名。例如，可以使用数学运算符，如减法、乘法等，以实现更复杂的筛选逻辑。  

**核对办法**：在构建表达式时，应使用多种操作符，并合理设置Selection Handling，以确保选出的Alpha符合预期。  

### 表达式构建的反例  

〔语音 00:04:00〕 讲师提到，如果只使用条件语句，可能会导致选出的Alpha数量过多，无法有效筛选出真正有价值的Alpha。因此，在构建表达式时，应合理设置Selection Limits，如选择前〈数值待核〉个Alpha，以确保选出的Alpha具有更高的特性和排名。  

**核对办法**：在构建表达式时，应合理设置Selection Limits，如选择前〈数值待核〉个Alpha，以确保选出的Alpha具有更高的特性和排名。  

### 表达式构建的总结  

〔语音 00:04:30〕 讲师总结，在构建表达式时，应考虑Turnover、Universe Size、Selection Handling、Selection Limits等多个因素，以确保选出的Alpha具有更高的特性和排名。同时，应避免只使用条件语句，还应考虑其他操作符，以实现更复杂的筛选逻辑。  

**核对办法**：在构建表达式时，应综合考虑多个因素，并合理设置Selection Handling和Selection Limits，以确保选出的Alpha具有更高的特性和排名。  

### 表达式构建的复验建议  

〔画面 00:00:10〕 为了验证表达式是否正确，可以使用不同的参数进行测试，如调整Turnover的权重、改变Universe Size的范围等。同时，可以使用不同的Selection Handling方式，如加负号、用1减去Turnover等，以确保选出的Alpha符合预期。  

**复验建议**：在构建表达式时，应使用不同的参数和Selection Handling方式，以验证选出的Alpha是否符合预期。

![用候选属性过滤并排序](../画面/43/00-04-10-frame-013.jpg)

*原片 00:04:10 · 用候选属性过滤并排序*

<a id="part-02"></a>
## 00:06:00–00:12:00　Super Alpha 第二节

### 一、SuperAlpha与RegularAlpha的设置差异  

讲师在〔语音 00:06:00〕中指出，SuperAlpha和RegularAlpha在设置界面存在差异。右边是RegularAlpha的Setting，左边是SuperAlpha的Setting。讲师在〔语音 00:06:30〕中进一步说明，RegularAlpha有Universe（股票池），而SuperAlpha没有Universe，但有Delay（延迟）。  

讲师在〔语音 00:07:00〕中强调，SuperAlpha和RegularAlpha在功能上其实差别不大，只是RegularAlpha需要用户定义股票池，而SuperAlpha则让用户自行选择Alpha。  

**复验建议**：在SuperAlpha的Setting中，检查是否包含Delay字段，确认其与RegularAlpha的差异。  

### 二、Alpha作为资产的理解  

讲师在〔语音 00:07:30〕中指出，SuperAlpha的核心理念是将Alpha视为一个资产，而不是传统的股票。一个Alpha可以看作是一个最小的元素，就像股票一样。  

讲师在〔语音 00:08:00〕中进一步说明，选择Alpha后，数据库中会形成一个三维数据结构，用户需要通过表达式将其转化为二维数据，以便平台运行。  

**复验建议**：在SuperAlpha的数据库中，确认是否支持三维数据结构，并尝试将其转化为二维数据。  

### 三、Generate Stats的使用  

讲师在〔语音 00:09:00〕中提到，选择Alpha后，可以通过Generate Stats提取Alpha的特征，如Returns、Holder P&L、Drawdown等。  

讲师在〔语音 00:09:30〕中详细说明，Generate Stats可以提取多种统计指标，包括Returns、P&L、Drawdown等，这些指标可以类比股票的价格、成交量等。  

**复验建议**：在SuperAlpha中尝试使用generate_stats(alpha)提取Alpha的统计特征，并确认是否能获取Returns、P&L等指标。  

### 四、Alpha与股票的类比  

讲师在〔语音 00:10:30〕中指出，Alpha可以类比为股票，其P&L可以看作是Alpha的价格，Return可以看作是Alpha的收益率。  

讲师在〔语音 00:11:00〕中进一步说明，Alpha的Volume（成交量）和Trade Value（成交额）可以类比股票的成交量和成交额，甚至可以计算AdV20（过去20天的平均成交量）。  

**复验建议**：在SuperAlpha中尝试计算Alpha的AdV20，并确认是否与股票的AdV20计算方式一致。  

### 五、Alpha数据的构建  

讲师在〔语音 00:11:30〕中强调，Alpha的数据构建类似于股票，包括P&L、Return、Volume、Trade Value等字段。  

讲师在〔语音 00:10:30〕中指出，用户需要将Alpha的这些数据构建为类似股票的数据结构，以便后续的表达式编写和回测。  

**复验建议**：在SuperAlpha中尝试构建Alpha的数据结构，并确认是否包含P&L、Return、Volume等字段。  

### 六、Alpha表达式的构建  

讲师在〔语音 00:08:30〕中提到，用户需要将三维数据转化为二维数据，以便平台运行。  

讲师在〔语音 00:10:00〕中指出，用户需要将Alpha的特征转化为数据，以便后续的表达式编写。  

**复验建议**：在SuperAlpha中尝试将三维数据转化为二维数据，并确认是否能成功运行表达式。  

### 七、Alpha的统计特征  

讲师在〔语音 00:10:00〕中指出，用户可以通过Generate Stats提取Alpha的统计特征，如Returns、P&L、Drawdown等。  

讲师在〔语音 00:10:30〕中进一步说明，这些统计特征可以类比股票的价格、成交量等，帮助用户更好地理解Alpha的表现。  

**复验建议**：在SuperAlpha中尝试使用generate_stats(alpha)提取Alpha的统计特征，并确认是否能获取Returns、P&L等指标。  

### 八、Alpha的表达式编写  

讲师在〔语音 00:08:30〕中强调，用户需要将Alpha的特征转化为数据，以便后续的表达式编写。  

讲师在〔语音 00:10:00〕中指出，用户需要将Alpha的特征转化为数据，以便后续的表达式编写和回测。  

**复验建议**：在SuperAlpha中尝试将Alpha的特征转化为数据，并确认是否能成功运行表达式。  

### 九、Alpha的回测  

讲师在〔语音 00:09:30〕中提到，用户可以通过Generate Stats提取Alpha的统计特征，并用于回测。  

讲师在〔语音 00:10:00〕中进一步说明，用户可以通过这些统计特征进行回测，以评估Alpha的表现。  

**复验建议**：在SuperAlpha中尝试使用Generate Stats提取Alpha的统计特征，并进行回测，确认是否能获取回测结果。  

### 十、Alpha的稳健性  

讲师在〔语音 00:07:00〕中指出，SuperAlpha的核心理念是将Alpha视为一个资产，而不是传统的股票。  

讲师在〔语音 00:07:30〕中进一步说明，Alpha的稳健性可以通过其表现来评估，如Returns、P&L等。  

**复验建议**：在SuperAlpha中尝试评估Alpha的稳健性，并确认是否能获取Returns、P&L等指标。

![把底层 Alpha 的 PnL、成交和多空数量作为组合输入](../画面/43/00-10-10-frame-031.jpg)

*原片 00:10:10 · 把底层 Alpha 的 PnL、成交和多空数量作为组合输入*

<a id="part-03"></a>
## 00:12:00–00:18:00　Super Alpha 第二节 - 表达式与回测

### 一、数据核查与 Alpha 表现获取  
讲师在 〔画面 00:12:10〕 中展示了平台中用于 Alpha 表现分析的字段，包括 `stats.pnl`、`stats.returns`、`stats.trade_pnl` 等。这些字段是通过调用 `generate_stats(alpha)` 函数生成的，用于评估因子的收益、风险和交易表现。  
- **关键操作**：在平台中，调用 `generate_stats(alpha)` 可以获取因子的统计信息，包括收益、交易盈亏、持仓盈亏等。  
- **验证方式**：在你的平台中运行 `stats = generate_stats(alpha)`，查看输出结果是否包含 `stats.returns`、`stats.trade_pnl` 等字段。  

### 二、表达式编写与分组逻辑  
讲师在 〔语音 00:13:00〕 中提到，可以通过 `rank` 和 `bucket` 函数对因子进行分组，从而构建组合。  
- **关键操作**：  
  1. 使用 `rank` 对因子进行排序，例如 `rank(stats.trade_pnl)`。  
  2. 使用 `bucket` 对排序后的因子进行分组，例如 原片代码参数待核。  
- **验证方式**：在你的平台中尝试运行 原片代码参数待核，观察输出是否为分组结果。  

### 三、数据准备与分组定义  
讲师在 〔画面 00:12:30〕 中展示了如何定义分组逻辑，包括数据准备和分组定义。  
- **关键操作**：  
  1. 数据准备：`stats = generate_stats(alpha)`。  
  2. 定义分组：原片代码参数待核。  
- **验证方式**：在你的平台中运行上述代码，确认是否能正确生成分组结果。  

### 四、分组与因子表现分析  
讲师在 〔语音 00:13:00〕 中提到，可以通过分组来分析因子的表现，例如高分组和低分组的收益差异。  
- **关键操作**：  
  1. 使用 `bucket` 对因子进行分组。  
  2. 分析不同分组的收益表现，例如 `stats.returns`。  
- **验证方式**：在你的平台中运行分组代码，并查看不同分组的收益表现是否符合预期。  

### 五、失败现象与常见问题  
- **失败现象**：如果 `generate_stats(alpha)` 无法返回预期字段，可能是平台配置问题或因子定义错误。  
- **常见问题**：  
  - 分组范围设置错误，例如 原片代码参数待核 应该是数值范围，而不是分组数量。  
  - `rank` 和 `bucket` 函数参数使用错误，例如 `rank(stats.trade_pnl)` 应该是因子值，而不是其他字段。  

### 复验建议  
1. 确认 `generate_stats(alpha)` 是否能正确返回 `stats.returns`、`stats.trade_pnl` 等字段。  
2. 尝试运行 原片代码参数待核，观察分组结果是否符合预期。  
3. 如果分组失败，检查 `rank` 和 `bucket` 的参数是否正确，例如 `range` 是否为数值范围。  
4. 如果 `stats.returns` 无法获取，检查 `generate_stats(alpha)` 是否正确调用。

![本段画面证据 00:12:10](../画面/43/gpu-frame-037.jpg)

*原片 00:12:10 · 本段引用的画面。*

<a id="part-04"></a>
## 00:18:00–00:24:00　Super Alpha第二节 - 数据核查与表达式回测

### 一、数据准备与 stats 函数使用  
**问题**：如何准备数据以进行后续的回测？  
**讲师采用的理由**：  
讲师指出，数据准备是回测的第一步，必须使用 `generate_stats(alpha)` 函数来生成统计信息。  
**操作或公式走读**：  
- 使用 `stats = generate_stats(alpha)` 来获取 alpha 的统计信息。  
- 该函数会返回包括 `trade_pnl`（交易盈亏）和 `hold_pnl`（持有盈亏）等字段。  
**所见结果**：  
屏幕显示了 `stats = generate_stats(alpha)` 的代码片段，并强调这是数据准备的关键步骤。  
**核对办法**：  
- 确认是否调用了 `generate_stats(alpha)` 函数。  
- 检查返回的字段是否包含 `trade_pnl` 和 `hold_pnl`。  

### 二、计算每日振幅  
**问题**：如何计算每日振幅？  
**讲师采用的理由**：  
讲师指出，振幅是衡量价格波动的重要指标，可以通过 `high / low - [数值回看]` 来计算。  
**操作或公式走读**：  
- 使用 `amplitude = high / low - [数值回看]` 来计算每日振幅。  
- 其中 `high` 和 `low` 是价格的最高和最低值，`[数值回看]` 是一个预设的数值（需根据实际数据调整）。  
**所见结果**：  
屏幕显示了 `amplitude = high / low - [数值回看]` 的代码片段，并强调这是计算振幅的关键公式。  
**核对办法**：  
- 确认是否使用了 `high` 和 `low` 字段。  
- 检查是否减去了正确的数值（需根据实际数据调整）。  

### 三、定义分组与桶化  
**问题**：如何定义分组并进行桶化？  
**讲师采用的理由**：  
讲师指出，分组是进行回测和稳健性分析的重要步骤，可以通过 `bucket(rank(cap), range="...")` 来实现。  
**操作或公式走读**：  
- 使用 `grouping = bucket(rank(cap), range="...")` 来定义分组。  
- 其中 `cap` 是资本，`rank` 是排序函数，`range` 是桶的范围（需根据实际数据调整）。  
**所见结果**：  
屏幕显示了 `grouping = bucket(rank(cap), range="...")` 的代码片段，并强调这是分组的关键步骤。  
**核对办法**：  
- 确认是否使用了 `rank` 和 `bucket` 函数。  
- 检查 `range` 参数是否符合实际需求。  

### 四、失败现象与验证建议  
**问题**：如果回测无法运行，可能是什么原因？  
**讲师采用的理由**：  
讲师指出，回测失败可能是由于数据准备不正确或代码逻辑错误。  
**操作或公式走读**：  
- 检查是否正确调用了 `generate_stats(alpha)` 函数。  
- 确认 `high` 和 `low` 字段是否正确。  
- 检查 `bucket` 函数的参数是否合理。  
**所见结果**：  
屏幕显示了部分同学在回测时遇到问题，讲师建议检查数据和代码逻辑。  
**核对办法**：  
- 确认是否所有步骤都正确执行。  
- 检查是否有语法错误或字段名拼写错误。  

### 复验建议  
- 确认 `generate_stats(alpha)` 是否正确调用，并返回了 `trade_pnl` 和 `hold_pnl`。  
- 检查 `amplitude = high / low - [数值回看]` 是否使用了正确的字段和数值。  
- 验证 `grouping = bucket(rank(cap), range="...")` 的参数是否合理，是否符合实际需求。  
- 如果回测失败，建议检查数据准备、字段名和函数调用是否正确。

<a id="part-05"></a>
## 00:24:00–00:30:00　Super Alpha第二节

### 数据核查与维度处理  

讲师在〔语音 00:29:00〕中提到，很多同学在使用Super Alpha时出现了dimension的错误，这通常是因为数据维度不匹配导致的。为了处理这个问题，讲师建议使用一个叫做**reduce operator**的操作符，它能够将三维数据降维为二维数据，从而解决维度不一致的问题。  

**操作说明：**  
- 在WorldQuant BRAIN的界面中，找到“Super Alpha”模块。  
- 在数据处理过程中，如果遇到维度不匹配的错误，尝试使用**reduce operator**。  
- 该操作符类似于**vector operator**，但更适用于将三维数据转换为二维数据。  

**所见结果：**  
- 使用reduce operator后，数据维度问题被解决，系统不再报错。  
- 在〔语音 00:29:00〕中，讲师提到“如果你不知道什么是reduce，就理解vector operator就可以了”，说明reduce operator是vector operator的扩展。  

**核对办法：**  
- 在BRAIN的“Super Alpha”模块中，查看是否有reduce operator的使用说明。  
- 如果没有，可以参考“BRAIN Tips”或“Community”中的相关讨论。  

### Alpha选择与组合优化  

讲师在〔语音 00:27:30〕中强调，选择Alpha的数量对组合的稳定性至关重要。他指出，如果只选择10个Alpha，组合的稳定性较差，容易出现波动。因此，建议用户尽量多选Alpha，尤其是Master和Grand Master级别的Alpha，以提高组合的稳健性。  

**操作说明：**  
- 在“Super Alpha”模块中，进入“Combo by Alpha statistics”界面。  
- 在“Selection”中设置一个较大的Alpha数量，例如50个或更多。  
- 使用“generate_stats(alpha)”函数生成统计信息，并根据信息比率（IR）或波动率（Volatility）进行加权。  

**所见结果：**  
- 选择更多Alpha后，组合的稳定性明显提升。  
- 在〔语音 00:28:00〕中，讲师提到“选10个和选50个的performance有明显差别”，说明Alpha数量对结果有显著影响。  

**核对办法：**  
- 在“Super Alpha”模块中，查看“Combo by Alpha statistics”界面，确认Alpha数量是否足够。  
- 比较不同Alpha数量下的组合表现，如Sharpe比率、Turnover等。  

### 表达式与回测设置  

讲师在〔语音 00:25:30〕中提到，可以通过TSIR（Time Series Information Ratio）计算组合的信息比率，并用于回测。他指出，如果TSIR值与预期不符，可能是由于Alpha数量太少或太多导致的。  

**操作说明：**  
- 在“Super Alpha”模块中，进入“Simulate”界面。  
- 在“Fast Expression”中设置表达式，例如：  
  ```  
  combo exp = 〔数值回看〕  
  ```  
- 使用“ts_ir(stats.returns, 〔数值回看〕)”计算信息比率。  

**所见结果：**  
- 使用不同的Alpha数量和参数设置，TSIR值会有明显变化。  
- 在〔语音 00:26:30〕中，讲师提到“如果选的Alpha太多，TSIR值变动不大”，说明参数设置对结果有影响。  

**核对办法：**  
- 在“Simulate”界面中，查看TSIR值是否与预期一致。  
- 调整Alpha数量和参数，观察TSIR值的变化。  

### 复验建议  

- **Alpha数量不足**：如果TSIR值较低，可能是由于Alpha数量太少，建议增加Alpha数量。  
- **Alpha数量过多**：如果TSIR值波动不大，可能是由于Alpha数量过多，建议减少Alpha数量。  
- **参数设置不当**：如果TSIR值与预期不符，检查参数设置是否合理，如250天的回测窗口。  
- **维度问题**：如果遇到维度错误，使用reduce operator进行降维处理。  

通过以上步骤，用户可以更好地理解和应用Super Alpha的功能，提高组合的稳定性和表现。

<a id="part-06"></a>
## 00:30:00–00:31:21　Super Alpha第二节

### 数据核查与界面确认  

在本节课程中，讲师首先引导学员熟悉 WorldQuant BRAIN 平台的界面，并强调了数据核查的重要性。  

### 〈数值待核〉. 界面标签与人员信息  
- 屏幕上显示了多个人员名字，包括 Kunqi Jiang、Yuqi Liu、WJ Li 等，这些可能是讲师或助教的姓名。  
- 界面中还出现了多个标签，如 **SOURCES AND REFERENCES**、**BRAIN: SuperAlpha section**、**WorldQuant learn section**、**BRAIN Community** 等，这些标签帮助学员快速定位课程内容与相关资源。  
- 课程链接如 [https://platform.worldquantbrain.com/learn/documentation/superalpha/superalpha-overview](https://platform.worldquantbrain.com/learn/documentation/superalpha/superalpha-overview) 和 [https://platform.worldquantbrain.com/learn/documentation](https://platform.worldquantbrain.com/learn/documentation) 也出现在界面中，供学员进一步学习。  

### 〈数值待核〉. 数据来源与回测确认  
- 讲师提到，学员在进行回测前，需要确认数据来源是否正确，例如是否使用了正确的市场数据、资产类别或时间范围。  
- 在 〔画面 00:30:10〕 中，可以看到 **"数值回看"** 的提示，这可能是指在回测过程中需要核对关键数值是否与实际数据一致。  

### 〈数值待核〉. 注意事项  
- 在数据核查过程中，应避免使用猜测或假设，如 OCR 识别错误或字段不明确时，应标注 **"原片待核"**。  
- 所有数值仅引用语音中明确提到的数字，不进行汉字转阿拉伯数字的操作。  

### 复验建议  
- 建议学员在回测前，先确认数据来源与平台界面标签是否匹配，如 〔画面 00:30:10〕 中的链接与标签。  
- 若发现字段或参数无法辨识，应标记为 **"原片待核"**，并记录具体位置以便后续核实。  
- 若有疑问，可参考 〔语音 00:30:00〕 和 〔语音 00:30:30〕 中讲师提到的回测与比赛信息，确认是否与当前课程内容相关。

![本段画面证据 00:30:10](../画面/43/gpu-frame-091.jpg)

*原片 00:30:10 · 本段引用的画面。*
