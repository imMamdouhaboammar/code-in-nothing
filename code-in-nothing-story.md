# Code in Nothing

*What should code inherit from the code that came before it?*

I've been thinking about something that bothers me whenever I look at how far AI has come

We can ask a model to write a function, explain the function, fix the function, and occasionally apologize for breaking it in the first place. Some of that work is genuinely impressive. But there's a question I keep coming back to: when a problem has been solved, what exactly has the software learned that it can carry into the next problem?

The answer depends on the software, of course. Models can be trained, agents can store memories, tools can retrieve old examples. Still, I wanted to explore a more specific possibility

What if a piece of code could develop a useful capability, have that capability checked independently, and pass a reusable part of it to the next generation of code?

That question eventually became [Code in Nothing (CIN)](https://github.com/imMamdouhaboammar/code-in-nothing)

And yes, the name sounds a little strange. I can live with that

## The idea I borrowed from biology

Neural networks are one of the most successful examples of computing borrowing an idea from biology. They are obviously much simpler than biological brains in some respects, and quite different in others, but the inspiration helped open an enormous field of research

So I started wondering about a different biological idea: inheritance

In nature, organisms don't arrive with a blank biological starting point. Genetic information influences what they can become and how they develop. That doesn't mean a parent's newly acquired knowledge gets written directly into its child's DNA. Biology is considerably more complicated than my little programming experiment, and I don't want the analogy to pretend otherwise

The part that interests me is simpler: **a new generation starts with structure it didn't have to discover from scratch**

In CIN, I represent that idea with five genetic components:

`base` · `driver` · `directive` · `maturity_point` · `stop_station`

These fields form a genome that constrains how a candidate program is generated, developed, evaluated, and stopped. The names come from the biological framing, but they have to earn their place as software contracts. If a gene doesn't produce a measurable change in search behavior, calling it a gene achieves very little

The interesting part begins when a successful program can leave behind something useful

Say one generation discovers how to return the larger of two numbers. The next generation gets a challenge that needs to keep a value between a lower and an upper limit. A human developer immediately sees why `min` and `max` belong in that solution. We don't mentally enumerate thousands of syntax trees to rediscover comparisons every time

I want to know whether CIN can eventually behave in a similarly economical way, within a carefully defined programming language

## Why I started without an LLM

This choice needs a little explanation, because today the obvious answer to almost any code-generation problem is to put a language model in front of it

LLMs are useful. I've worked with enough of them to know that. They can also produce plausible code that violates a requirement, invent an assumption, or quietly change behavior while claiming the result is equivalent. Sampling randomness makes some outputs variable, but incorrect answers can happen even with deterministic decoding. The reliability problem goes deeper than temperature settings

And I don't buy the easy claim that predicting tokens proves a model cannot reason. That argument skips far too much. What matters for this project is that a convincing explanation and a correct program are separate things. If correctness matters, I need a test that lives outside the generator's opinion of its own work

That is why CIN's current core is deliberately model-free

It uses a restricted, typed representation of programs, searches for candidate abstract syntax trees, and submits candidates to a verifier with its own private test witnesses. The generator is not supposed to see those private witnesses and then tailor an answer to them. A candidate has to meet the rules of the world in which it is being tested

There are no neural weights being updated here. When I talk about CIN learning, I mean retaining useful program structures and, eventually, using them to change future search decisions. That is a narrower and more testable claim than saying the project has already solved online learning

The verifier can make a precise claim about that world. It cannot magically turn a finite test domain into a mathematical proof for every possible integer

That limitation is part of the experiment, and I'd rather keep it visible

## What the project can actually do today

CIN already explores small arithmetic and conditional programs. It can enumerate candidate structures under defined constraints, avoid some duplicate work by comparing behavior on public probes, and verify certain tasks over finite domains. The code also has early provisions for wider input arity, while parts of the independent verification path remain limited to two-input tasks

I think the numbers tell the story better than a polished feature list

In the repository's recorded finite-domain experiments, finding `max2` took 85 candidate proposals. `min2` took 59. `absdiff`, which asks for the absolute distance between two inputs, took 22,698 proposals and 229,135 internal shape attempts

All three were small problems. All three were solvable. And one of them made the cost of searching painfully obvious

Those figures come from a particular implementation and benchmark setup, not a general speed claim. The [`experiments/RESULTS.md`](https://github.com/imMamdouhaboammar/code-in-nothing/blob/main/experiments/RESULTS.md) record is there for anyone who wants to inspect the evidence

There is something useful about being confronted by 229,135 shape attempts while trying to solve a function a programmer might write in one line. It's an excellent way to lose confidence in a simplistic theory of intelligence

## The search problem gets ugly very quickly

Imagine you're trying to construct a program from a limited set of building blocks: constants, variables, arithmetic operations, comparisons, and `If` expressions

For a small expression, you can try a large number of combinations and survive. Add more inputs, allow nested decisions, or require a larger expression, and the number of possible syntax trees grows at an alarming rate. The search isn't merely choosing operators. It is also choosing tree shapes, subexpressions, where conditions belong, and which branches should do what

For binary-expression trees with a fixed number of internal nodes, Catalan numbers are part of that growth. Adding operators and leaf choices multiplies the possibilities further. The exact count depends on the grammar, but the practical result is easy to recognize: the CPU starts spending most of its time considering programs that never had much chance of satisfying the task

This is the first major problem I'm trying to address

If CIN has to rediscover every useful composition by brute force, inheritance becomes a nice story wrapped around an expensive search loop. Eventually the story has to pay for itself in fewer evaluations, lower total search time, or better results on new tasks

I see four research directions worth testing

### 1. Learn where a condition belongs

Suppose we're looking for a function that returns the larger of `x` and `y`

One approach is to generate complete `If(predicate, then, else)` trees, over and over, until the right combination appears. That makes every predicate compete with every possible branch expression

A smarter approach is to discover small expressions that are correct for *some* public examples, discover predicates that divide those examples, and then connect the two. In this case, `x` already produces the right output for part of the domain, and `y` does for the rest. The useful question becomes: which condition sends each case to the right branch?

This is closely related to the divide-and-conquer method demonstrated by **EUSolver**, which uses small expressions, predicates, and decision-tree learning in syntax-guided synthesis. The point isn't that I've invented this method. The point is to test what happens when it becomes part of CIN's search process and its hereditary constraints

There is still a danger here. Information gain over a few public examples can favor a predicate that looks clever locally and generalizes badly. Any resulting tree has to go through independent verification, and the total cost of collecting terms and building the tree belongs in the benchmark

### 2. Work backward from what must be true

If a function must produce `7`, and I've decided that the root operation is addition, I don't need to guess both sides independently forever

Once one side produces `3`, the other side has an obligation: it must produce `4`

That's the basic intuition behind inverse semantics and deductive pruning. Operators can communicate constraints backward to the expressions that feed them. For subtraction, multiplication, or a conditional branch, the obligations change, sometimes becoming more complicated than a single required value

This could help CIN reject impossible combinations earlier. The difficult part is doing it correctly across many public examples, with sound rules for partial operations and types, without feeding the searcher privileged information from the verifier

I want this kind of search to ask better questions before it spends time building an entire AST

### 3. Let a successful generation leave a useful abstraction

This is the part I'm most interested in

Imagine CIN learns a small, verified program equivalent to `max(a, b)`. A later task needs `clamp(x, low, high)`. If the language can express the required functions, the candidate could be built from something like:

```python
min(max(x, low), high)
```

The next generation should be able to consider the inherited `max` capability as one building block, rather than reconstructing all its internal comparisons every time

But simply saving old syntax trees would be a weak form of memory. A useful abstraction needs parameters, a clear type and behavior contract, and evidence that it still works when inserted into a new program. It also needs to earn the cost of being added to the library. Save every repeated fragment and the library becomes another enormous search space

So the proposed rule is selective inheritance: find common structures in admitted programs, generalize the parts that really repeat, measure their compression value, and promote only candidates that survive validation

There is serious prior research here. **DreamCoder** learns reusable program libraries alongside a neural search policy. **Stitch** explores fast, corpus-guided abstraction discovery. CIN's particular research constraint is to explore library learning without a neural guide in its core, with independent verification and an explicit record of what each generation inherits

I have to be careful with the DNA comparison here. A learned software abstraction passed to a child is closer to engineered inheritance of acquired capabilities than to ordinary human genetic inheritance. That's fine. The biology gave me a question; the software has to supply the answer

### 4. Find out where finite verification stops being enough

The current verifier can exhaustively check a defined finite input world. If that world contains every pair of integers from `-4` to `4`, passing all 81 input pairs is meaningful evidence about those 81 cases

It's still possible for the program to fail on `10,000` and `-7`, or on a combination outside the chosen domain

For stronger guarantees, CIN would eventually need proof techniques that match the program language and its claims: symbolic equivalence, deductive reasoning, invariant checking, or induction for properties that require it. Mathematical induction is one important technique, though it isn't the only route to proofs over unbounded domains

And some program properties are undecidable in general, so there will never be a universal verifier that settles every possible question about arbitrary software

That's a boundary I want the project to respect, especially if its ambitions grow

## What inheritance has to prove

There's an easy way to make a research demo look impressive: show a child program solving a problem quickly after giving it exactly the library entry that problem needs

That would teach us very little

The harder test is to let CIN learn abstractions from one collection of tasks, freeze what it learned, and then give its descendants tasks they haven't seen. Compare them with fresh searchers under the same total computational budget. Charge the inherited version for the cost of discovering, validating, storing, and retrieving its abstractions. Include problems where yesterday's favorite abstraction is useless

The measures I care about are fairly ordinary:

- How often does it solve previously unseen tasks?
- How much total computation does each valid solution require?
- When does an inherited abstraction help, and when does it slow search down?
- Can the verifier still work independently, without private witnesses leaking into generation?
- Does the benefit continue across generations, or does the library eventually become clutter?

Even a negative result would tell me something. Maybe the overhead of maintaining an abstraction library exceeds its value for small tasks. Maybe the gains appear only across related task families. Maybe a clever decision-tree search does most of the work and inheritance contributes very little

All of those are answers I would want to know

## And what about AGI?

This is where the experiment gets philosophical again

I often think about Daniel Kahneman's distinction between fast, intuitive judgment and slower, deliberate reasoning. The *System 1 / System 2* framing is a useful analogy for asking what happens when a quick proposal has to survive a slower check. It isn't a literal description of how an LLM or CIN thinks

The longer-term question that interests me is whether a program can accumulate verified knowledge across problems, then use that knowledge to reduce the work required by its future self

That touches several big topics at once: continual learning, program synthesis, symbolic reasoning, persistent memory, and compositional generalization. It also leaves a lot unresolved. Verification of a formal function says nothing on its own about truth in an open-ended conversation. A library of reusable code does not amount to general intelligence. And a model-free synthesizer solving arithmetic challenges is a very long way from a system that can understand the physical and social world

I'm also unconvinced that AGI has to arrive through a single brand-new mathematical idea. More data and compute have achieved things many people underestimated, while symbolic methods and learned search policies have shown how useful structure can change a problem. I suspect the interesting progress will involve several kinds of reasoning and memory working together. That's a research hunch, not a prediction

CIN gives me a small place to investigate one piece of that larger puzzle without pretending to have solved the rest

## The question I want the next generation to answer

If the first version of a program solves `max2`, and a later version solves `clamp`, I want to know exactly what passed between them

Was it a verified abstraction that shortened the search? A better way to choose predicates? A compact record of useful behavior? Or did I just move the expensive computation into a library-building stage and congratulate myself when the final search looked faster?

That last possibility deserves serious attention

For now, Code in Nothing is an experimental research project with a restricted language, bounded evidence, and a very large question behind some very small programs

I'm happy to let the code look modest while I work on the question

Because what I'd really like to see, one generation from now, is a program that can point to a capability it inherited, show why the capability is valid, and demonstrate that it helped solve a problem its predecessor had never encountered

That would be a result worth building on

---

### Research behind the questions

These papers inform the proposed directions. Their methods and reported results belong to their authors; CIN's own claims require its own experiments

- [Alur, Radhakrishna & Udupa, *Scaling Enumerative Program Synthesis via Divide and Conquer* (TACAS 2017)](https://www.microsoft.com/en-us/research/publication/scaling-enumerative-program-synthesis-via-divide-and-conquer/)
- [Polozov & Gulwani, *FlashMeta: A Framework for Inductive Program Synthesis* (OOPSLA 2015)](https://www.microsoft.com/en-us/research/uploads/prod/2018/01/oopsla2015-flashmeta.pdf)
- [Polikarpova et al., *Program Synthesis from Polymorphic Refinement Types* (PLDI 2016)](https://cseweb.ucsd.edu/~npolikarpova/publications/pldi16.pdf)
- [Ellis et al., *DreamCoder: Bootstrapping Inductive Program Synthesis with Wake-Sleep Library Learning* (PLDI 2021)](https://people.csail.mit.edu/asolar/papers/EllisWNSMHCST21.pdf)
- [Bowers et al., *Top-Down Synthesis for Library Learning* (POPL 2023)](https://arxiv.org/abs/2211.16605)

**Project:** [github.com/imMamdouhaboammar/code-in-nothing](https://github.com/imMamdouhaboammar/code-in-nothing)
