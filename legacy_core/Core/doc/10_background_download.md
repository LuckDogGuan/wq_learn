# background_download 数据同步说明

本文对应以下目录和文件：

```text
代码/优化代码/Core/
├── test/background_download.py   # 后台入口，负责循环调用同步流程
├── data/catalog_db.py            # 负责本地 SQLite、数量判断和 upsert
├── api/data_api.py               # 负责从平台获取 datasets/datafields
└── doc/                          # 本说明所在目录
```

## 先说结论

`python background_download.py` 重复运行时：

1. 不会简单地把同一条数据无限追加成多行，因为数据表以 `id` 为主键，并使用 upsert。
2. 数据集列表会在每次运行、每个 Region/Universe 下重新请求一次，然后写入本地表。
3. 字段同步有一个数量门槛：本地字段数量达到平台返回的 `fieldCount` 时跳过该数据集。
4. 本地数量不足时，会重新请求该数据集的完整字段列表。它会把已有字段和新字段一起交给 upsert，而不是只向平台请求“缺失的字段”。
5. 所以要区分两件事：

   - 数据库层面：通常不会产生重复主键行。
   - 网络层面：某个数据集本地不完整时，已有字段也可能随完整列表再次被下载。

## 实际流程

入口脚本 `test/background_download.py` 本身不做“是否已下载”的判断，它只执行：

```text
CatalogDB()
    └─ fetch_all_scopes()
        ├─ 登录并读取平台可用的 Region/Universe
        ├─ 获取当前分区的 datasets 列表
        ├─ datasets_<REGION>_<UNIVERSE> 做 upsert
        └─ 对每个 dataset 判断字段数量
             ├─ local_count >= fieldCount 且 fieldCount > 0：跳过请求
             └─ 否则：请求完整字段列表，再 upsert
```

字段判断使用的是当前分区表中：

```text
SELECT dataset_id, COUNT(id)
FROM datafields_<REGION>_<UNIVERSE>
GROUP BY dataset_id
```

然后比较：

```text
local_count = 本地已经保存的字段行数
expected_count = 平台 datasets 返回的 fieldCount
```

只有下面条件同时成立，才会跳过字段请求：

```text
local_count >= expected_count AND expected_count > 0
```

## “增加”到底发生在哪里

这里的“增加”主要是数据库写入层面的 upsert：

- 数据集表主键是 `id`。
- 字段表主键也是字段 `id`。
- 新 `id` 会插入。
- 已存在的 `id` 会更新已有列。
- `first_written_at` 只在首次插入时保留，`updated_at` 会在再次写入时更新。

因此，重复运行通常不会形成两条相同 `id` 的记录。但“upsert 不重复”不代表“不会重复发起网络请求”。

## 哪些情况会再次下载

以下情况会让某个数据集再次调用字段接口：

- 本地没有该数据集的字段记录。
- 本地字段数量小于平台 `fieldCount`。
- 平台返回的 `fieldCount` 为 `0`，因为当前判断要求 `expected_count > 0` 才允许跳过。
- 本地数据库被删除，或脚本显式连接到了另一个 `catalog.db`。
- 上一次下载中途失败，只保存了部分字段。

字段接口本身按分页获取完整结果；同步层没有把本地已有字段 ID 传给平台作为排除条件。因此“本地少一条”时，当前行为更准确地说是“重新拉取该数据集的字段全集并合并”，不是“只拉取一条缺失字段”。

## 数据库位置要注意

`CatalogDB()` 未显式传入路径时，使用的是当前进程工作目录下的：

```text
Core/runtime_data/catalog.db
```

默认数据库位置固定为 `代码/优化代码/Core/runtime_data/catalog.db`，不再随启动目录变化。判断“为什么这次又下载”时，应确认该固定数据库文件是否存在，以及调用方是否显式传入了其他 `db_path`。

## 失败与重试

`background_download.py` 捕获异常后会等待 5 分钟，再重新调用整个 `fetch_all_scopes()`。因此：

- 失败前已经写入的数据通常会保留。
- 下一轮会重新扫描所有分区和数据集。
- 已经达到数量门槛的数据集会跳过字段请求。
- 仍未达到门槛的数据集会再次请求完整字段列表。
- 这不是按失败数据集精确续跑，而是“重新扫描 + 按数量门槛跳过”的断点方式。

## 当前代码核对时的路径约定

数据库路径由 `Core/data/runtime_paths.py` 统一定义；SC/PPA 缓存路径为 `Core/runtime_data/sc_ppa/`。测试专用的 `Core/tests/test_dummy.db` 仍保持独立，不与真实目录数据库混用。

## 建议的人工核对方法

不修改代码时，可以按下面顺序确认一次运行是否发生了真实字段下载：

1. 查看 `Core/runtime_data/catalog.db` 是否存在。
2. 看日志中是否出现 `Downloading missing fields for ...`。
3. 对照该行的 `local` 和 `expected` 数量。
4. 运行结束时查看 `Skipped ... fully downloaded datasets, fetched ... datasets`。
5. 如果 `fetched` 大于 0，只能说明这些数据集触发了字段请求；不能据此断言只下载了缺失字段。

## 一句话理解

当前实现是“按数量判断是否跳过，数量不足则拉取完整字段列表并按 ID 合并”，不是“先逐条找缺失字段，再只追加缺失数据”。
