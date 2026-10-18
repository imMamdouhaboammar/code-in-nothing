# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Threat Model and Execution Boundaries

Code in Nothing (CIN-Lab) is a model-free evolutionary program synthesis research prototype. It evaluates synthesized code through a restricted, total, typed intermediate representation interpreter (`cin.ir`).

### Sandbox Guarantees

1. **Pure AST Interpretation**: The interpreter (`cin.ir.run_ir`) executes only whitelisted typed primitives (`Arg`, `ConstInt`, `Add`, `Sub`, `LessThan`, `Equal`, `If`).
2. **Zero System Access**: Generated programs have no access to Python builtins, imports (`__import__`), filesystem I/O, process execution (`subprocess`), sockets, or network communication.
3. **Execution Limits**: All evaluation cycles are bounded by depth limits (`max_ast_depth`), node limits (`max_ast_nodes`), step bounds (`max_steps`), and constant value boundaries. Exceeding limits triggers deterministic `IRViolation` exceptions without hanging the host interpreter.
4. **Exported Python Code**: The CLI exports synthesized programs as readable Python code (`generated_program.py`). **CIN-Lab never executes this exported file**; it is provided solely for human inspection. Do not execute unreviewed exported programs in privileged environments without validation.

## Reporting a Vulnerability

If you discover a security vulnerability (such as an execution boundary escape in `cin.ir` or an unhandled crash vector during finite-domain verification), please report it responsibly:

1. **Do not open a public issue.**
2. Send vulnerability details via GitHub Security Advisories at [https://github.com/imMamdouhaboammar/code-in-nothing/security/advisories/new](https://github.com/imMamdouhaboammar/code-in-nothing/security/advisories/new) or directly contact the maintainer at `mamdouhfces1997@gmail.com`.
3. Include reproducible steps, seed configuration, and environment details (Python version, OS).

Security reports will be acknowledged within 48 hours, and a triage timeline will be provided.
