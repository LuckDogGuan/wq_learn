# 25｜Quantcepts： What is Market-Neutral Investing

[原始转录](<../原始转录/25-Quantcepts： What is Market-Neutral Investing.txt>) · [原片截图索引](<../画面回看索引.txt>)

按 6 分钟编排为 1 个区间。旁注时间来自对应字幕或画面采样。

<a id="part-01"></a>
## 00:00:00–00:00:56　Market-Neutral Investing 的基本概念

### 一、市场中性策略的定义  
〔语音 00:00:00〕 中提到，市场中性策略（Long-Short Market Neutral Strategy）是指同时持有等量的多头（Long）与空头（Short）头寸。多头头寸意味着买入股票，期望其价格上涨获利；空头头寸意味着借入股票卖出，期望其价格下跌后低价买回并归还，从而获利。  

**验证步骤**：  
- 回看 〔语音 00:00:00〕 中的定义，确认“long positions”和“short positions”的操作方式。  
- 确认“equal amount”是否在课堂中被明确提及，如“equal weight”或“equal quantity”。  

### 二、多头与空头操作的细节  
〔语音 00:00:00〕 中指出，多头操作是买入股票，等待价格上涨；空头操作是借入股票卖出，希望其价格下跌后低价买回。  

**验证步骤**：  
- 回看 〔画面 00:00:46〕 中是否有“buy back at”或“return the borrowed shares”等关键词，确认空头操作的流程。  
- 注意 〔画面 00:00:46〕 中的“BUY BACK AT”是否与“return the borrowed shares”对应。  

### 三、策略的目标与风险  
〔语音 00:00:00〕 中提到，策略的目标是即使多头头寸下跌，空头头寸的盈利仍能覆盖损失，从而为对冲基金带来收益。  

**验证步骤**：  
- 确认课堂中是否提到“hedge fund”或“risk mitigation”等术语，以支持策略的收益目标。  
- 注意 〔画面 00:00:09〕 中的“CHIEF STRATEGY | OFFICER | WORLDQUANT”是否与策略目标相关，如是否提及“risk neutral”或“market neutral”策略的收益结构。  

### 四、术语与界面标签  
- **Long Position**：买入股票，期望价格上涨。  
- **Short Position**：借入股票卖出，期望价格下跌后低价买回。  
- **Buy Back At**：指在价格下跌后以较低价格买回股票。  
- **Return the Borrowed Shares**：归还借入的股票，完成空头操作。  

**验证步骤**：  
- 回看 〔画面 00:00:46〕 中的“BUY BACK AT”是否与“return the borrowed shares”对应，确认术语是否一致。  
- 注意 〔画面 00:00:09〕 中的“CHIEF STRATEGY”是否与策略定义相关，如是否提及“market neutral”或“long-short”策略。  

### 五、失败现象与反例  
- **失败现象**：若多头头寸大幅下跌，而空头头寸未能盈利，可能导致整体亏损。  
- **反例**：若市场整体上涨，多头头寸获利，但空头头寸亏损，可能导致策略失效。  

**验证步骤**：  
- 回看课堂中是否提到“market direction”或“market trend”对策略的影响，如是否提及“market neutral”策略在牛市或熊市中的表现。  
- 注意 〔语音 00:00:00〕 中是否提到“profit from shorting may still outweigh losses”，确认策略的盈利逻辑。  

### 六、复验建议  
- 若课堂中未明确提及“equal amount”，建议在回测中设置“equal weight”或“equal quantity”作为验证条件。  
- 若 〔画面 00:00:46〕 中的“BUY BACK AT”无法确认，建议在回测中使用“buy back price”或“repurchase price”作为参数。  
- 若 〔画面 00:00:09〕 中的“CHIEF STRATEGY”未明确提及“market neutral”，建议在回测中使用“long-short”或“market neutral”作为策略标签。  

---  
**注**：以上内容基于课堂中提供的文字与画面信息，未涉及任何代码或函数参数，仅用于教学复验与操作指引。

![以平衡的杠杆示意多空组合](../画面/25/00-00-09-frame-001.jpg)

*原片 00:00:09 · 以平衡的杠杆示意多空组合*

![图中低位买回用于解释空头在价格下跌时的收益来源](../画面/25/00-00-46-frame-003.jpg)

*原片 00:00:46 · 图中低位买回用于解释空头在价格下跌时的收益来源*
