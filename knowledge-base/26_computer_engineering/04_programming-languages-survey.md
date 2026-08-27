---
id: compeng.languages_survey
title: Programming languages — paradigms, type systems, memory models and a register of 48
domain: 26_computer_engineering
tags: [programming-languages, paradigms, type-systems, memory-management, compilers, jit, garbage-collection, ownership, language-register]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "2025 Stack Overflow Developer Survey — Technology", url: "https://survey.stackoverflow.co/2025/technology", publisher: "Stack Overflow", accessed: 2026-08-25}
  - {title: "TIOBE Index", url: "https://www.tiobe.com/tiobe-index/", publisher: "TIOBE Software", accessed: 2026-08-25}
  - {title: "C23 (C standard revision) — ISO/IEC 9899:2024", url: "https://en.wikipedia.org/wiki/C23_(C_standard_revision)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Standard C++ — current status", url: "https://isocpp.org/std/status", publisher: "Standard C++ Foundation", accessed: 2026-08-25}
  - {title: "Rust Edition Guide — editions", url: "https://doc.rust-lang.org/edition-guide/editions/index.html", publisher: "The Rust Project", accessed: 2026-08-25}
related: [compeng.language_deep_dives, compeng.machine_level, compeng.curriculum]
unit_system: SI
---

# Programming languages — paradigms, type systems, memory models and a register of 48

**Summary.** A language is a bundle of four independent design decisions — paradigm, type system, memory model and compilation model — plus a community and an ecosystem that usually matter more than any of them. This file sets out those four axes precisely, then registers 48 languages with year, creator, paradigm, typing, memory model, killer domain and current standing. It closes with the honest advice about how many languages to learn and which.

## Key facts

| Measure | Result | Source |
|---|---|---|
| Most-used languages, all respondents | JavaScript 66%, HTML/CSS 61.9%, SQL 58.6%, **Python 57.9%**, Bash/Shell 48.7%, TypeScript 43.6% | Stack Overflow 2025 (n≈31,771 for this section) |
| Most-admired languages | **Rust 72%**, Gleam 70%, Elixir 66%, Swift 65.9%, **Zig 64%** | Stack Overflow 2025 |
| Most-desired language | Python 39.3%, then SQL 35.6% | Stack Overflow 2025 |
| TIOBE top five | Python 20.17%, C++ 10.75%, Java 9.45%, C 8.89%, C# 6.08% | TIOBE, **September 2024** |
| Current C standard | **C23 = ISO/IEC 9899:2024**, published 31 Oct 2024 | Wikipedia / ISO |
| Current C++ standard | **C++23** published; C++26 in progress via a decoupled TS "feature branch" model | isocpp.org |

> ⚠️ The TIOBE figures fetched for this file are the **September 2024** index, not a 2026 one — the live page served a cached snapshot. Treat the ranking as indicative of ordering, not of current values. Stack Overflow 2025 is the more recent verified data point.

## Part 1 — The four axes

### Paradigms

A paradigm is a claim about what a program *is*.

- **Imperative** — a program is a sequence of state changes. The base case; everything below either restricts it or builds on it.
- **Procedural** — imperative plus subroutines and structured control flow (Dijkstra's contribution). C, Pascal, Fortran 77.
- **Object-oriented** — state and the code that mutates it are bundled into objects that communicate. Two very different traditions: the *Simula* lineage (classes, static types, inheritance — C++, Java, C#) and the *Smalltalk* lineage (message passing, late binding, everything is an object — Ruby, Objective-C, Erlang's ancestry). Alan Kay, who coined the term, meant the second.
- **Functional** — computation is the evaluation of expressions; functions are values; state change is minimised or eliminated. *Pure* functional (Haskell) makes effects explicit in the type system; *impure* functional (OCaml, F#, Scheme, Clojure) allows mutation but discourages it.
- **Logic** — you state facts and rules; the runtime searches for solutions. Prolog, Datalog, miniKanren, Answer Set Programming.
- **Declarative** — you state *what* you want, not *how*. SQL, HTML/CSS, Terraform, Make, regular expressions. Logic and functional programming are both special cases.
- **Array** — the primitive is the whole array, not the element. APL, J, K, and, in practice, NumPy and MATLAB. Loops disappear into operators.
- **Concurrent** — the language provides first-class abstractions for simultaneous execution. Sub-schools: *shared memory + locks* (C/C++/Java), *communicating sequential processes* (Go channels, occam), *actors* (Erlang, Elixir, Akka), *software transactional memory* (Clojure, Haskell), *structured concurrency* (Kotlin, Swift, Trio).
- **Dataflow / reactive** — computation is driven by data availability rather than a program counter. LabVIEW, Verilog and VHDL (fundamentally dataflow), spreadsheets, TensorFlow's original graph mode, RxJS.

Every real language is multi-paradigm. The paradigm labels describe what the language makes *easy*, not what it makes possible.

### Type systems

Four orthogonal questions, routinely conflated:

1. **Static vs dynamic** — are types checked before running (Java, Rust, Haskell) or attached to values at run time (Python, Ruby, JavaScript)? *Gradual* typing sits between (TypeScript, Python type hints, Sorbet).
2. **Strong vs weak** — how willing is the language to reinterpret a value of one type as another? C is statically but weakly typed (casts reinterpret bits). Python is dynamically but strongly typed (`"1" + 1` raises). JavaScript is dynamically and weakly typed (`"1" + 1 === "11"`). "Strong/weak" is a spectrum, not a boolean.
3. **Nominal vs structural** — does type identity come from the declared name (Java, C++, Rust) or the shape (TypeScript, Go interfaces, OCaml objects)? Structural typing gives duck typing with static checking.
4. **Inference** — how much can be omitted? Hindley–Milner inference (ML, Haskell, OCaml) infers whole signatures; local inference (`auto`, `var`, `let`) infers only within a body. Rust and Swift use a constraint-solving hybrid.

Beyond these: **algebraic data types** with exhaustive pattern matching (ML family, Rust, Swift, Scala 3, and — belatedly — Java and C#) are arguably the single most valuable type-system feature for correctness. **Dependent types** allow types to depend on values (`Vec n a` — a vector of statically-known length *n*), enabling proofs to be expressed as types; Idris, Agda, Lean 4 and F* are the practical exemplars. **Linear/affine types** track that a value is used exactly once (or at most once) — Rust's ownership is affine typing in disguise, and Haskell has linear types as an extension.

### Memory models

| Model | Mechanism | Cost | Languages |
|---|---|---|---|
| **Manual** | `malloc`/`free`, `new`/`delete` | Maximum control; use-after-free, double-free, leaks | C, Zig, assembly |
| **RAII / scope-based** | Destructors run at scope exit; ownership by convention | Deterministic, near-zero overhead; still allows dangling refs | C++, Rust, Swift (partly), Ada |
| **Reference counting** | Per-object count; free at zero | Deterministic; cycles leak; atomic RC costs on multicore | Swift (ARC), Objective-C, CPython (plus a cycle detector), Rust's `Rc`/`Arc` |
| **Tracing GC** | Periodically find and free unreachable objects | No manual errors; pause times and memory overhead | Java, C#, Go, JavaScript, Haskell, Erlang, Lua |
| **Ownership + borrowing** | Compile-time affine types with lifetime checking | Memory and thread safety with no runtime cost; steep learning curve | **Rust** |
| **Region / arena** | Allocate in a block, free the block wholesale | Very fast; needs the lifetime pattern to fit | Zig allocators, C arenas, Odin, D's regions |

Tracing GC has many strategies worth distinguishing: generational (most objects die young), concurrent/incremental (Go's, tuned for sub-millisecond pauses), region-based low-pause collectors (ZGC, Shenandoah), and copying/compacting collectors that eliminate fragmentation at the cost of moving objects.

The deep insight — Rust's contribution to language design — is that **memory safety and data-race freedom are the same problem**. Both are about aliasing plus mutation. Forbid mutable aliasing and both classes of bug disappear at compile time.

### Compilation models

- **AOT (ahead-of-time) to native** — C, C++, Rust, Go, Zig, Swift, Fortran, Ada. Fast startup, predictable performance, no runtime warm-up.
- **AOT to bytecode + VM** — Java, C#, Kotlin, Scala, Clojure, Erlang/Elixir. Portable artefact, runtime services (GC, reflection, hot-swap).
- **JIT (just-in-time)** — the VM profiles and compiles hot paths to native code at run time, using information a static compiler cannot have: actual types, actual branch frequencies, actual call targets. HotSpot, V8, .NET RyuJIT, LuaJIT, PyPy, GraalVM. JITs can beat AOT on long-running dynamic code and lose badly on short-lived processes.
- **Interpreted** — a tree-walker or bytecode loop with no native compilation. Reference CPython (with a specialising adaptive interpreter since 3.11), Ruby's MRI, Bash, classic Lua.
- **Transpiled** — compiled to another high-level language. TypeScript → JavaScript, Kotlin/JS, Nim → C, Cython → C, ClojureScript → JS.
- **Hybrid** — the modern norm. CPython interprets bytecode but has an optional JIT tier; Java interprets then JITs then deoptimises; Android AOT-compiles installed apps from profiles collected at run time.

**WebAssembly** cuts across all of this: a portable compilation *target* with a formal specification, a sandboxed memory model, and near-native speed, now used well beyond the browser (edge compute, plugin systems, embedded scripting).

## Part 2 — The register

Legend for memory: M = manual, RC = reference counting, GC = tracing GC, OB = ownership/borrowing, RAII = scope destructors.

### Systems languages

| # | Language | Year / creator | Paradigm | Typing | Memory | Killer domain | Standing 2026 |
|---|---|---|---|---|---|---|---|
| 1 | **C** | 1972, Dennis Ritchie (Bell Labs) | Procedural | Static, weak | M | Kernels, embedded, everything's substrate | Permanent. C23 = ISO/IEC 9899:2024. TIOBE #4 (Sep 2024) |
| 2 | **C++** | 1985, Bjarne Stroustrup | Multi (OO, generic, functional) | Static, strong-ish, nominal | M + RAII + smart ptrs | Games, HPC, trading, EDA, browsers | Enormous and growing. C++23 published; C++26 in progress. TIOBE #2 |
| 3 | **Rust** | 2010 (1.0 in 2015), Graydon Hoare / Mozilla | Multi, ownership-oriented | Static, strong, inference, traits | **OB** | Systems where safety matters; now in Linux and Windows kernels | **Most-admired language, 72%** (SO 2025). Editions 2015/2018/2021/2024 |
| 4 | **Zig** | 2016, Andrew Kelley | Procedural | Static, strong, comptime | M with explicit allocators | C replacement, cross-compilation, build tooling | Pre-1.0 but 64% admired (SO 2025); serious traction |
| 5 | **Go** | 2009, Griesemer/Pike/Thompson (Google) | Procedural + CSP concurrency | Static, structural interfaces | GC (low-pause concurrent) | Cloud infrastructure, CLIs, network services | Dominant in infrastructure. TIOBE #8 |
| 6 | **Ada** | 1980, Jean Ichbiah / US DoD | Procedural, concurrent | Static, very strong, range types | M + controlled types | Avionics, rail, defence, space | Niche but entrenched; SPARK subset for formal proof |
| 7 | **D** | 2001, Walter Bright | Multi | Static, strong | GC, optional manual | "Better C++" | Small, stable, respected niche |
| 8 | **Nim** | 2008, Andreas Rumpf | Multi | Static, strong, inference | ARC/ORC (deterministic RC) | Python-like syntax with C performance | Small, active |
| 9 | **Odin** | 2016, Ginger Bill | Procedural | Static, strong | Manual + explicit allocators | Games, graphics | Small, growing |
| 10 | **Mojo** | 2023, Chris Lattner / Modular | Multi, Python-superset ambition | Static + dynamic | Ownership-based | AI/GPU kernels with Python ergonomics | Early; commercially backed, still maturing |
| 11 | **Carbon** | 2022 (experimental), Google | Multi | Static, strong | Manual + ownership | Bidirectional C++ interop successor | **Experimental — not production** |
| 12 | **Crystal** | 2014, Manas Technology | OO | Static, global inference | GC | Ruby syntax at native speed | Small, stable |

### Managed / application languages

| # | Language | Year / creator | Paradigm | Typing | Memory | Killer domain | Standing 2026 |
|---|---|---|---|---|---|---|---|
| 13 | **Java** | 1995, James Gosling (Sun) | OO | Static, nominal | GC (G1/ZGC) | Enterprise backend, Android, big data | Vast installed base. TIOBE #3. Virtual threads (Project Loom) reshaped its concurrency story |
| 14 | **Kotlin** | 2011, JetBrains | Multi (OO + functional) | Static, null-safe | GC (JVM) | **Official Android language**; server-side | Strong and rising. TIOBE #18 |
| 15 | **C#** | 2000, Anders Hejlsberg (Microsoft) | Multi | Static, strong | GC (.NET) | Windows, enterprise, **Unity games** | Very strong; .NET is genuinely cross-platform now. TIOBE #5 |
| 16 | **Scala** | 2004, Martin Odersky | OO + functional | Static, very rich (HKT, implicits) | GC (JVM) | Data engineering (Spark), typed FP | Declining from its peak; Scala 3 is a large improvement |
| 17 | **Swift** | 2014, Chris Lattner (Apple) | Multi | Static, strong, ADTs | **ARC** | Apple platforms; expanding server-side | Dominant on Apple; 65.9% admired (SO 2025) |
| 18 | **Objective-C** | 1984, Brad Cox & Tom Love | OO (Smalltalk messaging) | Static + dynamic dispatch | ARC (MRC historically) | Legacy Apple codebases | Maintenance mode |
| 19 | **Dart** | 2011, Google | OO | Static, sound null safety | GC | **Flutter** cross-platform UI | Healthy, tied to Flutter's fate |

### Dynamic / scripting languages

| # | Language | Year / creator | Paradigm | Typing | Memory | Killer domain | Standing 2026 |
|---|---|---|---|---|---|---|---|
| 20 | **Python** | 1991, Guido van Rossum | Multi | Dynamic, strong, gradual hints | RC + cycle GC | **ML/AI, data, scripting, glue, teaching** | **TIOBE #1 (20.17%), most-desired (39.3%)**. Free-threaded build officially supported from 3.14 |
| 21 | **JavaScript** | 1995, Brendan Eich (Netscape) | Multi, prototype-based | Dynamic, weak | GC | The browser; also Node/Deno/Bun on the server | **Most-used language, 66%** (SO 2025) |
| 22 | **TypeScript** | 2012, Anders Hejlsberg (Microsoft) | Multi | **Static, structural, gradual** | GC (JS host) | Any JavaScript project above toy size | 43.6% usage and rising; effectively the default for new web work |
| 23 | **Ruby** | 1995, Yukihiro Matsumoto | OO (Smalltalk-influenced) | Dynamic, strong | GC | **Rails**, DevOps tooling | Stable niche; TIOBE #16 |
| 24 | **PHP** | 1995, Rasmus Lerdorf | Imperative + OO | Dynamic, weak-ish | RC + cycle GC | Web backends; **WordPress** | Still enormous by deployment; PHP 8 with JIT is a real language now. TIOBE #13 |
| 25 | **Perl** | 1987, Larry Wall | Multi | Dynamic | RC | Text processing, sysadmin, bioinformatics | Legacy; regex legacy is its lasting contribution |
| 26 | **Lua** | 1993, PUC-Rio (Ierusalimschy et al.) | Multi, prototype-based | Dynamic | GC (incremental/generational) | **Embedded scripting**: games, Redis, Neovim, OpenResty | Permanent niche; LuaJIT is remarkably fast |

### Scientific and numeric languages

| # | Language | Year / creator | Paradigm | Typing | Memory | Killer domain | Standing 2026 |
|---|---|---|---|---|---|---|---|
| 27 | **Fortran** | 1957, John Backus (IBM) | Procedural, array | Static | Manual/static | **HPC, climate, CFD, linear algebra** | Alive and standardised (Fortran 2023). TIOBE #10 — higher than it has been in decades |
| 28 | **R** | 1993, Ihaka & Gentleman | Multi, array | Dynamic | GC | Statistics, bioinformatics, academic analysis | Strong in statistics; losing general data work to Python. TIOBE #15 |
| 29 | **Julia** | 2012, Bezanson/Karpinski/Shah/Edelman (MIT) | Multi, multiple dispatch | Dynamic + optional annotations, JIT-specialised | GC | Technical computing that needs both speed and expressiveness | Excellent design; adoption below its quality |
| 30 | **MATLAB** | 1984, Cleve Moler / MathWorks | Array, imperative | Dynamic | GC | Control systems, DSP, engineering simulation, Simulink | Entrenched in engineering education and industry. Proprietary. TIOBE #12 |
| 31 | **APL** | 1962, Kenneth Iverson | **Array** | Dynamic | GC | Array-oriented thinking; historical influence | Historic; Iverson won the 1979 Turing Award for it |
| 32 | **J** | 1990, Iverson & Hui | Array, tacit/point-free | Dynamic | GC | ASCII-only APL successor | Tiny but devoted |
| 33 | **K / q (kdb+)** | 1993, Arthur Whitney | Array | Dynamic | Manual/RC | **Time-series in finance** — kdb+ is the HFT standard | Small, extremely lucrative niche |

### Functional languages

| # | Language | Year / creator | Paradigm | Typing | Memory | Killer domain | Standing 2026 |
|---|---|---|---|---|---|---|---|
| 34 | **Haskell** | 1990, committee | **Purely functional**, lazy | Static, HM + extensions, very strong | GC | Compilers, correctness-critical work, research | Influential far beyond its usage; ideas leak into every language |
| 35 | **OCaml** | 1996, INRIA | Functional + imperative + OO | Static, HM inference | GC (multicore since 5.0) | Compilers, static analysis, **Jane Street's whole stack** | Small, healthy, well-paid |
| 36 | **F#** | 2005, Don Syme (Microsoft) | Functional-first | Static, HM-ish | GC (.NET) | Finance, data on .NET | Small but well-supported |
| 37 | **Clojure** | 2007, Rich Hickey | Functional Lisp | Dynamic, spec-based contracts | GC (JVM) | Data-heavy backends; immutable-by-default design | Small, influential, loyal |
| 38 | **Erlang** | 1986, Joe Armstrong et al. (Ericsson) | Functional, **actor** concurrency | Dynamic | Per-process GC | Telecom switches, messaging (WhatsApp), soft real-time fault tolerance | The BEAM VM is a genuine engineering marvel |
| 39 | **Elixir** | 2011, José Valim | Functional, actor | Dynamic + gradual | Per-process GC (BEAM) | Web (Phoenix/LiveView), realtime, IoT | **66% admired** (SO 2025); healthy and growing |
| 40 | **Lisp / Scheme / Racket** | 1958 John McCarthy; 1975 Scheme (Sussman & Steele); 1995 Racket (PLT) | Functional + everything (macros) | Dynamic (typed variants exist) | GC | Metaprogramming, language design, teaching (SICP) | Common Lisp niche; Racket alive in PL research and education |
| 41 | **Gleam** | 2016, Louis Pilfold | Functional | **Static, HM inference** | BEAM GC | Type-safe BEAM programming | Newest entrant in the register; **70% admired** (SO 2025) |

### Declarative, domain-specific and hardware languages

| # | Language | Year / creator | Paradigm | Typing | Memory | Killer domain | Standing 2026 |
|---|---|---|---|---|---|---|---|
| 42 | **SQL** | 1974, Chamberlin & Boyce (IBM), on Codd's model | **Declarative, relational** | Static-ish, per-dialect | n/a | Every relational database on earth | **58.6% usage** (SO 2025); the most durable language in the register |
| 43 | **Prolog** | 1972, Colmerauer & Roussel | **Logic** | Dynamic | GC | Theorem proving, NLP research, constraint problems | Academic; Datalog descendants power modern static analysis |
| 44 | **Bash** | 1989, Brian Fox (GNU) | Imperative shell | Untyped strings | n/a | Glue, automation, CI, everything on Unix | **48.7% usage** (SO 2025). Unavoidable |
| 45 | **PowerShell** | 2006, Jeffrey Snover (Microsoft) | Imperative, **object pipeline** | Dynamic over .NET types | GC (.NET) | Windows and Azure administration | Standard on Windows; cross-platform since v6 |
| 46 | **Assembly** | 1947 onward | Imperative, machine-level | Untyped | Manual | Boot code, kernels, cryptographic primitives, DSP kernels, exploit dev | Small volume, irreplaceable. See `03_machine-level-language.md` |
| 47 | **Verilog / SystemVerilog** | 1984 Verilog (Moorby & Thomas); SystemVerilog IEEE 1800 | **Dataflow / concurrent RTL** + OO for verification | Static | n/a (hardware) | Digital design and verification | The industry default worldwide |
| 48 | **VHDL** | 1983, US DoD (VHSIC) | Dataflow / concurrent RTL | **Very strongly typed** | n/a | Digital design — Europe, aerospace, defence | Second to SystemVerilog globally, first in some sectors |
| 49 | **Chisel** | 2012, UC Berkeley | Hardware *generator* — a Scala eDSL | Static (Scala) | n/a | Parameterised RTL generation; RISC-V cores (Rocket, BOOM) | The most interesting idea in HDLs in decades |
| 50 | **Solidity** | 2014, Gavin Wood et al. | Contract-oriented, imperative | Static | EVM-managed | Ethereum smart contracts | Dominant in its niche; correctness-critical and unforgiving |
| 51 | **WebAssembly (Wat/Wasm)** | 2017, W3C | Stack machine, low-level target | Static | Linear memory, manual (host-managed) | Portable sandboxed compilation target | Standard; expanding well beyond browsers |
| 52 | **Forth** | 1970, Charles Moore | Stack-based, concatenative | Untyped | Manual | Boot firmware (Open Firmware), spacecraft, embedded | Tiny but immortal |
| 53 | **Smalltalk** | 1972, Alan Kay, Dan Ingalls, Adele Goldberg (Xerox PARC) | **Pure OO**, message passing | Dynamic | GC | The ancestor of GUIs, IDEs, refactoring, and OO itself | Historic; Pharo keeps it alive. Kay won the 2003 Turing Award |
| 54 | **Pascal / Delphi** | 1970 Pascal (Niklaus Wirth); 1995 Delphi (Borland) | Procedural / OO | Static, strong | Manual + RC (Delphi interfaces) | Teaching (historically); Windows desktop business apps | Delphi still commercially maintained. TIOBE #11 |
| 55 | **COBOL** | 1959, committee including **Grace Hopper**'s FLOW-MATIC | Procedural, record-oriented | Static | Static | **Banking, insurance, government mainframes** | Still running an enormous share of world financial transactions. TIOBE #19 |

## Part 3 — How many languages, and which

Learning a fifth language in the same family teaches you almost nothing. Learning one language per *paradigm and memory model* teaches you a great deal. A defensible portfolio for a computer engineer:

1. **C** — because it is the model of the machine, the ABI everything speaks, and the substrate of every OS and runtime.
2. **One memory-safe systems language** — **Rust** if you want the compile-time guarantee and are willing to pay the learning cost; **Go** if you want productivity and a GC you never think about; **Zig** if you want C with the sharp edges filed down and explicit allocators.
3. **Python** — the lingua franca of scripting, data and ML, and the fastest way to prototype anything.
4. **One JVM or .NET language** — Java, Kotlin or C#. This is where a very large fraction of paid backend work is.
5. **TypeScript** — if anything you build has a user interface.
6. **SQL** — not optional. It is used by 58.6% of all developers and understood deeply by very few.
7. **One functional language you will never be paid for** — Haskell, OCaml, Elixir or Clojure. It rewires how you think about state, and the payoff shows up in the other six.
8. **One HDL** — SystemVerilog or Chisel — if you touch hardware at all.

The order that works: Python (to get productive) → C (to get honest) → one of Rust/Go (to get employable in systems) → SQL and TypeScript (to get employable generally) → a functional language (to get better).

## Part 4 — Idiomatic snippets: the same idea in eight languages

"Hello world" distinguishes nothing. The task below — *sum the squares of the even numbers in a list* — exposes paradigm, typing and idiom in four lines.

**C** (explicit loop, explicit types, no abstraction):
```c
long sum_even_squares(const int *a, size_t n) {
    long total = 0;
    for (size_t i = 0; i < n; i++)
        if (a[i] % 2 == 0) total += (long)a[i] * a[i];
    return total;
}
```

**Rust** (iterator chain, zero-cost, inferred types):
```rust
fn sum_even_squares(a: &[i64]) -> i64 {
    a.iter().filter(|x| *x % 2 == 0).map(|x| x * x).sum()
}
```

**Go** (deliberately plain — Go has no iterator chains by design):
```go
func sumEvenSquares(a []int) int {
    total := 0
    for _, x := range a {
        if x%2 == 0 {
            total += x * x
        }
    }
    return total
}
```

**Python** (generator expression — lazy, allocation-free):
```python
def sum_even_squares(a):
    return sum(x * x for x in a if x % 2 == 0)
```

**Haskell** (pure, lazy, point-free-ish):
```haskell
sumEvenSquares :: [Int] -> Int
sumEvenSquares = sum . map (^2) . filter even
```

**SQL** (declarative — you describe the result, the planner picks the algorithm):
```sql
SELECT COALESCE(SUM(x * x), 0) FROM nums WHERE x % 2 = 0;
```

**APL** (array-first; the whole thing is one expression):
```apl
+/ 2 * ⍨ (0 = 2 | v) / v
```

**Elixir** (pipeline operator, immutable data, on the BEAM):
```elixir
def sum_even_squares(a) do
  a |> Enum.filter(&rem(&1, 2) == 0) |> Enum.map(&(&1 * &1)) |> Enum.sum()
end
```

And one that is not a computation at all — **SystemVerilog**, where the "code" is a circuit that exists continuously rather than a sequence that runs:

```systemverilog
module counter #(parameter W = 8) (
    input  logic         clk, rst_n,
    output logic [W-1:0] q
);
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) q <= '0;
        else        q <= q + 1'b1;
endmodule
```

The `always_ff` block does not "execute" — it *describes* a bank of W flip-flops with an asynchronous reset. That difference in what a program *is* is the reason hardware description languages sit in their own paradigm.


## Sources

- [2025 Stack Overflow Developer Survey — Technology](https://survey.stackoverflow.co/2025/technology)
- [TIOBE Index](https://www.tiobe.com/tiobe-index/) — snapshot served was **September 2024**
- [C23 — ISO/IEC 9899:2024](https://en.wikipedia.org/wiki/C23_(C_standard_revision))
- [Standard C++ status](https://isocpp.org/std/status)
- [Rust Edition Guide](https://doc.rust-lang.org/edition-guide/editions/index.html)

## Open questions

- **Creation years and creators** in the register are from general knowledge, not from per-language fetches. High-confidence items (C 1972 Ritchie, Python 1991 van Rossum, Rust 1.0 in 2015, Go 2009) are safe; less-cited dates (Odin 2016, Crystal 2014, Gleam 2016, Nim 2008) are `needs-verification` against each project's own history page.
- The TIOBE ranking cited is **September 2024**; a current index should replace it.
- Mojo and Carbon are moving quickly and their status statements will date fastest of anything in this file.
- The APL snippet in Part 4 is written from general knowledge and was **not** executed against an APL interpreter on this machine (unlike the assembly in `03_machine-level-language.md`); treat it as illustrative and `needs-verification`.
