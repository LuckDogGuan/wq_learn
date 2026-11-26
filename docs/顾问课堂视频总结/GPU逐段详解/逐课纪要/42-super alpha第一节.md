# 42｜super alpha第一节

[原始转录](<../原始转录/42-super alpha第一节.txt>) · [原片截图索引](<../画面回看索引.txt>)

按 6 分钟编排为 8 个区间。旁注时间来自对应字幕或画面采样。

<a id="part-01"></a>
## 00:00:00–00:06:00　Super Alpha 第一节

### 一、课程背景与目的  

今天课程的目的是帮助所有有资格的consulting同学了解Super Alpha的机制，并鼓励大家积极参与。讲师提到，Super Alpha是独立于Alpha的一个池子，只有50%左右的consultant拥有权限。拥有该权限的同学可以获得更多收益，因为Super Alpha的池子是单独计算的，且不区分Alpha和Super Alpha的绩效。  

讲师还提到，base pay由两部分组成：regular alpha和super alpha，每天最多可以获得120美元。  

### 二、打开Super Alpha界面  

讲师建议所有同学在课程开始前打开Super Alpha界面，并一边听讲一边操作。  

**操作步骤：**  
1. 打开Zoom会议界面。  
2. 找到“会议”选项，点击进入“WJLi的屏幕”或“共享”功能。  
3. 确认Super Alpha界面已打开，可以查看base pay的结构。  

**讲师理由：**  
讲师希望通过实际操作帮助大家理解Super Alpha的界面和功能，以便后续操作时更加熟练。  

### 三、Base Pay结构与数值说明  

讲师在〔画面 00:03:10〕中展示了base pay的结构，包括两个池子：Alpha和Super Alpha。  

**关键信息：**  
- 每天最多可以获得120美元，其中一部分来自Alpha，一部分来自Super Alpha。  
- Alpha和Super Alpha是分开计算的，不互相影响。  
- 有部分数值被遮蔽，但讲师提到这些数值是用于计算base pay的参考。  

**核对办法：**  
- 可以在Super Alpha界面中查看自己的base pay结构，确认是否包含Alpha和Super Alpha两部分。  
- 如果数值被遮蔽，可以联系平台支持获取更多信息。  

### 四、数据核查与回测  

讲师提到，Super Alpha的绩效是独立计算的，且不区分Alpha和Super Alpha的绩效。因此，拥有Super Alpha权限的同学可以更轻松地获得收益。  

**操作建议：**  
- 如果你有Super Alpha权限，建议你积极参与，因为这将有助于提升你的base pay。  
- 可以通过回测查看自己的绩效，确认是否符合Super Alpha的条件。  

### 五、复验建议  

1. **检查Super Alpha权限：** 确认自己是否拥有Super Alpha权限，可以通过界面或联系平台支持。  
2. **核对base pay结构：** 确认base pay是否由Alpha和Super Alpha两部分组成，数值是否符合预期。  
3. **回测绩效：** 如果你有Super Alpha权限，可以尝试回测自己的绩效，确认是否符合Super Alpha的条件。  

**注意：** 课程中提到的数值均为示例，实际数值可能有所不同。请以平台实际显示为准。

![本段画面证据 00:03:10](../画面/42/gpu-frame-010.jpg)

*原片 00:03:10 · 本段引用的画面。*

<a id="part-02"></a>
## 00:06:00–00:12:00　Super Alpha 第一节 - 数据核查与表达式回测

### 一、数据核查：consultant的self correlation与base payment关系  

**问题**：如何通过数据核查判断consultant是否具备提升base payment的潜力？  

**讲师采用的理由**：  
讲师指出，优秀的consultant在不同region中，其self correlation通常控制在0.6以下。如果一个consultant的self correlation长期高于0.6，说明其alpha之间存在高度相关性，无法有效提升base payment。  

**操作或公式走读**：  
- 在BRAIN平台中，查看consultant的self correlation数据，通常在“Key Insights”或“Correlations Avgs.”部分。  
- 若self correlation高于0.6，需警惕其alpha的稳健性。  

**所见结果**：  
- 画面中展示了一些consultant的self correlation数据，其中部分consultant的self correlation接近0.6，而其他则高于0.6。  
- 例如，〔画面 00:06:30〕中提到“SELF-CORR”字段，显示部分consultant的self correlation值。  

**核对办法**：  
- 通过“Key Insights”或“Correlations Avgs.”字段，确认consultant的self correlation是否低于0.6。  
- 若高于0.6，建议优化alpha组合，降低相关性。  

**复验建议**：  
- 可以对比不同consultant的self correlation，判断其alpha的稳健性。  
- 若self correlation过高，可能意味着alpha之间存在重复，需进行筛选或组合。  

### 二、表达式与回测：如何通过表达式提升alpha质量  

**问题**：如何通过表达式与回测提升alpha的稳健性？  

**讲师采用的理由**：  
讲师强调，优秀的consultant会通过表达式与回测来优化alpha，使其在不同市场条件下表现稳定。  

**操作或公式走读**：  
- 在BRAIN平台中，进入“Selection Expression”和“Combo Expression”部分，输入表达式进行回测。  
- 表达式需结合多个信号，如“signals”字段，以提高alpha的多样性。  

**所见结果**：  
- 画面中展示了一个表达式输入界面，其中包含“signals”字段和“generate_stats()”函数。  
- 〔画面 00:09:30〕中提到“Operator generate_stats()”，用于生成统计信息。  

**核对办法**：  
- 在“Selection Expression”中输入表达式，如“signals[〈数值待核〉] + signals[〈数值待核〉]”，并进行回测。  
- 使用“generate_stats()”函数生成统计信息，判断alpha的稳定性。  

**复验建议**：  
- 可以尝试不同的表达式组合，观察其在不同市场条件下的表现。  
- 若回测结果不稳定，需调整表达式或增加信号数量。  

### 三、数据核查与表达式回测的结合  

**问题**：如何结合数据核查与表达式回测提升alpha质量？  

**讲师采用的理由**：  
讲师指出，优秀的consultant会同时关注数据核查和表达式回测，以确保alpha的稳健性和多样性。  

**操作或公式走读**：  
- 在“Key Insights”中查看consultant的self correlation和base payment数据。  
- 在“Selection Expression”中输入表达式，并进行回测。  

**所见结果**：  
- 画面中展示了一个consultant的self correlation和base payment数据，其中self correlation低于0.6，base payment较高。  
- 〔画面 00:06:50〕中提到“Submit more SuperAlphas”，说明提交高质量alpha可以提升base payment。  

**核对办法**：  
- 通过“Key Insights”和“Cor,relations Avgs.”字段，确认consultant的self correlation是否低于0.6。  
- 在“Selection Expression”中输入表达式，并进行回测，确保alpha的稳定性。  

**复验建议**：  
- 可以结合数据核查和表达式回测，优化alpha的稳健性和多样性。  
- 若self correlation过高，需调整表达式或增加信号数量。  

### 四、失败现象与核对办法  

**问题**：如何避免提交SuperAlpha时的失败？  

**讲师采用的理由**：  
讲师指出，提交SuperAlpha时需注意描述字段，否则可能导致失败。  

**操作或公式走读**：  
- 在提交SuperAlpha时，必须填写“description”字段。  
- 使用“Check Submission”按钮，确保SuperAlpha通过所有测试。  

**所见结果**：  
- 画面中展示了一个提交界面，其中“description”字段为空，导致提交失败。  
- 〔画面 00:11:50〕中提到“Write descriptions for your selection expr”，说明描述字段的重要性。  

**核对办法**：  
- 在提交SuperAlpha前，填写“description”字段，并使用“Check Submission”按钮验证。  
- 确保所有测试通过后再提交。  

**复验建议**：  
- 可以尝试提交SuperAlpha时填写描述字段，观察是否成功。  
- 若提交失败，检查是否填写了“description”字段。  

### 五、总结  

**问题**：如何通过数据核查与表达式回测提升alpha质量？  

**讲师采用的理由**：  
讲师总结，优秀的consultant会通过数据核查和表达式回测，确保alpha的稳健性和多样性，从而提升base payment。  

**操作或公式走读**：  
- 在“Key Insights”中查看consultant的self correlation和base payment数据。  
- 在“Selection Expression”中输入表达式，并进行回测。  

**所见结果**：  
- 画面中展示了一个consultant的self correlation和base payment数据，其中self correlation低于0.6，base payment较高。  
- 〔画面 00:06:50〕中提到“Submit more SuperAlphas”，说明提交高质量alpha可以提升base payment。  

**核对办法**：  
- 通过“Key Insights”和“Correlations Avgs.”字段，确认consultant的self correlation是否低于0.6。  
- 在“Selection Expression”中输入表达式，并进行回测，确保alpha的稳定性。  

**复验建议**：  
- 可以结合数据核查和表达式回测，优化alpha的稳健性和多样性。  
- 若self correlation过高，需调整表达式或增加信号数量。

![本段画面证据 00:06:30](../画面/42/gpu-frame-020.jpg)

*原片 00:06:30 · 本段引用的画面。*

<a id="part-03"></a>
## 00:12:00–00:18:00　Super Alpha第一节

### 一、Super Alpha的description要求  

**问题**：在Super Alpha中是否必须填写description？  
**讲师采用的理由**：是的，description是Super Alpha提交和检查的必要条件。  
**操作或公式走读**：在Super Alpha的创建过程中，必须填写description字段，否则无法进行check和submit操作。  
**所见结果**：讲师在〔语音 00:12:00〕中明确指出，不写description会导致无法check和submit。  
**核对办法**：在Super Alpha的创建界面中，description字段是必填项，未填写将无法提交。  

**失败现象**：未填写description会导致无法提交Super Alpha，系统会提示错误。  

**复验建议**：在创建Super Alpha时，务必填写description，以确保提交和检查流程顺利进行。  

### 二、Selection的设置与限制  

**问题**：Selection的最小和最大数量是多少？  
**讲师采用的理由**：Selection的最小数量是10，最大数量是500。  
**操作或公式走读**：在Super Alpha的设置中，Selection的最小数量为10，最大数量为500。  
**所见结果**：讲师在〔语音 00:14:00〕中提到，Selection的最小数量是10，最大数量是500。  
**核对办法**：在Super Alpha的界面中，Selection的最小数量为10，最大数量为500。  

**失败现象**：如果选择的策略数量不足10或超过500，系统会提示错误。  

**复验建议**：在创建Super Alpha时，注意Selection的数量限制，合理选择策略。  

### 三、Selection Handling的设置  

**问题**：Selection Handling的设置有哪些选项？  
**讲师采用的理由**：Selection Handling的设置包括Positive和Non-Zero两种选项。  
**操作或公式走读**：在Super Alpha的设置中，Selection Handling的选项包括Positive和Non-Zero。  
**所见结果**：讲师在〔语音 00:15:00〕中提到，Selection Handling的选项包括Positive和Non-Zero。  
**核对办法**：在Super Alpha的界面中，Selection Handling的选项包括Positive和Non-Zero。  

**失败现象**：如果未正确设置Selection Handling，可能导致策略选择错误。  

**复验建议**：在创建Super Alpha时，根据需求选择合适的Selection Handling选项。  

### 四、Selection Expression的使用  

**问题**：Selection Expression的作用是什么？  
**讲师采用的理由**：Selection Expression用于选择哪些策略被包含在Super Alpha中。  
**操作或公式走读**：在Super Alpha的设置中，Selection Expression用于选择策略。  
**所见结果**：讲师在〔语音 00:16:00〕中提到，Selection Expression用于选择策略。  
**核对办法**：在Super Alpha的界面中，Selection Expression用于选择策略。  

**失败现象**：如果未正确设置Selection Expression，可能导致策略选择错误。  

**复验建议**：在创建Super Alpha时，根据需求设置合适的Selection Expression。  

### 五、Selection Limit的设置  

**问题**：Selection Limit的作用是什么？  
**讲师采用的理由**：Selection Limit用于确定选择的策略数量。  
**操作或公式走读**：在Super Alpha的设置中，Selection Limit用于确定选择的策略数量。  
**所见结果**：讲师在〔画面 00:13:50〕中提到，Selection Limit用于确定选择的策略数量。  
**核对办法**：在Super Alpha的界面中，Selection Limit用于确定选择的策略数量。  

**失败现象**：如果未正确设置Selection Limit，可能导致策略数量超出限制。  

**复验建议**：在创建Super Alpha时，根据需求设置合适的Selection Limit。  

### 六、Selection的运行时间  

**问题**：Selection运行时间如何？  
**讲师采用的理由**：Selection运行时间取决于选择的策略数量，通常在〈数值待核〉到10分钟之间。  
**操作或公式走读**：在Super Alpha的设置中，Selection运行时间取决于选择的策略数量。  
**所见结果**：讲师在〔语音 00:14:30〕中提到，Selection运行时间通常在〈数值待核〉到10分钟之间。  
**核对办法**：在Super Alpha的界面中，Selection运行时间取决于选择的策略数量。  

**失败现象**：如果选择的策略数量过多，可能导致运行时间过长。  

**复验建议**：在创建Super Alpha时，合理选择策略数量，避免运行时间过长。  

### 七、Selection的优化技巧  

**问题**：如何优化Selection的运行时间？  
**讲师采用的理由**：可以先选择少量策略进行测试，再逐步增加数量。  
**操作或公式走读**：在Super Alpha的设置中，可以先选择少量策略进行测试，再逐步增加数量。  
**所见结果**：讲师在〔语音 00:15:00〕中提到，可以先选择少量策略进行测试，再逐步增加数量。  
**核对办法**：在Super Alpha的界面中，可以先选择少量策略进行测试，再逐步增加数量。  

**失败现象**：如果直接选择大量策略，可能导致运行时间过长。  

**复验建议**：在创建Super Alpha时，先选择少量策略进行测试，再逐步增加数量。

![本段画面证据 00:13:50](../画面/42/gpu-frame-042.jpg)

*原片 00:13:50 · 本段引用的画面。*

<a id="part-04"></a>
## 00:18:00–00:24:00　数据核查与表达式回测

### 一、selection handling的逻辑与零值处理

〔语音 00:18:00〕中讲师指出，当使用`if else`表达式时，若`turnover`大于零，则所有alpha都会被标记为零。这说明系统在处理表达式结果时，会将零值视为无效，从而影响最终的selection。此时，有同学提出疑问，认为零值在布尔逻辑中应为false，但讲师解释，这里的零值是用于处理selection的特殊情况。

讲师进一步说明，`selection handling`的作用是处理表达式结果为零的情况。例如，当设置为`positive`时，只有表达式结果为正数的alpha才会被选中；而设置为`non-zero`时，只要表达式结果不为零，alpha就会被选中。

### 二、selection handling的设置与结果验证

〔语音 00:18:30〕中讲师演示了如何通过修改selection handling的设置来选择alpha。当设置为`zero`时，所有alpha都会被标记为零，导致无法选中任何alpha。但当设置为`non-zero`时，系统会选中所有非零值的alpha。

〔语音 00:19:00〕中讲师进一步解释，`non-zero`意味着只判断正负，零值会被忽略。因此，只有表达式结果为正数或负数的alpha才会被选中。讲师还提到，`selection handling`的设置会直接影响最终的selection结果。

### 三、表达式与回测操作

〔语音 00:20:30〕中讲师要求学员在平台中运行selection表达式，并观察结果。当表达式为`turnover`时，系统会选中前30个turnover最高的alpha。讲师指出，如果所有alpha都被选中，可能是由于alpha数量少于30个，此时可以调整limit参数。

〔语音 00:21:00〕中讲师强调，limit参数决定了选中alpha的数量，而表达式`turnover`的含义是选前30个turnover最高的alpha。学员可以通过调整limit参数来控制选中alpha的数量。

### 四、selection handling的设置与结果验证

〔语音 00:21:30〕中讲师建议学员通过实际操作来感受selection handling的设置对结果的影响。当设置为`positive`时，系统会选中所有正数的alpha；当设置为`non-zero`时，系统会选中所有非零值的alpha。

〔语音 00:22:30〕中讲师进一步解释，`non-zero`意味着只要表达式结果不为零，alpha就会被选中。因此，只要alpha不被标记为零，就会被选中。

### 五、selection handling的设置与结果验证

〔语音 00:23:00〕中讲师指出，selection handling的设置会影响最终的selection结果。当设置为`positive`时，系统会选中所有正数的alpha；当设置为`non-zero`时，系统会选中所有非零值的alpha。

〔语音 00:23:30〕中讲师提到，如果设置为`positive`，系统会选中所有正数的alpha；如果设置为`non-zero`，系统会选中所有非零值的alpha。因此，selection handling的设置对最终结果有直接影响。

### 六、复验建议

1. **验证selection handling的设置**：确保设置为`positive`或`non-zero`，以正确筛选alpha。
2. **检查表达式结果**：确保表达式结果为正数或非零值，以避免零值被忽略。
3. **调整limit参数**：根据实际需求调整limit参数，以控制选中alpha的数量。
4. **实际操作验证**：通过实际操作验证selection handling的设置对结果的影响。

通过以上步骤，学员可以正确理解selection handling的逻辑，并有效设置表达式以进行回测。

![Selection Handling 区别 Positive、Non-Zero 与 Non-NaN](../画面/42/00-22-50-frame-069.jpg)

*原片 00:22:50 · Selection Handling 区别 Positive、Non-Zero 与 Non-NaN*

<a id="part-05"></a>
## 00:24:00–00:30:00　数据核查与表达式设置

### 一、selection handling与selection limit的设置  

在WorldQuant BRAIN中，selection handling和selection limit是两个关键参数，它们决定了如何筛选和限制alpha的选取。  

**selection handling** 是用来指定你希望选择的是哪些alpha的值。例如，如果你选择的是“positive”，那么系统会只选择那些计算结果为正数的alpha。但要注意的是，如果计算结果是0或复数，那么这些alpha将不会被选中。因此，你需要确保你的表达式计算出来的值是符合你预期的。  

**selection limit** 是用来限制你最多选择多少个alpha。例如，如果你设置为20，那么系统会从所有符合条件的alpha中选择前20个。  

**操作步骤**：  
1. 打开你的SuperAlpha项目，进入selection部分。  
2. 在selection handling中选择“positive”或“negative”等选项，确保你选择的是你想要的值类型。  
3. 设置selection limit为一个合理的数字，例如20。  

**结果**：  
- 如果你选择的是“positive”，那么系统会只选择那些计算结果为正数的alpha。  
- 如果你设置selection limit为20，那么系统会从所有符合条件的alpha中选择前20个。  

**核对办法**：  
- 检查selection handling是否设置为正确的值类型（如positive、negative等）。  
- 确认selection limit是否设置为一个合理的数字，如20。  

### 二、selection handling的设置与结果  

在〔语音 00:24:00〕中，讲师提到，如果selection handling设置为positive，那么系统会只选择那些计算结果为正数的alpha。如果计算结果是0或复数，那么这些alpha将不会被选中。  

**操作步骤**：  
1. 在selection handling中选择“positive”。  
2. 确认你的表达式计算出来的值是否为正数。  

**结果**：  
- 如果你的表达式计算出来的值是正数，那么这些alpha会被选中。  
- 如果你的表达式计算出来的值是0或复数，那么这些alpha将不会被选中。  

**核对办法**：  
- 检查你的表达式是否计算出正确的值类型（如正数、负数等）。  
- 确认selection handling是否设置为正确的值类型。  

### 三、selection limit的设置与结果  

在〔语音 00:27:30〕中，讲师提到，selection limit是用来限制你最多选择多少个alpha。例如，如果你设置为20，那么系统会从所有符合条件的alpha中选择前20个。  

**操作步骤**：  
1. 在selection limit中设置一个合理的数字，如20。  
2. 确认你的表达式是否计算出正确的值类型（如正数、负数等）。  

**结果**：  
- 如果你的表达式计算出来的值是正数，那么这些alpha会被选中。  
- 如果你的表达式计算出来的值是0或复数，那么这些alpha将不会被选中。  

**核对办法**：  
- 检查selection limit是否设置为一个合理的数字，如20。  
- 确认你的表达式是否计算出正确的值类型（如正数、负数等）。  

### 四、selection handling与selection limit的综合应用  

在〔语音 00:27:30〕中，讲师提到，selection handling和selection limit是两个关键参数，它们决定了如何筛选和限制alpha的选取。  

**操作步骤**：  
1. 在selection handling中选择“positive”。  
2. 在selection limit中设置一个合理的数字，如20。  

**结果**：  
- 如果你的表达式计算出来的值是正数，那么这些alpha会被选中。  
- 如果你的表达式计算出来的值是0或复数，那么这些alpha将不会被选中。  

**核对办法**：  
- 检查selection handling是否设置为正确的值类型（如positive、negative等）。  
- 确认selection limit是否设置为一个合理的数字，如20。  

### 五、selection handling与selection limit的限制  

在〔语音 00:28:30〕中，讲师提到，如果你选择的alpha太多，可能会超过operator的限制。例如，如果你选择500个alpha，那么这些alpha加起来的operator不能超过8000个。  

**操作步骤**：  
1. 在selection handling中选择“positive”。  
2. 在selection limit中设置一个合理的数字，如20。  

**结果**：  
- 如果你的表达式计算出来的值是正数，那么这些alpha会被选中。  
- 如果你的表达式计算出来的值是0或复数，那么这些alpha将不会被选中。  

**核对办法**：  
- 检查selection handling是否设置为正确的值类型（如positive、negative等）。  
- 确认selection limit是否设置为一个合理的数字，如20。  

### 六、selection handling与selection limit的失败现象  

在〔语音 00:28:30〕中，讲师提到，如果你选择的alpha太多，可能会超过operator的限制。例如，如果你选择500个alpha，那么这些alpha加起来的operator不能超过8000个。  

**操作步骤**：  
1. 在selection handling中选择“positive”。  
2. 在selection limit中设置一个合理的数字，如20。  

**结果**：  
- 如果你的表达式计算出来的值是正数，那么这些alpha会被选中。  
- 如果你的表达式计算出来的值是0或复数，那么这些alpha将不会被选中。  

**核对办法**：  
- 检查selection handling是否设置为正确的值类型（如positive、negative等）。  
- 确认selection limit是否设置为一个合理的数字，如20。  

### 七、selection handling与selection limit的验证  

在〔画面 00:24:10〕中，讲师提到，selection handling的设置决定了你选择的是哪些alpha的值，例如“positive”会只选择正数的alpha，而“-turnover”则会只选择负数的alpha。  

**操作步骤**：  
1. 在selection handling中选择“positive”或“-turnover”等选项。  
2. 确认你的表达式计算出来的值是否符合你选择的类型。  

**结果**：  
- 如果你的表达式计算出来的值是正数，那么这些alpha会被选中。  
- 如果你的表达式计算出来的值是负数，那么这些alpha会被选中。  

**核对办法**：  
- 检查selection handling是否设置为正确的值类型（如positive、negative等）。  
- 确认你的表达式是否计算出正确的值类型（如正数、负数等）。

![本段画面证据 00:24:10](../画面/42/gpu-frame-073.jpg)

*原片 00:24:10 · 本段引用的画面。*

<a id="part-06"></a>
## 00:30:00–00:36:00　Super Alpha第一节

### 一、数据核查与datafield限制  

在Super Alpha功能中，数据核查是第一步。讲师提到，如果想选出一个“纯粹”的alpha，它只能使用特定的datafield，比如fundamental 6。但要注意，仅仅选择fundamental 6并不足够，因为系统可能会自动引入其他数据字段，从而导致alpha中混入了其他信号。  

**问题**：如何确保alpha只使用指定的datafield？  
**讲师采用的理由**：通过设置`datasets count`为1，可以限制alpha只能使用一个数据集，从而避免引入其他数据字段。  
**操作或公式走读**：在选择alpha时，需要在表达式中加入`datasets count == 1`，以确保alpha只使用一个数据集。  
**所见结果**：当设置`datasets count == 1`后，系统会筛选出只使用一个数据集的alpha。  
**核对办法**：在回测结果中检查alpha是否只使用了指定的datafield，可以通过查看回测报告中的数据来源部分。  
**引用证据**：〔语音 00:31:00〕  

### 二、防止混信号的策略  

讲师提到，有些alpha可能会混入其他信号，因此需要设置一些限制条件，比如`datafield count`或`loan counts`。  

**问题**：如何防止alpha中混入其他信号？  
**讲师采用的理由**：通过设置`datafield count == 1`，可以确保alpha只使用一个数据字段，从而避免混入其他信号。  
**操作或公式走读**：在表达式中加入`datafield count == 1`，以确保alpha只使用一个数据字段。  
**所见结果**：当设置`datafield count == 1`后，系统会筛选出只使用一个数据字段的alpha。  
**核对办法**：在回测报告中检查alpha是否只使用了指定的数据字段。  
**引用证据**：〔语音 00:31:00〕  

### 三、loan counts与sor counts的平衡  

讲师提到，正常alpha的`loan counts`和`sor counts`应该是相对平衡的，但有些alpha可能会有单边风险，因此需要筛选掉这些alpha。  

**问题**：如何筛选出具有单边风险的alpha？  
**讲师采用的理由**：通过设置`loan counts`或`sor counts`的阈值，可以筛选出具有单边风险的alpha。  
**操作或公式走读**：在表达式中加入`loan counts > X`或`sor counts > Y`，以筛选出具有单边风险的alpha。  
**所见结果**：当设置`loan counts > X`后，系统会筛选出具有单边风险的alpha。  
**核对办法**：在回测报告中检查alpha的`loan counts`和`sor counts`是否符合预期。  
**引用证据**：〔语音 00:31:30〕  

### 四、turnover的筛选  

讲师提到，`turnover`是一个有趣的指标，可以用来筛选alpha。  

**问题**：如何利用`turnover`筛选alpha？  
**讲师采用的理由**：通过设置`turnover`的阈值，可以筛选出具有高或低turnover的alpha。  
**操作或公式走读**：在表达式中加入`turnover > X`或`turnover < Y`，以筛选出具有高或低turnover的alpha。  
**所见结果**：当设置`turnover > X`后，系统会筛选出具有高turnover的alpha。  
**核对办法**：在回测报告中检查alpha的`turnover`是否符合预期。  
**引用证据**：〔语音 00:33:30〕  

### 五、验证与反例  

**反例**：如果alpha的`datasets count`不等于1，可能会引入其他数据字段，导致alpha不纯粹。  
**验证步骤**：在回测报告中检查alpha的数据来源，确保只使用了指定的数据字段。  

**失败现象**：如果alpha的`loan counts`或`sor counts`不平衡，可能会导致alpha具有单边风险。  
**验证步骤**：在回测报告中检查alpha的`loan counts`和`sor counts`是否符合预期。  

### 六、复验建议  

- **检查datafield count**：确保alpha只使用了一个数据字段。  
- **检查loan counts与sor counts**：确保alpha的`loan counts`和`sor counts`相对平衡。  
- **检查turnover**：确保alpha的`turnover`符合预期。  
- **回测验证**：通过回测报告确认alpha是否符合预期。  

### 七、对照表  

| 项目 | 描述 | 设置 | 示例 |
|------|------|------|------|
| datasets count | 限制alpha使用的数据集数量 | 设置为1 | `datasets count == 1` |
| datafield count | 限制alpha使用的数据字段数量 | 设置为1 | `datafield count == 1` |
| loan counts | 限制alpha的贷款数量 | 设置为X | `loan counts > X` |
| sor counts | 限制alpha的sor数量 | 设置为Y | `sor counts > Y` |
| turnover | 限制alpha的turnover | 设置为Z | `turnover > Z` |

<a id="part-07"></a>
## 00:36:00–00:42:00　Super Alpha 第一节 - 数据核查与表达式回测

### 一、数据核查与 Alpha 属性选择  

在课程中，讲师首先强调了在 WorldQuant BRAIN 平台上进行 Alpha 筛选时，需要对数据进行核查。〔语音 00:36:00〕 中提到，某些 Alpha 的 Performance 一般，Turn Over 也无法通过，但其 Idea 仍具有研究价值。这说明在数据核查阶段，不能仅凭 Performance 或 Turn Over 来判断 Alpha 的质量，而是需要结合其他属性进行综合评估。

讲师随后提到，UniverseSize 可以帮助用户构建多个 Universe，例如 Top500、Top3000、Top2000 等，这为 Alpha 的筛选提供了更多维度。〔语音 00:36:30〕 中还提到，Self Correlation、颇大 Correlation、Data Field Counts、Data Category Counts 等属性都可以作为筛选条件，这表明在数据核查阶段，用户可以根据自己的策略选择不同的属性进行筛选。

### 二、Alpha 属性与筛选表达式  

在 〔画面 00:36:10〕 和 〔画面 00:36:30〕 中，讲师展示了 Alpha 属性的列表，包括 `neutralization`、`datafields`、`dataset_count` 等。这些属性可以用于构建 Selection 表达式，从而筛选出符合特定条件的 Alpha。例如，`neutralization` 属性用于中性化设置，`datafields` 属性用于描述 Alpha 使用的数据字段。

讲师还提到，某些 Alpha 可能不包含所有属性，因此在使用时需要注意数据的可用性。〔画面 00:36:50〕 中展示了 `datafields` 属性的使用示例，如 `in(datafields, "returns")`，这表示筛选出使用 "returns" 字段的 Alpha。

### 三、筛选表达式与 Selection Handling  

在 〔语音 00:37:00〕 中，讲师提到，用户可以通过设置不同的 Selection Handling 来筛选 Alpha，例如选择 `颇大 Correlation` 或 `Alpha Year Yield Rate`。用户还可以通过排序方式选择最高产或最低产的 Consultant。

在 〔语音 00:38:30〕 中，讲师演示了如何通过设置 Selection Handling 来筛选 Alpha。例如，设置 `Non Handling` 时，只能选择前 10 个或后 10 个 Alpha，而无法选择中间的。讲师指出，用户可以通过使用 `Rank` 或 `Operator` 来实现更灵活的筛选。

### 四、操作与验证建议  

讲师在 〔语音 00:40:00〕 中要求用户进行练习，设置 Selection 表达式并运行模拟。用户需要思考如何选择 Alpha，并通过模拟验证结果。〔语音 00:40:30〕 中提到，用户可以尝试将 Selection Handling 改为其他方式，观察结果是否变化。

### 复验建议  

1. **验证 Alpha 属性是否可用**：在使用 `neutralization`、`datafields` 等属性时，需确认 Alpha 是否包含这些字段，避免因数据缺失导致筛选失败。  
2. **测试不同 Selection Handling 设置**：尝试将 Selection Handling 设置为 `Non`、`All` 等，观察筛选结果是否变化，以验证筛选逻辑的正确性。  
3. **使用 Rank 或 Operator 进行排序**：通过 `Rank` 或 `Operator` 实现更灵活的排序，例如选择中间的 Alpha，以提高筛选的多样性。  
4. **模拟验证筛选结果**：在设置好 Selection 表达式后，运行模拟并查看返回的 Alpha 列表，确认是否符合预期。  

通过以上步骤，用户可以更系统地进行 Alpha 筛选，并确保筛选逻辑的准确性。

![按 Turnover 选入 Alpha 并用等权作为基线](../画面/42/00-40-30-frame-122.jpg)

*原片 00:40:30 · 按 Turnover 选入 Alpha 并用等权作为基线*

<a id="part-08"></a>
## 00:42:00–00:43:58　数据核查

### 一、模拟界面与数据核查  
〔语音 00:43:30〕 中，讲师提到“你已经点 simulate”，说明学员已进入模拟环境。此时，界面显示“Simulation SuperAlpha 〔数值回看〕”，表明当前处于一个带有数值回看功能的模拟环境。  
- **界面标签**：`Simulation SuperAlpha`、原片代码参数待核、`Selection`、`View all`、`selected alpha pool`、`anonymous`、`TOP3000`  
- **字段**：`Name`、`Universe`、`Sharpe`、`Turnover`、`Fitness`、`Returns`、`Margin`、`selected alpha pool`、`anonymous`、`TOP3000`  
- **功能说明**：原片代码参数待核，表明数值回看功能在选择过程中可以提供不同的视角或数据支持。

### 二、数据核查的初步操作  
- **操作**：学员在模拟环境中点击 `simulate`，进入数据核查阶段。  
- **结果**：界面显示 `Selection: turnover*short count`，表明当前选择的策略是基于 `turnover*short count` 的组合。  
- **核对办法**：学员可通过点击 `View all` 查看所有选择的 alpha 策略，或通过 `selected alpha pool` 查看已选策略池。

### 三、数据回看功能的使用  
- **功能说明**：原片代码参数待核 功能允许学员查看历史数据，以验证当前策略的表现。  
- **字段说明**：`Sharpe` 表示夏普比率，`Turnover` 表示换手率，`Returns` 表示收益率，`Margin` 表示保证金。  
- **操作建议**：学员可通过点击 原片代码参数待核 查看具体数值，以确认当前策略的回测表现。

### 四、数据核查的注意事项  
- **字段限制**：`anonymous` 和 `TOP3000` 是数据池的标签，学员需注意区分不同数据池的使用场景。  
- **数值限制**：所有数值均为课堂示例，不得用于实际交易。  
- **失败现象**：若学员未正确点击 `simulate`，则无法进入数据核查阶段，界面将显示错误提示。

### 复验建议  
- 学员可尝试在模拟环境中点击 `simulate`，观察是否进入数据核查界面。  
- 若界面未显示 `Selection: turnover*short count`，则需检查是否已正确选择策略。  
- 学员可通过 `View all` 查看所有选择的 alpha 策略，并通过 原片代码参数待核 功能验证数据准确性。
