# ai-fit-check · 哪件事能交给 AI 做

**一个 5 分钟就能跑完的判据工具，回答一个问题：你手上这件重复活，能不能交给 AI 批量做。**

大多数「AI 能不能替代人工」的讨论都停在感觉上。这个仓库把它压成三条硬闸门 + 两条软闸门，可以跑、可以复核、可以被反驳。

```bash
python audit.py examples/store-inquiry.json
```

```
任务                              判定             月人工h   可省h  原因
顾客咨询回信（营业时间/地址/订餐）  BATCH              22.5    18.0  三条硬闸门全部通过，可批量自动化
每日进货对账（单据↔系统）           HUMAN_REVIEW       17.5     7.0  硬闸门通过，但需人工复核：S1 输入数据可获取
菜品图拍摄与修图                   NOT_BATCHABLE      15.0     0.0  硬闸门未过：G1；G2；G3
差评安抚回复                       NOT_BATCHABLE       8.0     0.0  硬闸门未过：G1；G2；G3
```

## 三条硬闸门（缺一即不可批量）

| 闸门 | 问法 | 反例 |
|---|---|---|
| **G1 有唯一正确答案或可核对的对照** | 做完之后，对错能不能被指出来？ | 「这张图好不好看」没有答案 |
| **G2 失败可被自动检测** | 出错时，机器能不能自己发现？ | 视频剪辑哪一段留、哪一段剪，只能人看 |
| **G3 差异不引发公平感比较** | 结果不一样时，会不会变成人和人之间的比较？ | 每个客户一份定制品 → 客户之间开始比细节 |

三条全过 = 可以批量。任一条不过 = 不要批量，做了也是负期望值。

## 两条软闸门（影响成本，不影响对错）

- **S1 输入数据可获取**：数据拿不到，模型再好也白搭。
- **S2 人工判断占比 ≤ 0.2**：每单里需要人拍板的比例。超了就是「人做，AI 打下手」，不是自动化。

## 为什么要有第三条（G3）

这条最容易被忽略，也最贵。

一个真实反例：给每个学员做一份专属成长视频。生成成本确实趋零，但**验收成本不会趋零**——保留哪段、要不要美颜、细节对不对，全靠人工判断；而且一旦开始比较，客户之间会比细节、比待遇，**争议成本随人头线性增长**。

结论：**生成便宜、验收贵 = 整体不贵不了**。判断一件事能不能放大，不要问生成端，要问验收端。

## 输入字段

```json
{
  "name": "顾客咨询回信",
  "monthly_volume": 900,            // 每月发生次数
  "minutes_per_case": 1.5,          // 每次人工耗时（分钟）
  "g1_objective": true,
  "g2_auto_detectable": true,
  "g3_no_fairness_comparison": true,
  "s1_data_available": true,
  "human_judgement_share": 0.1,     // 0~1
  "regulated": false                // 是否需前置资质（金融/医疗等）
}
```

字段缺失按 `false` 处理——宁可判保守，不判乐观。`regulated: true` 直接 BLOCKED。

## 输出四档

| 判定 | 含义 |
|---|---|
| `BATCH` | 可批量自动化（估省 80% 工时） |
| `HUMAN_REVIEW` | 硬闸门过、需人审（估省 40%） |
| `NOT_BATCHABLE` | 不可批量，理由会写明哪条闸门没过 |
| `BLOCKED` | 合规或数据前置条件缺失，先别谈自动化 |

工时数字是**上限估计**，不是承诺。真实节省以试点为准。

---

## 免费诊断（前 2 家）

工具只能给出粗判。真实业务里的边界条件（数据在哪、谁审、出错谁负责）跑不出来，得看现场。

**前 2 家免费**，我给一份 3–5 页的诊断：

1. 你现有任务里，哪些现在就能接掉、哪些做不了（会明说做不了）
2. 每条判定的依据（哪条闸门、缺什么）
3. 大概成本与工期
4. 第一步该做什么（可执行，不是 PPT）

**条件**：允许我把结果脱敏后当案例讲。不收钱，也不要求你买后续。

**申请**：[开一个 issue](../../issues/new?template=free-diagnosis.yml)，或用 issue 里的模板发我。一周内出结果。

边界：不承诺效果；不接需前置资质的业务；不代你对客户发言。

---

## English

`ai-fit-check` is a tiny, dependency-free tool that tells you whether a repetitive task can be **batch-automated** with AI — before you spend money on it.

Three hard gates: (G1) objective ground truth exists, (G2) failures are machine-detectable, (G3) output variance does not trigger fairness comparisons between people. Fail any one → do not batch it. Two soft gates (data availability, share of human judgement) decide the cost, not the verdict.

The reasoning is documented in [`docs/three-gates.md`](docs/three-gates.md). MIT licensed, no dependencies, no telemetry.

## License

MIT
