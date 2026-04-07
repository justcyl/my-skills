# TikZ 与图表防碰撞规则

编译器不会捕获 TikZ 的视觉错误。你必须自己检查。
以下规则同时适用于 TikZ 图和 matplotlib/Python 生成的图。

## 工作流：Bézier 优先，其余其次

每次创建或编辑含 TikZ 的 deck 后，按顺序执行以下 Pass。不要只检查你刚改的那张 slide——检查整个 deck。

### Pass 0: 跨 slide 一致性

当同一个图/元素出现在多张 slide 上时：

1. **颜色必须一致**：slide 5 中某节点是 Teal，slide 6 中也必须是 Teal
2. **布局必须一致**：相同节点在相同位置、相同间距、相同字号
3. **只有故意的变化才是变化**：如果 slide 6 加了高亮框，那应该是唯一的区别

```bash
# 查找跨 frame 共享的节点名
grep -n "node.*draft\|node.*compile\|node.*inspect" [file].tex
```

### Pass 1: Bézier 曲线碰撞检测

```bash
grep -n "bend" [file].tex
```

对每个弯曲箭头：

1. 识别两个端点和弯曲角度
2. 计算最大曲线深度：`max_depth = (弦长 / 2) × tan(弯曲角 / 2)`
3. 计算安全距离：`safe_distance = max_depth + 0.5cm`
4. 检查曲线附近的每个 label，距离小于 safe_distance 的必须移走
5. 检查曲线是否穿过其他箭头，是则改方向（`bend right` ↔ `bend left`）

常用弯曲角速查：

| 弯曲角 | tan(角/2) | 半弦乘数 |
|--------|-----------|---------|
| 20° | 0.176 | × 0.18 |
| 30° | 0.268 | × 0.27 |
| 40° | 0.364 | × 0.36 |
| 45° | 0.414 | × 0.41 |

若 deck 中无 `bend` 关键词，跳过此 Pass。

### Pass 2: 节点间 label 间隙计算

对每个位于两个节点之间的 label：

```
可用间隙 = 中心距 - 节点A半宽 - 节点B半宽
可用空间 = 可用间隙 - 0.6cm（两侧各 0.3cm padding）
```

估算 label 宽度：

| 字号 | 每字符宽度 |
|------|-----------|
| `\scriptsize` | 0.10cm |
| `\footnotesize` | 0.12cm |
| `\small` | 0.15cm |
| `\normalsize` | 0.18cm |

粗体 +10%，等宽 +15%。中文字符按 2× 西文宽度估算。

**如果 label 宽度 > 可用空间 → 碰撞确认。** 将 label 移到上方/下方，或缩短文字。

### Pass 3: 箭头 label 定位

每个箭头 label 必须有位置关键词：

```latex
% ✅ 正确
\draw[->] (A) -- (B) node[midway, above] {label};

% ❌ 错误（位置不确定）
\draw[->] (A) -- (B) node {label};
```

检查方法：
```bash
grep -n "node\s*{" [file].tex | grep -v "above\|below\|left\|right\|midway\|anchor"
```

输出中排除 `\node[...]` 定义（有 `at` 坐标的），只关注边上的 label。

## 何时跳过

- 无 TikZ 内容的 deck → 跳过全部 Pass
- 无弯曲箭头 → 跳过 Pass 1
- 纯 `\node[...] at (x,y)` 定位（无边 label） → 跳过 Pass 2 和 3
