from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

FRAME_MODULO = 1024
SLOT_MODULO = 20
DEFAULT_TASK_COL = "pusch_detection_frontend_task_work_sum_cost"
ORDERED_STATES = ["NO_CACHE", "LOW", "MED", "XXHIGH"]
STATE_TO_ID = {state: idx for idx, state in enumerate(ORDERED_STATES)}


def normalize_state(value: Any) -> str:
    label = str(value or "").upper()
    if "NO_CACHE" in label or "NOCACHE" in label:
        return "NO_CACHE"
    if label.startswith("LOW"):
        return "LOW"
    if label.startswith("MED"):
        return "MED"
    if "XXHIGH" in label:
        return "XXHIGH"
    return label


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def read_csv_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        print(f"[WARN] no rows to write: {path}")
        return
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def add_absolute_frame(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    wrap_count = 0
    last_frame: Optional[int] = None

    def sort_key(row: Dict[str, Any]) -> Tuple[int, int, int]:
        row_id = to_int(row.get("id"))
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        return (
            row_id if row_id is not None else 10**12,
            frame if frame is not None else -1,
            slot if slot is not None else -1,
        )

    for row in sorted(rows, key=sort_key):
        frame = to_int(row.get("frame"))
        slot = to_int(row.get("slot"))
        if frame is None or slot is None:
            continue
        if last_frame is not None and frame < last_frame and (last_frame - frame) > (FRAME_MODULO // 2):
            wrap_count += 1
        last_frame = frame
        abs_frame = wrap_count * FRAME_MODULO + frame
        new_row = dict(row)
        new_row["abs_frame"] = abs_frame
        new_row["abs_slot"] = abs_frame * SLOT_MODULO + slot
        out.append(new_row)
    return out


def row_matches_filters(row: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        if expected is None:
            continue
        raw = row.get(key)
        if isinstance(expected, int):
            actual = to_int(raw)
        elif isinstance(expected, float):
            actual = to_float(raw)
        else:
            actual = str(raw)
        if actual != expected:
            return False
    return True


def aggregate_slot_task(
    input_paths: Sequence[str],
    task_col: str,
    label_col: str,
    filters: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for path in input_paths:
        for row in add_absolute_frame(read_csv_rows(path)):
            if not row_matches_filters(row, filters):
                continue
            task = to_float(row.get(task_col))
            frame = to_int(row.get("frame"))
            slot = to_int(row.get("slot"))
            abs_frame = to_int(row.get("abs_frame"))
            abs_slot = to_int(row.get("abs_slot"))
            label = normalize_state(row.get(label_col, ""))
            if (
                task is None
                or frame is None
                or slot is None
                or abs_frame is None
                or abs_slot is None
                or label not in STATE_TO_ID
            ):
                continue
            rows.append(
                {
                    "input_file": str(path),
                    "abs_frame": abs_frame,
                    "frame": frame,
                    "slot": slot,
                    "abs_slot": abs_slot,
                    "task_work_sum": task,
                    "row_count": 1,
                    "mcs": to_int(row.get("mcs")),
                    "nb_rb": to_int(row.get("nb_rb")),
                    "nb_symbol": to_int(row.get("nb_symbol")),
                    "true_state": label,
                    "true_state_id": STATE_TO_ID[label],
                }
            )
    if not rows:
        return pd.DataFrame()
    raw = pd.DataFrame(rows)
    group_cols = ["input_file", "abs_frame", "frame", "slot", "abs_slot"]
    grouped = (
        raw.groupby(group_cols, as_index=False)
        .agg(
            task_work_sum=("task_work_sum", "sum"),
            row_count=("row_count", "sum"),
            mcs=("mcs", "first"),
            nb_rb=("nb_rb", "first"),
            nb_symbol=("nb_symbol", "first"),
            true_state=("true_state", "first"),
            true_state_id=("true_state_id", "first"),
        )
        .sort_values(["input_file", "abs_slot"])
        .reset_index(drop=True)
    )
    return grouped


def linear_weights(window_frames: int) -> np.ndarray:
    return np.arange(1, window_frames + 1, dtype=float)


def exp_weights(window_frames: int, decay: float) -> np.ndarray:
    return np.array([decay ** i for i in range(window_frames - 1, -1, -1)], dtype=float)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    total = weights.sum()
    if total <= 0:
        return float(np.quantile(values, q))
    cutoff = q * total
    cumsum = np.cumsum(weights)
    idx = int(np.searchsorted(cumsum, cutoff, side="left"))
    idx = min(idx, len(values) - 1)
    return float(values[idx])


def compute_feature(
    values: np.ndarray,
    weights: np.ndarray,
    feature: str,
) -> float:
    if feature == "last":
        return float(values[-1])
    if feature == "mean":
        return float(values.mean())
    if feature == "weighted_mean":
        return float(np.average(values, weights=weights))
    if feature == "median":
        return float(np.median(values))
    if feature == "p90":
        return float(np.quantile(values, 0.9))
    if feature == "weighted_p90":
        return weighted_quantile(values, weights, 0.9)
    if feature == "max":
        return float(values.max())
    raise ValueError(f"unknown feature: {feature}")


def add_scores(
    df: pd.DataFrame,
    window_frames: int,
    weight_mode: str,
    feature: str,
    decay: float = 0.5,
    min_frames: int = 1,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    if weight_mode == "current":
        window_frames = 1
        feature = "last"
        weights = np.array([1.0])
    elif weight_mode == "linear":
        weights = linear_weights(window_frames)
    elif weight_mode == "exp":
        weights = exp_weights(window_frames, decay)
    elif weight_mode == "mean":
        weights = np.ones(window_frames, dtype=float)
    else:
        raise ValueError(f"unknown weight_mode: {weight_mode}")

    records: List[Dict[str, Any]] = []
    for _, group in df.groupby(["input_file", "slot"], sort=False):
        group = group.sort_values("abs_frame")
        value_by_frame = {
            int(row.abs_frame): float(row.task_work_sum)
            for row in group.itertuples(index=False)
        }
        for row in group.itertuples(index=False):
            abs_frame = int(row.abs_frame)
            vals: List[float] = []
            wts: List[float] = []
            for offset in range(window_frames):
                source_frame = abs_frame - (window_frames - 1 - offset)
                value = value_by_frame.get(source_frame)
                if value is None:
                    continue
                vals.append(value)
                wts.append(float(weights[offset]))
            if len(vals) < min_frames:
                continue
            values = np.array(vals, dtype=float)
            row_weights = np.array(wts, dtype=float)
            rec = row._asdict()
            rec["score"] = compute_feature(values, row_weights, feature)
            rec["window_frames"] = window_frames
            rec["window_observed_frames"] = len(vals)
            rec["weight_mode"] = weight_mode
            rec["feature"] = feature
            rec["decay"] = decay if weight_mode == "exp" else ""
            records.append(rec)
    return pd.DataFrame(records)


def predict_from_thresholds(scores: np.ndarray, thresholds: Sequence[float]) -> np.ndarray:
    return np.digitize(scores, thresholds, right=False).astype(int)


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int = 4) -> np.ndarray:
    matrix = np.zeros((n_classes, n_classes), dtype=int)
    for true, pred in zip(y_true, y_pred):
        if 0 <= int(true) < n_classes and 0 <= int(pred) < n_classes:
            matrix[int(true), int(pred)] += 1
    return matrix


def metrics_from_confusion(matrix: np.ndarray) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    total = int(matrix.sum())
    correct = int(np.trace(matrix))
    per_class: List[Dict[str, Any]] = []
    f1s: List[float] = []
    for idx, state in enumerate(ORDERED_STATES):
        tp = int(matrix[idx, idx])
        fp = int(matrix[:, idx].sum() - tp)
        fn = int(matrix[idx, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1s.append(f1)
        per_class.append(
            {
                "state": state,
                "support": int(matrix[idx, :].sum()),
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )
    return {
        "accuracy": correct / total if total else 0.0,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "total": total,
        "correct": correct,
    }, per_class


def confusion_rows(matrix: np.ndarray) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i, state in enumerate(ORDERED_STATES):
        row = {"true_state": state}
        for j, pred_state in enumerate(ORDERED_STATES):
            row[f"pred_{pred_state}"] = int(matrix[i, j])
        rows.append(row)
    return rows


def threshold_candidates(scores: np.ndarray, max_candidates: int) -> np.ndarray:
    unique = np.unique(scores.astype(float))
    if len(unique) <= max_candidates:
        vals = unique
    else:
        qs = np.linspace(0.01, 0.99, max_candidates)
        vals = np.unique(np.quantile(unique, qs))
    if len(vals) <= 1:
        return vals
    mids = (vals[:-1] + vals[1:]) / 2.0
    return np.unique(mids)


def search_ordered_thresholds(
    scores: np.ndarray,
    y_true: np.ndarray,
    max_candidates: int = 80,
) -> Tuple[Dict[str, Any], np.ndarray, List[Dict[str, Any]]]:
    candidates = threshold_candidates(scores, max_candidates)
    if len(candidates) < 3:
        candidates = np.unique(np.quantile(scores, [0.25, 0.5, 0.75]))
    order = np.argsort(scores)
    sorted_scores = scores[order]
    sorted_labels = y_true[order].astype(int)
    prefix = np.zeros((len(sorted_labels) + 1, 4), dtype=int)
    for idx, label in enumerate(sorted_labels, start=1):
        prefix[idx] = prefix[idx - 1]
        if 0 <= label < 4:
            prefix[idx, label] += 1

    positions = np.searchsorted(sorted_scores, candidates, side="left")
    best: Optional[Tuple[Tuple[float, float], Dict[str, Any], np.ndarray, List[Dict[str, Any]]]] = None
    for i in range(len(candidates) - 2):
        t1 = float(candidates[i])
        p1 = int(positions[i])
        for j in range(i + 1, len(candidates) - 1):
            t2 = float(candidates[j])
            p2 = int(positions[j])
            for k in range(j + 1, len(candidates)):
                thresholds = [t1, t2, float(candidates[k])]
                p3 = int(positions[k])
                matrix = np.zeros((4, 4), dtype=int)
                matrix[:, 0] = prefix[p1] - prefix[0]
                matrix[:, 1] = prefix[p2] - prefix[p1]
                matrix[:, 2] = prefix[p3] - prefix[p2]
                matrix[:, 3] = prefix[len(sorted_labels)] - prefix[p3]
                metrics, per_class = metrics_from_confusion(matrix)
                key = (metrics["macro_f1"], metrics["accuracy"])
                if best is None or key > best[0]:
                    row = {
                        "threshold_1": thresholds[0],
                        "threshold_2": thresholds[1],
                        "threshold_3": thresholds[2],
                        **metrics,
                    }
                    best = (key, row, matrix, per_class)
    if best is None:
        raise RuntimeError("failed to find thresholds")
    return best[1], best[2], best[3]


def save_model(path: Path, model: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")


def load_model(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
