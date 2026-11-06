"""Probabilistic Intuitive Engine — شبيه بالشبكة العصبية، بدون أي مكتبات خارجية.

هذا المحرك يتعلم من تاريخ المقترحات ويولّد تخمينات سريعة بناءً على الأنماط.
لا يُغذَّى بأي شاهد من المُتحقق (verifier witness) أو إجابة مهمة أو بيانات مخفية.
كل تعلّم يأتي من المشاهدات العامة (probe signatures) فقط.

المكوّنات:
  PatternMemory   — ذاكرة أنماط مؤطرة (تخزن تردد الـ ops والبنى الناجحة)
  NeuralLikeLayer — طبقة وزن احتمالية (تُحدَّث بقانون هبل المبسَّط)
  IntuitiveEngine — المحرك الكامل: يولّد مقترحات مُرجَّحة بدلاً من المنهجية
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from random import Random
from typing import Iterator

from .ir import IRViolation, Limits, canonical_hash, check_tree, run_ir_args
from .search import Proposal, SearchStats, _probe_inputs

# ──────────────────────────────────────────────────────────────────────────────
# الثوابت الداخلية — لا تُكشف للمُتحقق أو لمُولّد المرشحات الأصلي
# ──────────────────────────────────────────────────────────────────────────────
_LEARNING_RATE = 0.15  # معدّل التعلم لكل مشاهدة ناجحة
_DECAY = 0.98  # تخفيف الوزن بعد كل دورة (forgetting)
_MIN_WEIGHT = 0.05  # حدٌّ أدنى لأي وزن (لا تنهار الاحتمالات)
_MAX_DEPTH_BIAS = 3  # الحد الأعمق الذي يُفضَّل في التخمين الحدسي
_INTUITION_VERSION = "cin.intuition/v0.1"


# ──────────────────────────────────────────────────────────────────────────────
# PatternMemory — ذاكرة الأنماط
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class PatternMemory:
    """تخزّن تردد المُشغِّلات (ops) والأعماق وتتبّع البصمات المشاهَدة.

    هذه الذاكرة عامة تمامًا — لا تحتوي على أي بيانات من المُتحقق.
    """

    op_frequency: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    depth_frequency: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    const_frequency: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    seen_signatures: set[tuple] = field(default_factory=set)
    total_observations: int = 0

    def observe(self, expr: dict, probe_values: tuple) -> None:
        """سجّل مشاهدة ناجحة (تجاوزت الفلترة بالبصمة)."""
        self.total_observations += 1
        self._walk_ops(expr)
        depth = self._depth(expr)
        self.depth_frequency[depth] += 1
        self.seen_signatures.add(probe_values)

    def _walk_ops(self, node: dict) -> None:
        op = node.get("op", "")
        self.op_frequency[op] += 1
        for child in node.get("args", []):
            self._walk_ops(child)
        if op == "ConstInt":
            self.const_frequency[node.get("value", 0)] += 1

    def _depth(self, node: dict) -> int:
        children = node.get("args", ())
        if not children:
            return 1
        return 1 + max(self._depth(c) for c in children)

    def op_weights(self, candidates: list[str]) -> list[float]:
        """إرجاع أوزان احتمالية لكل مُشغِّل بناءً على التردد."""
        total = sum(self.op_frequency.get(op, 0) for op in candidates) + len(candidates)
        return [(self.op_frequency.get(op, 0) + 1) / total for op in candidates]

    def preferred_depth(self) -> int:
        """العمق الأكثر ظهورًا في الذاكرة."""
        if not self.depth_frequency:
            return 2
        return min(max(self.depth_frequency, key=self.depth_frequency.get), _MAX_DEPTH_BIAS)

    def preferred_constants(self, allowed: list[int]) -> list[float]:
        """أوزان للثوابت المسموح بها."""
        total = sum(self.const_frequency.get(c, 0) for c in allowed) + len(allowed)
        return [(self.const_frequency.get(c, 0) + 1) / total for c in allowed]


# ──────────────────────────────────────────────────────────────────────────────
# NeuralLikeLayer — طبقة الأوزان الاحتمالية (بدون أي مكتبة ML)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class NeuralLikeLayer:
    """تُحاكي الطبقة المخفية في الشبكة العصبية بأوزان قابلة للتعلم.

    التعلم يتبع قانون هبل المبسَّط:
      w_new = clip(w_old + lr * signal, _MIN_WEIGHT, 1.0)

    ثم يُطبَّق التطبيع (softmax-like) لضمان توزيع احتمالي سليم.
    """

    keys: list[str]
    weights: list[float] = field(init=False)
    _rng: Random = field(default_factory=Random, repr=False)

    def __post_init__(self) -> None:
        n = len(self.keys)
        # تهيئة موحدة مع ضوضاء صغيرة
        self.weights = [1.0 / n + self._rng.uniform(-0.01, 0.01) for _ in range(n)]
        self._normalize()

    def _normalize(self) -> None:
        """Normalize probability weights without reapplying softmax to probabilities."""
        if not self.weights:
            raise ValueError("At least one sampling key is required")
        floor = min(_MIN_WEIGHT, 1.0 / len(self.weights))
        mass = [max(0.0, value) for value in self.weights]
        total = sum(mass)
        if total == 0:
            mass = [1.0] * len(mass)
            total = len(mass)
        remaining = 1.0 - floor * len(mass)
        self.weights = [floor + remaining * value / total for value in mass]

    def reinforce(self, key: str, signal: float = 1.0) -> None:
        """تعزيز وزن مفتاح بناءً على إشارة موجبة (Hebbian)."""
        try:
            idx = self.keys.index(key)
        except ValueError:
            return
        self.weights[idx] = min(1.0, self.weights[idx] + _LEARNING_RATE * signal)
        self._normalize()

    def decay(self) -> None:
        """تخفيف الأوزان بعد كل دورة (forgetting factor)."""
        uniform = 1.0 / len(self.weights)
        self.weights = [_DECAY * w + (1.0 - _DECAY) * uniform for w in self.weights]
        self._normalize()

    def sample(self, rng: Random) -> str:
        """أخذ عيّنة بالأوزان الحالية (roulette wheel)."""
        r = rng.random()
        cumulative = 0.0
        for key, weight in zip(self.keys, self.weights):
            cumulative += weight
            if r <= cumulative:
                return key
        return self.keys[-1]

    def top_k(self, k: int) -> list[str]:
        """إرجاع أعلى k مفاتيح وزنًا."""
        paired = sorted(zip(self.weights, self.keys), reverse=True)
        return [key for _, key in paired[:k]]


# ──────────────────────────────────────────────────────────────────────────────
# بناء AST احتمالي (بدلاً من المنهجية الحتمية)
# ──────────────────────────────────────────────────────────────────────────────


def _sample_target_depth(rng: Random, preferred_depth: int, max_depth: int) -> int:
    """Usually exploit the observed depth, occasionally explore deeper admissible ASTs."""
    if max_depth > preferred_depth + 1 and rng.random() < 0.15:
        return rng.randint(preferred_depth + 2, max_depth)
    return max(1, min(preferred_depth + rng.randint(-1, 1), max_depth))


def _build_intuitive_node(
    rng: Random,
    op_layer: NeuralLikeLayer,
    const_layer: NeuralLikeLayer,
    allowed_ops: set[str],
    allowed_consts: list[int],
    arity: int,
    depth: int,
    max_depth: int,
) -> dict:
    """بناء عقدة AST بشكل احتمالي، يُرجِّح المُشغِّلات الأكثر نجاحًا تاريخيًا."""
    # إذا وصلنا للعمق الأقصى، نُرجع ورقة فقط
    if depth >= max_depth:
        return _make_leaf(rng, const_layer, allowed_consts, arity, allowed_ops)

    # احتمال إنتاج ورقة يزداد مع العمق
    leaf_prob = 0.3 + 0.4 * (depth / max_depth)
    if rng.random() < leaf_prob:
        return _make_leaf(rng, const_layer, allowed_consts, arity, allowed_ops)

    # اختر مُشغِّل من الطبقة الاحتمالية
    op = op_layer.sample(rng)

    # تأكد المُشغِّل مسموح به
    binary_ops = {"Add", "Sub", "LessThan", "Equal"} & allowed_ops
    ternary_ops = {"If"} & allowed_ops

    if op == "If" and ternary_ops and depth + 1 < max_depth:
        pred = _build_bool_node(
            rng, op_layer, const_layer, allowed_ops, allowed_consts, arity, depth + 1, max_depth
        )
        then = _build_intuitive_node(
            rng, op_layer, const_layer, allowed_ops, allowed_consts, arity, depth + 1, max_depth
        )
        else_ = _build_intuitive_node(
            rng, op_layer, const_layer, allowed_ops, allowed_consts, arity, depth + 1, max_depth
        )
        return {"op": "If", "args": [pred, then, else_]}

    if op in binary_ops and binary_ops:
        left = _build_intuitive_node(
            rng, op_layer, const_layer, allowed_ops, allowed_consts, arity, depth + 1, max_depth
        )
        right = _build_intuitive_node(
            rng, op_layer, const_layer, allowed_ops, allowed_consts, arity, depth + 1, max_depth
        )
        return {"op": op, "args": [left, right]}

    # احتياطي: ورقة
    return _make_leaf(rng, const_layer, allowed_consts, arity, allowed_ops)


def _build_bool_node(
    rng: Random,
    op_layer: NeuralLikeLayer,
    const_layer: NeuralLikeLayer,
    allowed_ops: set[str],
    allowed_consts: list[int],
    arity: int,
    depth: int,
    max_depth: int,
) -> dict:
    """بناء عقدة بوليانية احتمالية (شرط الـ If)."""
    bool_ops = ["LessThan", "Equal"]
    available = [op for op in bool_ops if op in allowed_ops]
    if not available:
        # احتياطي: LessThan بين وسيطين
        a = {"op": "Arg", "index": 0}
        b = {"op": "Arg", "index": min(1, arity - 1)}
        return {"op": "LessThan", "args": [a, b]}
    op = rng.choice(available)
    left = _make_leaf(rng, const_layer, allowed_consts, arity, allowed_ops)
    right = _make_leaf(rng, const_layer, allowed_consts, arity, allowed_ops)
    return {"op": op, "args": [left, right]}


def _make_leaf(
    rng: Random,
    const_layer: NeuralLikeLayer,
    allowed_consts: list[int],
    arity: int,
    allowed_ops: set[str],
) -> dict:
    """اختيار ورقة (Arg أو ConstInt) باحتمال مرجّح."""
    choices = []
    if "Arg" in allowed_ops:
        choices.extend([("Arg", i) for i in range(arity)])
    if "ConstInt" in allowed_ops and allowed_consts:
        choices.extend([("ConstInt", c) for c in allowed_consts])
    if not choices:
        return {"op": "Arg", "index": 0}

    # وزن الثوابت بناءً على const_layer
    weights = []
    for kind, val in choices:
        if kind == "Arg":
            weights.append(1.0 / max(len(choices), 1))
        else:
            try:
                idx = const_layer.keys.index(str(val))
                weights.append(const_layer.weights[idx])
            except ValueError:
                weights.append(_MIN_WEIGHT)

    total = sum(weights)
    weights = [w / total for w in weights]

    r = rng.random()
    cumulative = 0.0
    for (kind, val), w in zip(choices, weights):
        cumulative += w
        if r <= cumulative:
            if kind == "Arg":
                return {"op": "Arg", "index": val}
            return {"op": "ConstInt", "value": val}
    kind, val = choices[-1]
    if kind == "Arg":
        return {"op": "Arg", "index": val}
    return {"op": "ConstInt", "value": val}


# ──────────────────────────────────────────────────────────────────────────────
# IntuitiveEngine — المحرك الحدسي الكامل
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class IntuitiveEngine:
    """محرك حدسي احتمالي يتعلم أنماط المُشغِّلات والبنى ويولّد تخمينات سريعة.

    - يبدأ بأوزان موحدة ويتعلم من كل مقترح يتجاوز فلتر البصمة.
    - لا يستقبل أي إشارة من المُتحقق (verifier) أو المهمة المخفية.
    - يُكمّل — ولا يُحل محل — البحث الحتمي الحالي.

    الاستخدام:
        engine = IntuitiveEngine(base, seed=42)
        for proposal in engine.intuition_stream(parent, max_proposals=200):
            ...
    """

    base: dict
    seed: int = 0
    _memory: PatternMemory = field(default_factory=PatternMemory, init=False)
    _op_layer: NeuralLikeLayer = field(init=False)
    _const_layer: NeuralLikeLayer = field(init=False)
    _rng: Random = field(init=False)
    _version: str = field(default=_INTUITION_VERSION, init=False)

    def __post_init__(self) -> None:
        self._rng = Random(self.seed)
        allowed_ops = list(self.base.get("allowed_primitives", ["Arg", "ConstInt", "Add", "Sub"]))
        allowed_consts = [str(c) for c in self.base.get("allowed_constants", [0, 1, -1])]
        self._op_layer = NeuralLikeLayer(keys=allowed_ops, _rng=Random(self.seed + 1))
        self._const_layer = NeuralLikeLayer(keys=allowed_consts, _rng=Random(self.seed + 2))

    # ── واجهة عامة ─────────────────────────────────────────────────────────

    def intuition_stream(
        self,
        parent: dict,
        max_proposals: int = 500,
        stats: SearchStats | None = None,
    ) -> Iterator[Proposal]:
        """تدفق المقترحات الحدسية — البديل الاحتمالي لـ candidate_stream.

        كل مقترح ينبثق من الأوزان المتعلَّمة، ثم يُعاد تعليم الأوزان بكل
        مقترح ناجح (تجاوز فلتر البصمة والقيود الثابتة).
        """
        check_tree(parent, self.base)
        arity = len(self.base.get("input_types", ("Int", "Int")))
        probes = _probe_inputs(arity)
        parent_hash = canonical_hash(parent)
        limits = Limits(
            max_depth=self.base["max_ast_depth"],
            max_nodes=self.base["max_ast_nodes"],
            max_ops=max(512, self.base["max_ast_nodes"]),
        )
        allowed_ops = set(self.base["allowed_primitives"])
        allowed_consts = self.base["allowed_constants"]
        max_depth = self.base["max_ast_depth"]
        seen_signatures: set[tuple] = set()
        produced = 0
        attempts = 0
        max_attempts = max(max_proposals * 20, 5000)

        while produced < max_proposals and attempts < max_attempts:
            attempts += 1
            if stats is not None:
                stats.attempted_shapes += 1

            # توليد مقترح AST احتمالي
            target_depth = _sample_target_depth(
                self._rng, self._memory.preferred_depth(), max_depth
            )

            try:
                expr = _build_intuitive_node(
                    self._rng,
                    self._op_layer,
                    self._const_layer,
                    allowed_ops,
                    allowed_consts,
                    arity,
                    depth=1,
                    max_depth=target_depth,
                )
                check_tree(expr, self.base)
            except (IRViolation, ValueError, RecursionError):
                continue

            # حساب بصمة المقترح
            try:
                probe_values = tuple(
                    run_ir_args(expr, point, limits, expected_arity=arity) for point in probes
                )
                if stats is not None:
                    stats.probe_evaluations += len(probes)
            except IRViolation:
                continue

            if probe_values in seen_signatures:
                if stats is not None:
                    stats.observational_prunes += 1
                continue

            seen_signatures.add(probe_values)

            # تعلّم من هذا المقترح (Hebbian reinforcement)
            self._memory.observe(expr, probe_values)
            self._learn_from(expr)

            if stats is not None:
                stats.integer_representatives += 1

            produced += 1
            yield Proposal(expr, "intuition_guess", parent_hash, self.seed)

        # تخفيف الأوزان بعد انتهاء الدورة
        self._op_layer.decay()
        self._const_layer.decay()

    def top_patterns(self, k: int = 5) -> dict:
        """إرجاع ملخص لأبرز الأنماط المتعلَّمة (للبحث والتحليل فقط)."""
        return {
            "version": self._version,
            "total_observations": self._memory.total_observations,
            "top_ops": self._op_layer.top_k(k),
            "top_constants": self._const_layer.top_k(k),
            "preferred_depth": self._memory.preferred_depth(),
            "op_weights": dict(
                zip(self._op_layer.keys, [round(w, 4) for w in self._op_layer.weights])
            ),
        }

    def reset(self) -> None:
        """إعادة ضبط المحرك مع الحفاظ على البذرة الأصلية."""
        self.__post_init__()
        self._memory = PatternMemory()

    # ── تعلّم داخلي (خاص) ──────────────────────────────────────────────────

    def _learn_from(self, expr: dict) -> None:
        """تعزيز أوزان المُشغِّلات والثوابت الموجودة في الـ AST."""
        self._walk_and_reinforce(expr)

    def _walk_and_reinforce(self, node: dict) -> None:
        op = node.get("op", "")
        if op:
            self._op_layer.reinforce(op)
        if op == "ConstInt":
            val = str(node.get("value", 0))
            self._const_layer.reinforce(val)
        for child in node.get("args", []):
            self._walk_and_reinforce(child)


# ──────────────────────────────────────────────────────────────────────────────
# دوال مساعدة عامة
# ──────────────────────────────────────────────────────────────────────────────


def make_engine(base: dict, seed: int = 0) -> IntuitiveEngine:
    """منشئ مُيسَّر للمحرك الحدسي."""
    return IntuitiveEngine(base=base, seed=seed)


def hybrid_stream(
    parent: dict,
    base: dict,
    engine: IntuitiveEngine,
    intuition_ratio: float = 0.4,
    max_proposals: int = 500,
    seed: int = 0,
    stats: SearchStats | None = None,
) -> Iterator[Proposal]:
    """تدفق هجين: يمزج بين البحث الحتمي والتخمين الحدسي.

    intuition_ratio: نسبة المقترحات الحدسية (0.0 = حتمي فقط، 1.0 = حدسي فقط).
    المُتحقق وحده يقرر صحة أي مقترح — هذا المحرك يوفر مرشحين فقط.
    """
    from .search import candidate_stream

    if not 0.0 <= intuition_ratio <= 1.0:
        raise ValueError("intuition_ratio must be in [0.0, 1.0]")
    if engine.base != base:
        raise ValueError("Intuition engine base must match the deterministic search base")

    n_intuitive = int(max_proposals * intuition_ratio)
    n_deterministic = max_proposals - n_intuitive

    det_stream = candidate_stream(
        parent, base, seed=seed, max_proposals=n_deterministic, stats=stats
    )
    int_stream = engine.intuition_stream(parent, max_proposals=n_intuitive, stats=stats)

    rng = Random(seed + 999)
    det_buffer: list[Proposal] = []
    int_buffer: list[Proposal] = []
    det_done = False
    int_done = False
    produced = 0
    seen_hashes: set[str] = set()

    while produced < max_proposals:
        # جمع دفعة من كلا المصدرين
        if not det_done and len(det_buffer) < 5:
            try:
                det_buffer.append(next(det_stream))
            except StopIteration:
                det_done = True

        if not int_done and len(int_buffer) < 5:
            try:
                int_buffer.append(next(int_stream))
            except StopIteration:
                int_done = True

        if not det_buffer and not int_buffer:
            break

        # اختر المصدر باحتمالية
        use_intuition = int_buffer and (not det_buffer or rng.random() < intuition_ratio)

        if use_intuition and int_buffer:
            proposal = int_buffer.pop(0)
        elif det_buffer:
            proposal = det_buffer.pop(0)
        else:
            break
        expression_hash = canonical_hash(proposal.expression)
        if expression_hash in seen_hashes:
            continue
        seen_hashes.add(expression_hash)
        yield proposal
        produced += 1
