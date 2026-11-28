# 子代理简报模板（DSH flash）

按 [运行配置](../../goal/run_config.json) 的 `subagent_profile` 通过 `dsh_crew` MCP 探测并派单。同一任务由同一个子代理完成诊断、核验和回报。最多 4 轮，停止派单后保留 DSH 会话及对话。

```text
【任务】<一句话目标>
【工作区】C:\Wq\WorldQuant Brain
【只读证据】<所需绝对路径、批次 ID、母版和对照组>
【验收】<要核对的指标与判定标准、可运行的只读检查>
【回报】直接返回结论、证据位置、验收输出和未验证项，最多 30 行。结论标 [V] 已验证、[R] 有报告未复核、[C] 条件成立或 [U] 未验证。
【文件】默认不写文件。只有派单指定全新路径时才可创建该文件，不覆盖、追加、重命名或删除现有文件。
【边界】不 commit、不 push、不回测、不写平台、不调用 /submit、不读 Password/config.yaml。保护 reference/、legacy_core/Core/runtime_data/ 和 COMPLETED_FULL，遵循项目 D1 与算子约束。
```

主 Agent 独立复核证据，决定方向，承担现有文件修改和账本回写。接到长任务的轻量检查时，只回传运行方式是否符合预期、已完成数、满足条件数和待判定数。
