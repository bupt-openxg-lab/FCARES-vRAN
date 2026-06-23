# concordia_baseline —— Concordia 时延预测器忠实复现与交叉评估

把 Concordia（SIGCOMM'21, *Teaching the 5G vRAN to Share Compute*）的决策树式时延预测
作为**基线**，在本平台两个数据集上忠实复现并交叉评估，与本项目方法
**grouped_linear**（[`../group_linear_model/`](../group_linear_model/)）对比。

---

## 1. Concordia 方法（忠实复现，对应论文 §4.2 + Algorithm 1/2）

Concordia WCET predictor 的算法要素，本目录 `concordia_predictor.py` 逐条复现：

1. **每 task 一棵 quantile decision tree**（CART，minimize-variance 分裂），让落同叶的样本
   runtime 相近。decode / frontend 各一棵。
2. **特征选择（Algorithm 1）**：dcor 距离相关排序选 top-N + 后向消除 + 手选。本实现用
   numpy 手写标准 distance correlation（无 `dcor` 包依赖），产出排序报告
   `out/dcor_feature_ranking.csv`；观测特征仅 5 个、CART 分裂本身已隐式选特征，故默认保留
   全部观测特征。
3. **每叶 ring buffer** B_i，存最近观测 runtime（默认 5000 条，与论文一致）。
4. **WCET 预测 = max(B_i)**（Algorithm 2 Prediction Step），面向 99.999% 可靠。
5. **online 阶段**：用在线样本顺序替换叶内 offline 样本，**不改树结构**，以适应 collocated
   workload 造成的 cache interference（`predict_online`）。

**与本项目 grouped_linear 的两点本质差异（贯穿全部结论）**：
- Concordia 是 **state-agnostic 单棵树**：无显式 state 输入，靠 ring buffer 在线追踪当前
  regime；本项目按 `stress_level` 显式分 state 各训一套。
- Concordia 靠 **每叶查表统计**，对未见 `nb_rb` 无法外推（`tree.apply` 落到最近已有叶 →
  系统性低估）；grouped_linear 在 `nb_rb` 上线性，可外推。

> 注：忠实复现 ≠ 照搬旧代码。`python_scripts_bak/sim_framework/concordia_runtime.py` 是旧的
> ring-buffer 实现，本目录据论文重写、聚焦交叉评估，并修正了旧脚本只看 random split、
> 用文件名当 state 等问题（见 `../bak_inventory_for_integration.md`）。

---

## 2. 文件

| 文件 | 作用 |
|---|---|
| `concordia_predictor.py` | Concordia WCET predictor（CART + dcor 排序 + 每叶 ring-buffer + WCET=max + 在线更新） |
| `grouped_linear_predictor.py` | 对照：per-state CodeBlocks 分组 Ridge + 残差 p70（复用 bak 原语） |
| `common.py` | 两数据集加载（md5 去重 / tb_done=1 / state / nb_rb 分箱）、特征 tier、指标 |
| `evaluate.py` | 主驱动：三类场景交叉评估，产出 `out/results.csv` / `dcor_feature_ranking.csv` / `summary.md` |

运行（仓库根目录）：
```bash
cd python_scripts/concordia_baseline
/home/bupt/wlh/ran/venv/bin/python evaluate.py --out-dir out
```
依赖：venv 自带 sklearn 1.7.2 / numpy / pandas / scipy（`dcor` 包**不需要**，已手写）。

---

## 3. 数据与场景

两数据集列完全一致（99 列），state = `stress_level` ∈ {NO_CACHE, LOW, XXHIGH}（均无 MED）：
- **toy**：7 个固定 PRB 文件（93…273）× 3 态，受控 PRB 扫描（md5 去重后每 PRB 一文件）。
- **integration**：273PRB 实际部署（with_hcs / without_hcs），`nb_rb` 随 HCS 调度变化。

模块：`decode[observable]`（可部署档）、`decode[oracle]`（给 Concordia 加 snr_db+iteration 的
steelman 上界）、`frontend`。三类评估场景：

| 场景 | 含义 |
|---|---|
| S1 within/random | 单数据集随机 75/25（见过的 operating point） |
| S2 within/prb_holdout | 单数据集 leave-one-`nb_rb`-out（**对未见 PRB 外推**）—— 关键区分点 |
| S3 cross_dataset | train toy ↔ test integration 双向（跨采集场景泛化） |

指标：点预测 R²/MAE/RMSE/MAPE；保守(预算)预测 `coverage`=P(实测≤预测)（p70 目标 0.70，
WCET 目标 ~1.0），`overprov_us`=平均过量预留（正=余量，负=系统性欠配），`underprov_us`。

---

## 4. 结果

### 4.1 头条：p70 覆盖率（ALL, decode[observable]，目标 0.70）

| 场景 | concordia(树) | concordia_online | grouped_linear |
|---|---|---|---|
| within/random | 0.697 | — | 0.698 |
| within/prb_holdout（**未见 PRB**） | **0.344** | — | **0.729** |
| cross toy→integration | 0.536 | 0.708 | 0.694 |
| cross integration→toy | 0.570 | 0.686 | 0.566 |

### 4.2 三条结论

**① 见过的 operating point 上，树与线性打平。**
within/random（decode[observable], ALL）：concordia 与 grouped_linear 的 R²、p70 覆盖、
过量预留几乎逐位相同（toy R²=0.914 双方，cov 0.701/0.701；integration R²=0.975，cov 0.692/0.696）。
random split 下树只是查训练见过 nb_rb 的叶统计，缺陷被 per-leaf 记忆掩盖。

**② 对未见 PRB 外推：Concordia 树的保守界塌陷，grouped_linear 守住。**
within/prb_holdout（decode[observable], ALL）p70：

| 数据 | concordia cov / overprov | grouped_linear cov / overprov |
|---|---|---|
| toy | **0.232 / −52.9µs** | 0.709 / +38.5µs |
| integration | **0.455 / −6.3µs** | 0.749 / +36.2µs |

树对未见 nb_rb 落到最近已有叶 → 系统性低估 → p70 过量预留变**负**（欠配），会把 deadline
budget 严重算小；grouped_linear 线性外推，覆盖守在 ~0.70+。

**③ WCET=max（论文真实工作点）保覆盖但巨量过配，且仍无法外推。**
concordia `cons_mode=max`（ALL, decode[observable]）：within/random 覆盖 ~1.0 但平均过配
**303–307µs**；跨数据集 toy→integration 过配 **327µs**。更关键，prb_holdout 下 max 覆盖反而
跌到 0.965/0.970——**连最大值也外推不了**，未见的大 PRB 上真值越过训练叶的 max。即 Concordia
要么巨量浪费预算，要么在未见 PRB 上仍漏配。

**④ 在线 ring-buffer 能救回覆盖，但有代价。**
cross-dataset 下 concordia_online 把 p70 覆盖从 0.54/0.57 拉到 0.69–0.71、R² 也明显回升
（如 cross/integration→toy NO_CACHE：R² 0.875→0.966）。这是 Concordia 的真正强项——在线观测
新 regime 后适应。但它**需先观测到该 regime 的真实 runtime**（warmup 滞后，无法预判 state
切换那一刻），且本质是「用 state 内的在线样本替代显式 state 模型」；grouped_linear 靠线性外推
**离线**即守住覆盖，无 warmup。

### 4.3 cross/integration→toy 的诚实记录
该方向 grouped_linear 在 XXHIGH 也掉点（R²=0.263, cov=0.171）。原因是 integration 各 state 的
PRB 多样性有限（without_hcs 仅 nb_rb∈{5,273}），用它训练再外推到 toy 的 93…273 全扫描偏难——
这是**训练数据覆盖问题**（见 `../group_linear_model/README.md` §4 的 MCS/PRB 缺口），不是方法缺陷；
反向 toy→integration（训练侧 PRB 覆盖好）grouped_linear 守住 0.694。

---

## 5. 结论

在**见过的点**上 Concordia 树与 grouped_linear 等价；一旦要对**未见 PRB 外推**或**跨采集场景
泛化**，离线 Concordia 树系统性欠配（保守界塌陷 / WCET 巨量过配），grouped_linear 凭 `nb_rb`
线性外推守住预算覆盖。Concordia 的在线 ring-buffer 可补救，但需 warmup 观测、无法预判 state
切换。**因此本项目部署 grouped_linear（显式 per-state + 线性外推），以 Concordia 为基线。**

关联：[`../group_linear_model/`](../group_linear_model/) ·
[`../bak_inventory_for_integration.md`](../bak_inventory_for_integration.md) ·
论文 `../../thesis/reference/Concordia:Teaching the 5G vRAN to Share Compute.pdf`
