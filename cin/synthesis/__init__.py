"""Synthesis engines for model-free program induction, CEGIS, and Neuro-Symbolic Guidance."""

from .cegis import (
    CEGISResult,
    run_cegis_loop,
)
from .decision import (
    DecisionResult,
    generate_candidate_predicates,
    generate_candidate_subterms,
    synthesize_conditional_tree,
)
from .deductive import (
    DeductiveStats,
    Interval,
    compute_relational_target_sets,
    compute_term_interval,
    deduce_inverse_obligations,
    deductive_filter_binary_pairs,
    soundly_prunes_binary_op,
)
from .guidance import (
    GuidanceVerdict,
    NeuroSymbolicAgentKernel,
)
from .library import (
    Macro,
    MacroRegistry,
    anti_unify,
    evaluate_transfer_utility,
    extract_reusable_abstractions,
)
from .sygus import (
    SYGUS_BENCHMARKS,
    SyGuSTask,
    get_sygus_task,
)
from .symbolic import (
    AffineExpr,
    LinearInequality,
    PolyhedralRegion,
    SymbolicVerdict,
    ast_to_piecewise_affine,
    verify_equivalence_symbolic,
    verify_spec_symbolic,
)
from .z3_verifier import (
    HAS_Z3,
    Z3Verdict,
    cin_to_z3,
    verify_equivalence_with_z3,
    verify_spec_with_z3,
)

__all__ = [
    "AffineExpr",
    "CEGISResult",
    "DecisionResult",
    "DeductiveStats",
    "GuidanceVerdict",
    "HAS_Z3",
    "Interval",
    "LinearInequality",
    "Macro",
    "MacroRegistry",
    "NeuroSymbolicAgentKernel",
    "PolyhedralRegion",
    "SYGUS_BENCHMARKS",
    "SyGuSTask",
    "SymbolicVerdict",
    "Z3Verdict",
    "anti_unify",
    "ast_to_piecewise_affine",
    "cin_to_z3",
    "compute_relational_target_sets",
    "compute_term_interval",
    "deduce_inverse_obligations",
    "deductive_filter_binary_pairs",
    "evaluate_transfer_utility",
    "extract_reusable_abstractions",
    "generate_candidate_predicates",
    "generate_candidate_subterms",
    "get_sygus_task",
    "run_cegis_loop",
    "soundly_prunes_binary_op",
    "synthesize_conditional_tree",
    "verify_equivalence_symbolic",
    "verify_equivalence_with_z3",
    "verify_spec_symbolic",
    "verify_spec_with_z3",
]
