import pytest

from cin.ir import IRViolation, Limits, canonical_hash, check_tree, run_ir

BASE = {
    "max_ast_depth": 8,
    "max_ast_nodes": 64,
    "allowed_constants": [-1, 0, 1],
    "allowed_primitives": ["Arg", "ConstInt", "Add", "Sub", "LessThan", "Equal", "If"],
}


def test_seed_projection_and_tree_hash():
    expr = {"op": "Arg", "index": 0}
    assert check_tree(expr, BASE) == "Int"
    assert run_ir(expr, 7, -1, Limits()) == 7
    assert canonical_hash(expr) == canonical_hash({"index": 0, "op": "Arg"})


def test_max_tree_and_lazy_if():
    p = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 1},
            {"op": "Arg", "index": 0},
        ],
    }
    assert check_tree(p, BASE) == "Int"
    assert run_ir(p, 4, 12, Limits()) == 12
    assert run_ir(p, 17, -1, Limits()) == 17
    # Unselected branch would overflow the limited arithmetic bit budget.
    lazy = {
        "op": "If",
        "args": [
            {"op": "Equal", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 0}]},
            {"op": "ConstInt", "value": 1},
            {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
        ],
    }
    assert run_ir(lazy, 2**60, 2**60, Limits(max_bits=64)) == 1


def test_wrong_type_rejected_before_execution():
    bad = {
        "op": "Add",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "ConstInt", "value": 1},
        ],
    }
    with pytest.raises(IRViolation):
        check_tree(bad, BASE)


def test_unknown_op_and_extra_attributes_rejected():
    with pytest.raises(IRViolation):
        check_tree({"op": "Import", "module": "os"}, BASE)
    with pytest.raises(IRViolation):
        check_tree({"op": "Arg", "index": 0, "exec": "bad"}, BASE)


def test_limits_bound_compute_and_depth():
    p = {"op": "Add", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]}
    with pytest.raises(IRViolation):
        check_tree(p, {**BASE, "max_ast_depth": 1})
    with pytest.raises(IRViolation):
        run_ir(p, 3, 4, Limits(max_ops=2))
    with pytest.raises(IRViolation):
        run_ir(p, 2**60, 2**60, Limits(max_bits=32))


def test_export_verified_ir_to_readable_python():
    from cin.ir import render_python

    tree = {
        "op": "If",
        "args": [
            {"op": "LessThan", "args": [{"op": "Arg", "index": 0}, {"op": "Arg", "index": 1}]},
            {"op": "Arg", "index": 1},
            {"op": "Arg", "index": 0},
        ],
    }
    source = render_python(tree, BASE)
    assert "def solve(x: int, y: int) -> int:" in source
    assert "(y if (x < y) else x)" in source
    assert "eval(" not in source
