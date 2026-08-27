---
id: compeng.language_deep_dives
title: Six languages in depth — C, C++, Rust, Python, JavaScript/TypeScript, Go
domain: 26_computer_engineering
tags: [c, cpp, rust, python, javascript, typescript, go, zig, undefined-behaviour, raii, ownership, gil, event-loop, tooling]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "C23 (C standard revision) — ISO/IEC 9899:2024", url: "https://en.wikipedia.org/wiki/C23_(C_standard_revision)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Standard C++ — current status", url: "https://isocpp.org/std/status", publisher: "Standard C++ Foundation", accessed: 2026-08-25}
  - {title: "Rust Edition Guide — editions", url: "https://doc.rust-lang.org/edition-guide/editions/index.html", publisher: "The Rust Project", accessed: 2026-08-25}
  - {title: "PEP 703 — Making the Global Interpreter Lock Optional in CPython", url: "https://peps.python.org/pep-0703/", publisher: "Python Software Foundation", accessed: 2026-08-25}
  - {title: "PEP 779 — Criteria for supported status for free-threaded Python", url: "https://peps.python.org/pep-0779/", publisher: "Python Software Foundation", accessed: 2026-08-25}
  - {title: "2025 Stack Overflow Developer Survey — Technology", url: "https://survey.stackoverflow.co/2025/technology", publisher: "Stack Overflow", accessed: 2026-08-25}
related: [compeng.languages_survey, compeng.machine_level, compeng.tooling]
unit_system: SI
---

# Six languages in depth — C, C++, Rust, Python, JavaScript/TypeScript, Go

**Summary.** Six languages carry most of the weight for a serious engineer in 2026. For each this file gives the *mental model* (the one idea that makes the rest of the language legible), the *traps* (what actually bites in production), the *tooling* (what a competent practitioner uses), and — the section most language documentation omits — *what the language is genuinely bad at*.

## Key facts

| Language | Current standard / version anchor | Verified source |
|---|---|---|
| C | **C23 = ISO/IEC 9899:2024**, published 31 October 2024; successor in progress as C2y | Wikipedia / ISO designation |
| C++ | **C++23 published**; C++26 being developed under a "decoupled" model where major work ships as feature-branch Technical Specifications | isocpp.org/std/status |
| Rust | Editions 2015 / 2018 / 2021 / 2024; editions change syntax only, never the compiled representation, and crates on different editions interoperate | Rust Edition Guide |
| Python | Free-threaded (no-GIL) build **officially supported but optional from 3.14** (PEP 779, Final). PEP 703 accepted 24 Oct 2023; targeted 3.13 for the `--disable-gil` build | peps.python.org |
| Rust standing | **Most-admired language, 72%** | Stack Overflow 2025 |
| JavaScript standing | **Most-used language, 66%**; TypeScript 43.6% | Stack Overflow 2025 |

## 1. C — the model of the machine

### Mental model
C is a portable assembler over an **abstract machine** that the standard defines but no hardware implements. Everything in C follows from three facts: memory is a flat array of bytes addressable by pointer; a value has a type that determines its size, alignment and interpretation; and the compiler is permitted to do *anything at all* to a program that violates the abstract machine's rules.

That third fact is the one that separates competent C programmers from the rest. C's speed does not come from the language being "close to the metal" — modern C is not close to any metal. It comes from **undefined behaviour**: the standard declines to specify what happens in a long list of situations, which frees the optimiser to assume those situations never occur.

### Undefined behaviour, concretely
- Signed integer overflow. `if (x + 1 < x)` is optimised to `false` — the compiler knows overflow cannot happen, because if it did the program would be undefined.
- Dereferencing NULL. A null check *after* a dereference is deleted, because the dereference proved the pointer non-null. This has caused real kernel vulnerabilities.
- Out-of-bounds array access, use after free, double free.
- Strict aliasing: accessing an object through a pointer of an incompatible type. This is why `-fno-strict-aliasing` exists and why the Linux kernel uses it.
- Data races. Two threads, one write, no synchronisation — undefined, not "whichever wins".
- Reading an uninitialised variable; shifting by ≥ the width of the type; modifying an object twice between sequence points.

The correct mental posture: UB is not "the machine does something unpredictable". It is "**the compiler is allowed to assume this code path is unreachable and delete everything downstream of it**".

### The standards, C89 → C23
- **C89/C90** (ANSI X3.159-1989 / ISO 9899:1990) — the K&R book describes an earlier dialect; C89 added function prototypes, `const`, `volatile`, the standard library.
- **C99** — `//` comments, `inline`, `restrict`, variable-length arrays, designated initialisers, `long long`, `<stdint.h>`, `_Bool`, compound literals, mixed declarations and statements.
- **C11** — `_Static_assert`, `_Generic`, atomics (`<stdatomic.h>`), threads (`<threads.h>`, widely unimplemented), anonymous structs/unions, `_Alignas`. VLAs became optional.
- **C17/C18** — a defect-fix release; no new features.
- **C23 (ISO/IEC 9899:2024, published 31 October 2024)** — the largest revision in two decades. Added `nullptr` and `nullptr_t`; made `true`, `false`, `bool`, `static_assert`, `alignas`, `alignof` and `thread_local` real keywords; `constexpr` for objects; `typeof`; `auto` type inference; `_BitInt(N)` bit-precise integers; `char8_t`; binary literals `0b`; digit separators; C++11-style `[[attributes]]`; checked arithmetic (`ckd_add`, `ckd_sub`, `ckd_mul`); `<stdbit.h>` bit utilities; `strdup`/`strndup`/`memset_explicit`; and `%b` in printf. **Removed:** trigraphs, K&R function definitions, and non-two's-complement signed representations.

### Traps
`strcpy`/`strcat`/`sprintf` (unbounded); `gets` (removed in C11 and never safe); integer promotion surprises (`char + char` is `int`); `sizeof` on an array parameter (it decayed to a pointer); `char` signedness being implementation-defined; forgetting that `malloc` can return NULL; `errno` semantics; the `volatile` misconception (it is for memory-mapped I/O and signal handlers, **not** a synchronisation primitive).

### Tooling
`gcc`/`clang` with `-Wall -Wextra -Wpedantic -Werror`; **sanitizers** (`-fsanitize=address,undefined`, and `-fsanitize=thread`) — these turn most UB from silent corruption into a loud crash and are the single biggest quality improvement available to a C programmer; Valgrind for cases sanitizers miss; `clang-tidy` and `cppcheck` for static analysis; `gdb`/`lldb`; `perf`; Make or CMake; `clang-format`. For fuzzing, libFuzzer or AFL++.

### What C is genuinely bad at
Strings (there is no string type, only a convention about a trailing zero byte). Generic containers (you get `void*` and macros, or you write it again for each type). Error handling (return codes that everyone forgets to check). Concurrency (`<threads.h>` is barely implemented; everyone uses pthreads or Win32). Modularity (a header is textual inclusion, not a module; C23 still has no module system). Dependency management (there is no package manager, and this is a real productivity tax). And — most importantly — **safety**: memory-safety defects in C and C++ codebases account for a large and well-documented share of severe vulnerabilities, which is why Microsoft, Google, the NSA and CISA have all published guidance pushing new systems code toward memory-safe languages.

## 2. C++ — abstraction without overhead, at enormous cost in complexity

### Mental model
C++'s organising principle is **zero-overhead abstraction**: you should not pay for what you do not use, and what you do use should be as efficient as hand-written equivalent code. Everything else follows — templates so generic code compiles to specialised code, RAII so resource management costs nothing at run time, move semantics so value semantics do not force copies.

**RAII (resource acquisition is initialisation)** is C++'s single best idea and the one most worth stealing. A resource's lifetime is bound to an object's lifetime; the destructor releases it; scope exit — including by exception — is guaranteed to run destructors in reverse construction order. `std::unique_ptr`, `std::lock_guard`, `std::fstream` are all the same pattern. Correct modern C++ contains almost no explicit `delete` and no explicit `unlock`.

**Move semantics** (C++11) closed the last hole. An rvalue reference `T&&` binds to a temporary, letting a constructor *steal* its guts rather than copy them. This is why `std::vector<std::string>` can be returned from a function for free, and why the rule of three became the rule of five, then the rule of zero (write no special members at all and let members manage themselves).

**Templates** are a compile-time functional language over types. Ordinary generic code is easy; the trouble is that template metaprogramming grew organically and produced SFINAE, tag dispatch and error messages measured in kilobytes. **Concepts** (C++20) finally let you constrain a template and get a sane diagnostic.

### The standards, C++11 → C++23
- **C++11** — the language became a different one: `auto`, range-`for`, lambdas, move semantics, `nullptr`, `constexpr`, variadic templates, smart pointers, the memory model and `std::thread`, `std::function`, `enum class`, uniform initialisation.
- **C++14** — generic lambdas, relaxed `constexpr`, `std::make_unique`.
- **C++17** — structured bindings, `if constexpr`, `std::optional`/`variant`/`any`/`string_view`, filesystem, parallel algorithms, guaranteed copy elision, fold expressions.
- **C++20** — the second great leap: **concepts**, **ranges**, **coroutines**, **modules**, `<format>`, the spaceship operator `<=>`, designated initialisers, `constinit`/`consteval`, `std::span`, calendar and time zones.
- **C++23** — `std::expected`, `std::mdspan`, `std::print`, `std::flat_map`, `if consteval`, deducing `this`, multidimensional `operator[]`, "modules for the standard library" (`import std;`).
- **C++26** — in progress. isocpp.org describes a **decoupled** development model in which major pieces of work progress independently as feature-branch Technical Specifications so vendors can implement and gather feedback before standardisation. Reflection, contracts, `std::execution` (senders/receivers) and a profiles-based safety story are the headline items; **treat any specific C++26 feature list as `needs-verification` until the standard ships**.

### The committee process
ISO/IEC JTC1/SC22/**WG21**. Proposals are written as numbered papers (P-numbers), presented in study groups (SG1 concurrency, SG7 reflection, SG15 tooling, and many others), advanced through the Evolution and Library Evolution working groups, then Core and Library working groups for wording, then plenary vote. Standards ship on a three-year cadence: C++11, 14, 17, 20, 23, 26. It is slow, consensus-driven, and answerable to a vast installed base that cannot be broken — which explains both its conservatism and its accumulated complexity.

### Traps
Object slicing when a derived object is assigned to a base by value. Dangling references from `std::string_view` and iterators (C++ gives you no borrow checker). `std::shared_ptr` cycles. Undefined behaviour inherited wholesale from C, plus its own. Exception safety guarantees that are easy to state and hard to hold. The `const` correctness discipline. `std::vector<bool>` (a proxy-returning special case that is not a container of `bool`). Initialisation — there are more than a dozen forms and they are not equivalent. Build times: heavy template use can turn a small change into a multi-minute rebuild.

### Tooling
CMake (dominant, unloved) or Bazel; vcpkg or Conan for packages; clang-tidy, clang-format, include-what-you-use; sanitizers (as for C — indispensable); Compiler Explorer; Catch2, GoogleTest or doctest; `perf`, VTune, Tracy; `ccache` and modules or precompiled headers to survive build times.

### What C++ is genuinely bad at
Being learned. The language is genuinely enormous and its old and new idioms coexist, so a codebase is usually three C++s at once. Compile times. Package management (still no standard answer, decades in). Error messages, though concepts helped. ABI stability constrains the standard library so tightly that known-suboptimal designs (`std::regex`, `std::unordered_map`) cannot be fixed. And it cannot offer memory safety by default — the safety work in C++26 is opt-in profiles, not a guarantee.

## 3. Rust — safety as a type-system property

### Mental model
Every value has exactly one **owner**. When the owner goes out of scope, the value is dropped. You may **borrow** a value: any number of shared references `&T` **or** exactly one mutable reference `&mut T`, never both at once. Every reference has a **lifetime** the compiler verifies does not outlive the referent.

That single rule — *no aliasing plus mutation* — buys memory safety and data-race freedom simultaneously, at compile time, with no runtime cost. It is the most significant idea in mainstream language design since garbage collection, and it is why Rust is the **most-admired language at 72%** in the 2025 Stack Overflow survey.

```rust
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];   // shared borrow of v
    v.push(4);           // ERROR: cannot borrow `v` as mutable
    println!("{first}"); //        while it is borrowed as immutable
}
```

That program is rejected. In C++ the equivalent compiles, and `push` may reallocate the buffer, leaving `first` dangling. Rust turns a class of production bug into a compile error.

**Traits** are Rust's abstraction mechanism — closer to Haskell's type classes than to Java's interfaces. They support static dispatch (monomorphised generics, zero cost) and dynamic dispatch (`dyn Trait`, a fat pointer with a vtable). Key traits define the language's semantics: `Copy`, `Clone`, `Drop`, `Send` (safe to move between threads), `Sync` (safe to share between threads), `Iterator`, `Deref`. `Send` and `Sync` are what make "fearless concurrency" real — the compiler refuses to share a `Rc<T>` across threads because `Rc` is not `Sync`.

**`unsafe`** does not disable the borrow checker. It unlocks five extra abilities: dereferencing raw pointers, calling `unsafe` functions, implementing `unsafe` traits, mutating statics, and accessing union fields. The contract is that *you* uphold the invariants the compiler can no longer check, and the discipline is to wrap `unsafe` in a small, audited, safe abstraction. Every `Vec`, `Mutex` and `HashMap` in the standard library is safe code built over an `unsafe` core.

### Editions
Rust ships a new *edition* every three years — 2015, 2018, 2021, 2024. An edition may make backwards-incompatible **syntactic** changes (introducing `async` as a keyword, for example), and `cargo fix` automates migration. Crucially, per the Rust Edition Guide: editions do **not** change the internal representation code compiles to, and crates on different editions interoperate seamlessly. The stability promise holds while the language still evolves — a genuinely well-engineered social mechanism.

### The ecosystem
`cargo` is the best build-and-package tool in any systems language: build, test, benchmark, document, publish, dependency resolution and a lockfile in one binary. crates.io is the registry. The load-bearing crates: `serde` (serialisation), `tokio` (async runtime), `rayon` (data parallelism), `clap` (CLI), `anyhow`/`thiserror` (errors), `axum`/`actix-web` (HTTP), `sqlx`/`diesel` (databases), `criterion` (benchmarks), `bindgen`/`cxx` (FFI). Rust is now in the Linux kernel (Rust-for-Linux) and in Windows kernel components, and Android's Rust code has been reported to carry far fewer memory-safety defects than the C++ it replaced.

### Traps
Fighting the borrow checker by reaching for `Rc<RefCell<T>>` — which moves the check to run time and can panic. Self-referential structs (need `Pin`, or an arena, or indices instead of references). Async Rust is a second language layered on the first: `Pin`, `Send` bounds across `.await`, cancellation semantics, and function colouring. Long compile times. Error-handling ceremony until you settle on `thiserror` for libraries and `anyhow` for applications. The learning cliff is real and is measured in months, not weeks.

### What Rust is genuinely bad at
Prototyping — it forces you to resolve design questions the compiler will not let you defer. Graphs and doubly-linked structures with cyclic references (use indices into a `Vec`). Compile times. Dynamic plugin systems, because there is no stable ABI. GUI, where the ecosystem remains immature. And a large, mostly unavoidable tax on programmer ramp-up time.

## 4. Python — the object model and the GIL

### Mental model
**Everything is an object**, including classes, functions and modules. Names are not boxes; they are **bindings** in a namespace dictionary that point at objects. Assignment rebinds a name; it never copies. This single fact explains the mutable-default-argument trap, the aliasing surprises, and why `is` and `==` differ.

Attribute lookup is a defined protocol: instance `__dict__`, then the type's MRO (computed by C3 linearisation), with descriptors (`__get__`/`__set__`) intercepting — which is how `property`, `classmethod`, `staticmethod` and every ORM field work. Operator overloading, iteration, context managers (`with`) and async are all **dunder protocols**: `__add__`, `__iter__`, `__enter__`, `__await__`. Learn the protocols and Python stops having special cases.

### CPython internals
The reference implementation compiles source to bytecode (`dis` shows it) and runs it in an evaluation loop. Since 3.11 that loop is a **specialising adaptive interpreter** (PEP 659) that rewrites hot bytecodes into type-specialised variants; 3.12 added a per-interpreter GIL; 3.13 introduced an experimental JIT and the free-threaded build; 3.14 promoted free-threading to supported. Objects are reference-counted, with a generational cycle detector for reference cycles. Every object carries a header; `int` is arbitrary-precision; small integers and short strings are interned.

### The GIL and the free-threaded work
The **Global Interpreter Lock** is one mutex that guarantees only one thread executes Python bytecode at a time. It makes reference counting cheap and single-threaded code fast, and it makes CPU-bound threading useless — which is why the ecosystem uses `multiprocessing`, or drops into C/NumPy (which release the GIL), or uses async for I/O.

**PEP 703** ("Making the Global Interpreter Lock Optional in CPython") was accepted by the Steering Council on **24 October 2023**, with the condition that the rollout be gradual and reversible. It adds a `--disable-gil` build using biased reference counting, per-object locking, stop-the-world GC pauses and mimalloc. Its own measured costs on pyperformance 1.0.6 were **5–6% single-threaded** and **7–8% multi-threaded** overhead. Its phased plan: 2024 / Python 3.13, ship the build option with two ABIs; 2026–2027, a runtime-controlled GIL with a single ABI; 2028–2030, GIL disabled by default.

**PEP 779** then defined the criteria for Phase II — *officially supported but still optional* — for **Python 3.14**: a maximum 15% pyperformance slowdown versus the GIL build, a target of ≤20% higher memory use (geometric mean), API stability under PEP 387, and adequate internals documentation. It is Final.

The practical consequence for 2026: free-threaded Python is real and supported, but it is not the default, extension modules must be rebuilt for it, and a great deal of C-extension ecosystem work remains.

### Traps
Mutable default arguments (`def f(x=[])` — the list is created once). Late-binding closures in loops. `is` versus `==`. Shallow versus deep copy. Integer caching making `is` appear to work for small numbers. Exception handling that swallows everything with bare `except:`. Import cycles and the `__init__.py` side-effect trap. Packaging — historically the worst part of the language, now improving via `pyproject.toml` and `uv`.

### Tooling
`uv` (fast resolver, installer and virtual-environment manager; increasingly the default) or `poetry`/`pip-tools`; `ruff` (linter and formatter, replacing flake8/isort/black); `mypy` or `pyright` for static type checking; `pytest` plus `hypothesis` for property-based testing; `cProfile`, `py-spy`, `scalene`, `memray` for profiling; `pdb`/`ipdb`.

### The scientific stack
NumPy (ndarray and broadcasting — the foundation), SciPy, pandas / Polars, Matplotlib, scikit-learn, and the ML frameworks PyTorch and JAX. The key insight: **Python is the orchestration layer, not the compute layer.** The compute is C, C++, Fortran, CUDA or LLVM-compiled kernels, and Python's job is to be the most pleasant possible interface to it. Numba, Cython and JAX's tracing JIT blur the boundary.

### What Python is genuinely bad at
CPU-bound performance without dropping to C. True multi-core threading, until free-threading matures. Deployment — shipping a Python application to a machine you do not control is still unpleasant. Mobile. Large refactors in untyped codebases. Memory footprint. And startup time, which rules it out of much CLI and serverless work.

## 5. JavaScript and TypeScript — the event loop and a structural type system

### Mental model — JavaScript
**Single-threaded, non-blocking, event-driven.** One call stack; a task queue; an event loop that pulls the next task when the stack empties. Blocking the stack freezes everything — there is no other thread to take over.

The precise ordering matters and is asked in every interview: run the current task to completion → drain the **entire microtask queue** (promise callbacks, `queueMicrotask`, `MutationObserver`) → render (in a browser) → take one **macrotask** (`setTimeout`, I/O completion, events) → repeat. Which is why a promise chain always runs before a `setTimeout(fn, 0)` queued earlier.

**Prototypes, not classes.** Every object has a hidden link to a prototype object; property lookup walks that chain. `class` syntax (ES2015) is sugar over it. `this` is determined by *how a function is called*, not where it is defined — except for arrow functions, which capture `this` lexically and are the reason most `this` bugs disappeared.

**The module mess** is real history, not a complaint: no modules at all → IIFEs and globals → CommonJS (`require`, synchronous, Node) → AMD (`define`, asynchronous, browser) → UMD (both) → **ESM** (`import`/`export`, the actual standard, static and analysable). Node supports both CommonJS and ESM with different resolution semantics, `"type": "module"` in `package.json`, dual-package hazards, and conditional exports. This is the most common source of build failure in the ecosystem.

### TypeScript
A **structural, gradual** type layer over JavaScript that erases completely at compile time — TypeScript emits JavaScript and adds no runtime checks whatsoever. Its type system is unusually powerful for a mainstream language: union and intersection types, literal types, discriminated unions with exhaustiveness checking, generics with constraints, conditional types (`T extends U ? X : Y`), mapped types, template literal types, and `infer`. It is Turing-complete, which is both an achievement and a warning.

`strict` mode (especially `strictNullChecks`) is where the value is. Without it TypeScript is decoration; with it, an entire class of null/undefined bugs becomes a compile error.

### Traps
`==` versus `===` and the coercion table. `NaN !== NaN`. Floating-point money (`0.1 + 0.2`). `this` binding. Hoisting, and the temporal dead zone for `let`/`const`. `Array.prototype.sort` sorting numbers lexicographically by default. Prototype pollution as a security class. Unhandled promise rejections. In TypeScript: `any` silently disabling checking, type assertions (`as`) lying to the compiler, and the fact that **types do not exist at runtime** — so validating external data needs a runtime validator (Zod, Valibot, io-ts), not a type annotation.

### Tooling
Node.js, Deno or Bun as runtimes; `npm`/`pnpm`/`yarn` for packages (`pnpm` for its content-addressed store); Vite (dev and build), esbuild and SWC (fast transpilers), Rollup/Rspack for bundling; `tsc` for type checking; ESLint and Prettier — increasingly replaced by Biome or by `oxlint`; Vitest or Jest for tests, Playwright for end-to-end; Chrome DevTools, which remains the best-in-class debugger and profiler of any language.

### What JavaScript/TypeScript is genuinely bad at
CPU-bound work (Web Workers and WASM exist, but the ergonomics are poor). Numerics — one number type, IEEE 754 double, and `BigInt` bolted on later. Memory control. Dependency-tree size and supply-chain risk: a trivial project routinely pulls in hundreds of transitive packages, and this has repeatedly been exploited. Toolchain churn, which is a genuine and continuing tax. And TypeScript specifically: its unsoundness is deliberate — bivariant method parameters, `any`, and unchecked assertions mean the type system is a very good bug-finder, not a proof.

## 6. Go — deliberate simplicity for infrastructure

### Mental model
**Simplicity is the feature.** Go was designed at Google for large teams building network services, and every decision optimises for readability, fast compilation and quick onboarding over expressiveness. There is one formatting style (`gofmt`, non-negotiable), one way to handle errors, no inheritance, no exceptions, no operator overloading, and — for its first thirteen years — no generics.

**Concurrency is CSP.** Goroutines are cheap user-space threads (a few kilobytes of growable stack) multiplexed by the runtime onto OS threads. **Channels** communicate between them. Rob Pike's slogan — *don't communicate by sharing memory; share memory by communicating* — is the design. `select` multiplexes channel operations. `context.Context` carries cancellation and deadlines through call trees and is idiomatic in every API that does I/O.

**Interfaces are structural and implicit.** A type satisfies an interface by having the methods; there is no `implements` declaration. This means you can define an interface *at the point of use*, describing what the consumer needs rather than what the producer offers — the single most underrated feature in the language.

**Errors are values.** `if err != nil { return fmt.Errorf("doing x: %w", err) }`, endlessly. It is verbose and it is deliberate: every error is visible at the call site, and `errors.Is`/`errors.As` plus `%w` wrapping give you typed inspection without exceptions.

```go
func fetchAll(ctx context.Context, urls []string) ([]int, error) {
    g, ctx := errgroup.WithContext(ctx)
    sizes := make([]int, len(urls))
    for i, u := range urls {
        i, u := i, u          // pre-Go 1.22 loop-variable capture fix
        g.Go(func() error {
            n, err := fetch(ctx, u)
            if err != nil {
                return fmt.Errorf("fetch %s: %w", u, err)
            }
            sizes[i] = n
            return nil
        })
    }
    return sizes, g.Wait()
}
```

### Traps
`nil` interface values that are not `nil` (a nil pointer stored in an interface makes the interface non-nil — the classic Go gotcha). Slice aliasing after `append` — a slice shares its backing array until it grows. Loop-variable capture, fixed in Go 1.22 by giving each iteration its own variable, but still present in older code. Goroutine leaks from unbuffered channels no one reads. `defer` in a loop. Nil map writes panicking while nil map reads do not. Error-handling verbosity, which is a real cost even when it is the right trade.

### Tooling
The best-integrated standard toolchain of any language: `go build`, `go test` (with coverage, benchmarks and fuzzing built in), `go fmt`, `go vet`, `go mod`, `go doc`, and `pprof` — a production-grade CPU, heap, block and mutex profiler included in the standard library. Add `golangci-lint`, `delve` for debugging, and the race detector (`go test -race`), which is one of the most valuable tools in any ecosystem.

### What Go is genuinely bad at
Expressiveness — generics arrived in 1.18 and remain deliberately restricted (no method type parameters, no higher-kinded types). The type system cannot express sum types, so error and state modelling is weaker than in Rust or a typed FP language. GC pause behaviour rules it out of hard real-time. It has no place in systems programming below the runtime — no manual memory control. Its dependency on a runtime makes small static embedding awkward. And the culture's resistance to abstraction produces a lot of copy-paste.

### The alternative: Zig
Where Go optimises for team simplicity, **Zig** optimises for *transparency of cost*. No hidden control flow, no hidden allocation — every function that allocates takes an `Allocator` parameter, which makes arena and testing allocators trivial and makes leaks structurally visible. **`comptime`** replaces macros, generics and constant folding with one idea: ordinary Zig code executed at compile time, with types as first-class compile-time values. Error handling uses error unions and `try`. `defer`/`errdefer` handle cleanup. And `zig cc` is a drop-in C cross-compiler that ships every libc it targets, which is why projects with no other Zig code adopt it as a build tool. Zig is **64% admired** in the 2025 Stack Overflow survey despite being pre-1.0. Its weaknesses are exactly that: pre-1.0 churn, no memory-safety guarantee (it is safer than C, not safe), and a small ecosystem.

## Sources

- [C23 — ISO/IEC 9899:2024](https://en.wikipedia.org/wiki/C23_(C_standard_revision))
- [Standard C++ status and the decoupled C++26 model](https://isocpp.org/std/status)
- [Rust Edition Guide — editions](https://doc.rust-lang.org/edition-guide/editions/index.html)
- [PEP 703 — Making the GIL optional](https://peps.python.org/pep-0703/)
- [PEP 779 — Criteria for supported status for free-threaded Python](https://peps.python.org/pep-0779/)
- [2025 Stack Overflow Developer Survey — Technology](https://survey.stackoverflow.co/2025/technology)

## Open questions

- Per-standard C and C++ feature lists for C99, C11, C++11–C++23 are from general knowledge; only the **C23** list and the **C++23-published / C++26-in-progress** status were fetched. Verify specific features against the standard or cppreference before relying on them.
- C++26 contents are described only at the level isocpp.org states (decoupled TS-based development). Named features are `needs-verification`.
- The claim that Android's Rust code shows materially fewer memory-safety defects than the C++ it replaced is well documented in Google's security blog but was **not fetched** for this file — `needs-verification`.
- Rust edition years (2015/2018/2021/2024) are stated from general knowledge; the Edition Guide page fetched described the mechanism but did not enumerate the editions.
