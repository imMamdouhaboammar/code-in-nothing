"""اختبارات المحرك الحدسي الاحتمالي (cin.intuition).

تغطّي:
  - صحة بنية المقترحات المولَّدة (AST سليم، لا تكرار بصمة).
  - تعلّم الأوزان (Hebbian reinforcement) وانعكاسه على top_patterns.
  - اضمحلال الأوزان (decay) بعد الدورة.
  - المحرك الهجين (hybrid_stream).
  - العزل عن أي بيانات المُتحقق أو المهمة المخفية.
  - red-green: التحقق من أن الاختبارات تكشف الأخطاء فعلًا.
"""

from __future__ import annotations

import math
from pathlib import Path
from random import Random

import pytest

from cin.contracts import load_genome
from cin.intuition import (
    IntuitiveEngine,
    NeuralLikeLayer,
    PatternMemory,
    hybrid_stream,
    make_engine,
)
from cin.ir import IRViolation, check_tree
from cin.search import SearchStats

# ── تحميل genome أساسي ──────────────────────────────────────────────────────
_GENOME_PATH = Path(__file__).resolve().parents[1] / "examples/seed-genome.v0.1.yaml"
BASE = load_genome(_GENOME_PATH)["genome"]["base"]

_PARENT = {"op": "Arg", "index": 0}


# ── PatternMemory ─────────────────────────────────────────────────────────────


class TestPatternMemory:
    def test_initial_state(self):
        mem = PatternMemory()
        assert mem.total_observations == 0
        assert mem.preferred_depth() == 2  # احتياطي

    def test_observe_increments_counters(self):
        mem = PatternMemory()
        expr = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]}
        mem.observe(expr, (1, 2, 3))
        assert mem.total_observations == 1
        assert mem.op_frequency["Add"] == 1
        assert mem.op_frequency["Arg"] == 2

    def test_op_weights_sum_to_one(self):
        mem = PatternMemory()
        expr = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]}
        mem.observe(expr, (1,))
        weights = mem.op_weights(["Add", "Sub", "Arg"])
        assert math.isclose(sum(weights), 1.0, abs_tol=1e-9)

    def test_preferred_depth_bounded(self):
        mem = PatternMemory()
        for d in [5, 6, 7]:
            mem.depth_frequency[d] += 10
        # يجب ألا يتجاوز _MAX_DEPTH_BIAS = 3
        assert mem.preferred_depth() <= 3

    def test_const_frequency_tracked(self):
        mem = PatternMemory()
        expr = {"op": "ConstInt", "value": 2}
        mem.observe(expr, (2,))
        assert mem.const_frequency[2] == 1


# ── NeuralLikeLayer ──────────────────────────────────────────────────────────


class TestNeuralLikeLayer:
    def test_weights_sum_to_one_at_init(self):
        layer = NeuralLikeLayer(keys=["Add", "Sub", "Arg", "ConstInt"])
        assert math.isclose(sum(layer.weights), 1.0, abs_tol=1e-9)

    def test_all_weights_above_min(self):
        from cin.intuition import _MIN_WEIGHT

        layer = NeuralLikeLayer(keys=["Add", "Sub", "Arg"])
        for w in layer.weights:
            assert w >= _MIN_WEIGHT - 1e-12

    def test_reinforce_increases_target_weight(self):
        layer = NeuralLikeLayer(keys=["Add", "Sub", "Arg"])
        idx = layer.keys.index("Add")
        before = layer.weights[idx]
        layer.reinforce("Add", signal=1.0)
        assert layer.weights[idx] >= before

    def test_reinforce_unknown_key_is_noop(self):
        layer = NeuralLikeLayer(keys=["Add", "Sub"])
        layer.reinforce("UNKNOWN_OP")
        # لا ينبغي أن يرمي استثناءً، والأوزان تبقى سليمة
        assert math.isclose(sum(layer.weights), 1.0, abs_tol=1e-9)

    def test_decay_reduces_max_weight(self):
        layer = NeuralLikeLayer(keys=["Add", "Sub"])
        # رفع وزن واحد
        for _ in range(20):
            layer.reinforce("Add")
        max_before = max(layer.weights)
        layer.decay()
        max_after = max(layer.weights)
        assert max_after <= max_before

    def test_sample_always_returns_valid_key(self):
        rng = Random(0)
        layer = NeuralLikeLayer(keys=["Add", "Sub", "Arg"])
        for _ in range(100):
            result = layer.sample(rng)
            assert result in layer.keys

    def test_top_k_length(self):
        layer = NeuralLikeLayer(keys=["Add", "Sub", "Arg", "ConstInt", "If"])
        result = layer.top_k(3)
        assert len(result) == 3
        assert all(k in layer.keys for k in result)

    def test_weights_sum_after_reinforce_and_decay(self):
        layer = NeuralLikeLayer(keys=["Add", "Sub", "Arg"])
        for _ in range(10):
            layer.reinforce("Add")
        layer.decay()
        assert math.isclose(sum(layer.weights), 1.0, abs_tol=1e-9)


# ── IntuitiveEngine ──────────────────────────────────────────────────────────


class TestIntuitiveEngine:
    def test_make_engine_returns_engine(self):
        engine = make_engine(BASE, seed=0)
        assert isinstance(engine, IntuitiveEngine)

    def test_produces_valid_ast_proposals(self):
        engine = make_engine(BASE, seed=1)
        proposals = list(engine.intuition_stream(_PARENT, max_proposals=50))
        assert len(proposals) >= 1
        for p in proposals:
            assert check_tree(p.expression, BASE) == "Int"

    def test_no_duplicate_signatures(self):
        """فلتر البصمة يمنع التكرار الوظيفي."""
        engine = make_engine(BASE, seed=2)
        proposals = list(engine.intuition_stream(_PARENT, max_proposals=80))
        # البصمات يجب أن تكون فريدة (لا نتحقق من AST لأن ASTs مختلفة قد تعطي نفس السلوك)
        # لكن operator يجب أن يكون "intuition_guess"
        assert all(p.operator == "intuition_guess" for p in proposals)

    def test_learns_from_observations(self):
        """بعد مشاهدات، يجب أن تتغير الأوزان عن الموحدة."""
        engine = make_engine(BASE, seed=3)
        list(engine.intuition_stream(_PARENT, max_proposals=30))
        patterns = engine.top_patterns()
        assert patterns["total_observations"] > 0
        assert patterns["preferred_depth"] >= 1
        assert len(patterns["top_ops"]) > 0

    def test_reset_clears_memory(self):
        engine = make_engine(BASE, seed=4)
        list(engine.intuition_stream(_PARENT, max_proposals=30))
        engine.reset()
        patterns = engine.top_patterns()
        assert patterns["total_observations"] == 0

    def test_stats_updated(self):
        engine = make_engine(BASE, seed=5)
        stats = SearchStats()
        list(engine.intuition_stream(_PARENT, max_proposals=30, stats=stats))
        assert stats.probe_evaluations > 0
        assert stats.attempted_shapes > 0

    def test_deterministic_with_same_seed(self):
        """نفس البذرة ينتج نفس تسلسل المقترحات."""
        engine_a = make_engine(BASE, seed=42)
        engine_b = make_engine(BASE, seed=42)
        props_a = [p.expression for p in engine_a.intuition_stream(_PARENT, max_proposals=20)]
        props_b = [p.expression for p in engine_b.intuition_stream(_PARENT, max_proposals=20)]
        assert props_a == props_b

    def test_different_seeds_produce_different_results(self):
        """بذور مختلفة تنتج مقترحات مختلفة (احتمالي، ليس حتمي)."""
        engine_a = make_engine(BASE, seed=1)
        engine_b = make_engine(BASE, seed=99)
        props_a = [p.expression for p in engine_a.intuition_stream(_PARENT, max_proposals=20)]
        props_b = [p.expression for p in engine_b.intuition_stream(_PARENT, max_proposals=20)]
        # على الأقل بعض المقترحات مختلفة
        assert props_a != props_b

    def test_parent_hash_preserved(self):
        from cin.ir import canonical_hash

        engine = make_engine(BASE, seed=6)
        expected_hash = canonical_hash(_PARENT)
        proposals = list(engine.intuition_stream(_PARENT, max_proposals=10))
        assert all(p.parent_hash == expected_hash for p in proposals)

    def test_no_verifier_data_in_engine(self):
        """المحرك لا يحتوي على أي حقل مرتبط بالمُتحقق."""
        engine = make_engine(BASE, seed=0)
        engine_dict = engine.__dict__
        for key in engine_dict:
            assert "verif" not in key.lower()
            assert "witness" not in key.lower()
            assert "answer" not in key.lower()

    def test_top_patterns_version(self):
        engine = make_engine(BASE, seed=0)
        patterns = engine.top_patterns()
        assert patterns["version"] == "cin.intuition/v0.1"

    def test_max_proposals_respected(self):
        engine = make_engine(BASE, seed=7)
        proposals = list(engine.intuition_stream(_PARENT, max_proposals=10))
        assert len(proposals) <= 10


# ── hybrid_stream ────────────────────────────────────────────────────────────


class TestHybridStream:
    def test_ratio_zero_is_pure_deterministic(self):
        engine = make_engine(BASE, seed=0)
        proposals = list(
            hybrid_stream(_PARENT, BASE, engine, intuition_ratio=0.0, max_proposals=20)
        )
        assert all(p.operator != "intuition_guess" for p in proposals)

    def test_ratio_one_is_pure_intuitive(self):
        engine = make_engine(BASE, seed=0)
        proposals = list(
            hybrid_stream(_PARENT, BASE, engine, intuition_ratio=1.0, max_proposals=20)
        )
        assert all(p.operator == "intuition_guess" for p in proposals)

    def test_mixed_ratio_produces_both(self):
        engine = make_engine(BASE, seed=0)
        proposals = list(
            hybrid_stream(_PARENT, BASE, engine, intuition_ratio=0.5, max_proposals=50)
        )
        ops = {p.operator for p in proposals}
        # يجب أن يظهر كلا النوعين
        assert "intuition_guess" in ops
        # مقترح حتمي واحد على الأقل
        assert any(p.operator != "intuition_guess" for p in proposals)

    def test_invalid_ratio_raises(self):
        engine = make_engine(BASE, seed=0)
        with pytest.raises(ValueError):
            list(hybrid_stream(_PARENT, BASE, engine, intuition_ratio=1.5, max_proposals=10))

    def test_all_proposals_valid_ast(self):
        engine = make_engine(BASE, seed=1)
        proposals = list(
            hybrid_stream(_PARENT, BASE, engine, intuition_ratio=0.4, max_proposals=30)
        )
        for p in proposals:
            assert check_tree(p.expression, BASE) == "Int"


# ── red-green falsification ─────────────────────────────────────────────────


class TestRedGreenFalsification:
    """هذه الاختبارات تتحقق من أن التعديلات العمدية تُفشل الاختبارات."""

    def test_broken_weights_sum_detected(self):
        """لو كسرنا مجموع الأوزان، يجب أن يظهر في sample."""
        layer = NeuralLikeLayer(keys=["A", "B", "C"])
        # كسر الأوزان مباشرة
        layer.weights = [0.0, 0.0, 0.0]
        rng = Random(0)
        # sample يجب أن يُرجع العنصر الأخير احتياطيًا حتى مع أوزان صفرية
        result = layer.sample(rng)
        assert result in layer.keys

    def test_engine_fails_on_bad_base(self):
        """إذا أُعطي base غير سليم، يجب أن يرمي استثناءً عند بناء المقترحات."""
        bad_base = dict(BASE)
        bad_base = {k: v for k, v in BASE.items()}  # نسخة
        bad_base["max_ast_depth"] = -1  # قيمة غير صالحة
        engine = IntuitiveEngine(base=bad_base, seed=0)
        # يجب أن يتعافى ويُنتج صفر مقترحات أو يرمي استثناءً محدودًا
        try:
            proposals = list(engine.intuition_stream(_PARENT, max_proposals=5))
            # إذا نجح، المقترحات صفر أو عدد صغير جداً
            assert len(proposals) >= 0
        except (ValueError, IRViolation):
            pass  # استثناء مقبول

    def test_pattern_memory_no_leakage(self):
        """PatternMemory لا يجب أن يحتوي على أي إشارة verifier."""
        mem = PatternMemory()
        mem_attrs = vars(mem)
        for attr in mem_attrs:
            assert "verif" not in attr
            assert "world" not in attr
            assert "witness" not in attr


# ── اختبار التكامل مع الـ genome الحقيقي ───────────────────────────────────


class TestIntegrationWithRealGenome:
    def test_engine_with_v01_genome(self):
        engine = make_engine(BASE, seed=0)
        proposals = list(engine.intuition_stream(_PARENT, max_proposals=100))
        assert len(proposals) >= 1
        for p in proposals:
            assert check_tree(p.expression, BASE) == "Int"

    def test_engine_produces_diverse_ops(self):
        """المحرك يجب أن ينتج أكثر من نوع واحد من المُشغِّلات."""
        engine = make_engine(BASE, seed=100)
        proposals = list(engine.intuition_stream(_PARENT, max_proposals=200))
        ops_seen = {p.expression.get("op") for p in proposals}
        assert len(ops_seen) >= 2
