---
id: compeng.machine_level
title: Machine and assembly language — from bits to the boot process
domain: 26_computer_engineering
tags: [assembly, machine-code, x86-64, aarch64, risc-v, isa, abi, calling-convention, pipeline, cache, virtual-memory, elf, linking, ieee-754, twos-complement, simd]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "x86 calling conventions (System V AMD64 ABI and Microsoft x64)", url: "https://en.wikipedia.org/wiki/X86_calling_conventions", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "RISC-V ratified specifications", url: "https://riscv.org/specifications/ratified/", publisher: "RISC-V International", accessed: 2026-08-25}
  - {title: "C23 (C standard revision) — ISO/IEC 9899:2024", url: "https://en.wikipedia.org/wiki/C23_(C_standard_revision)", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Local toolchain output — gcc 13.3.0 (Ubuntu) and clang 18.1.3", url: "https://gcc.gnu.org/", publisher: "GNU Project / LLVM (generated on this machine, 2026-08-25)", accessed: 2026-08-25}
related: [compeng.overview, compeng.curriculum, compeng.language_deep_dives, semiconductors.overview]
unit_system: SI
---

# Machine and assembly language — from bits to the boot process

**Summary.** This is the load-bearing file of the domain: the layer where software stops being an abstraction and becomes voltages and state. It covers number representation, the von Neumann and Harvard models, three instruction set architectures compared side by side, calling conventions, the pipeline and everything that makes it go wrong, SIMD, the memory hierarchy, virtual memory, interrupts, boot, ELF and linking — and it ends with **real, machine-generated** x86-64, AArch64 and RISC-V listings of the same C function, produced on this machine with gcc 13.3.0 and clang 18.1.3.

## Key facts

| Item | Value |
|---|---|
| System V AMD64 integer argument registers, in order | **RDI, RSI, RDX, RCX, R8, R9** |
| System V AMD64 float argument registers | XMM0–XMM7 |
| System V AMD64 callee-saved | **RBX, RSP, RBP, R12–R15** |
| System V AMD64 red zone | **128 bytes** below RSP (leaf functions; not usable in signal handlers) |
| System V AMD64 stack alignment | 16 bytes (32 for AVX types, 64 for AVX-512) |
| Microsoft x64 integer arg registers | RCX, RDX, R8, R9 + **32-byte shadow space** |
| Microsoft x64 callee-saved | RBX, RBP, RDI, RSI, RSP, R12–R15 |
| AArch64 integer arg registers (AAPCS64) | X0–X7; return in X0 |
| RISC-V arg registers | a0–a7 (= x10–x17); return in a0/a1 |
| IEEE 754 binary64 layout | 1 sign, 11 exponent (bias 1023), 52 stored mantissa bits |
| ELF64 magic | `7f 45 4c 46 02 01 01 00` (`\x7fELF`, class 64, little-endian, v1) |
| Signed integers in C | **two's complement only**, as of C23 (ISO/IEC 9899:2024) |

> ⚠️ Signed integer *overflow* is still undefined behaviour in C and C++ even though C23 mandates two's complement *representation*. The two are separate questions. Compilers exploit the UB aggressively — `for (int i = 0; i <= n; i++)` is optimised on the assumption it cannot wrap.

## 1. Number representation

### Binary and hexadecimal
Hex exists because one hex digit is exactly four bits, so a byte is exactly two hex digits and a 64-bit word is exactly sixteen. `0xDEADBEEF` is 1101 1110 1010 1101 1011 1110 1110 1111. C23 finally added binary literals (`0b1010`) and digit separators, both long available in other languages.

### Two's complement
A signed *n*-bit value is interpreted as `-b_{n-1}·2^{n-1} + Σ b_i·2^i`. Its virtues: one representation of zero, and addition, subtraction and multiplication are bit-identical to the unsigned operations, so the ALU needs only one adder. Negation is "invert and add one". The asymmetry — `INT_MIN` has no positive counterpart — is where bugs live: `abs(INT_MIN)` is UB, and `-INT_MIN == INT_MIN`.

C23 (ISO/IEC 9899:2024, published 31 October 2024) removed sign-magnitude and ones'-complement representations from the standard entirely, along with trigraphs and K&R function definitions.

### IEEE 754 floating point
`binary32` (float): 1 sign + 8 exponent (bias 127) + 23 stored mantissa bits. `binary64` (double): 1 + 11 (bias 1023) + 52. The leading mantissa bit is implicit `1` for normals, giving 24 and 53 bits of significand respectively.

What every engineer must internalise:
- **0.1 is not representable.** `0.1 + 0.2 != 0.3` in every IEEE 754 language.
- **Addition is not associative.** `(a+b)+c != a+(b+c)`. This is why `-ffast-math` changes results and why reproducible parallel reductions are hard.
- **Special values:** ±0 (distinct bit patterns, compare equal), ±∞, and NaN. NaN is unordered: `x != x` is the portable NaN test.
- **Subnormals** fill the gap around zero at the cost of reduced precision and, on some hardware, a large performance penalty (hence flush-to-zero modes).
- **Rounding** is round-to-nearest-ties-to-even by default. Machine epsilon for binary64 is 2⁻⁵² ≈ 2.22e-16.
- **bfloat16** (1+8+7) trades mantissa for the same exponent range as float32, which is why ML hardware adopted it: gradients need range, not precision. **FP8** formats (E4M3, E5M2) push this further.

## 2. Machine models

**Von Neumann:** one memory holding both instructions and data, one bus. Simple, flexible (self-modifying code, JIT compilation, loading programs as data) — and bottlenecked, since instruction fetch and data access contend for the same path.

**Harvard:** separate instruction and data memories with separate buses. Used in DSPs and most microcontrollers (AVR, PIC), because you can fetch an instruction and a datum in the same cycle and the instruction memory can be flash while data is SRAM.

**Modified Harvard:** what every modern CPU actually is. A unified main memory (von Neumann to software) with split L1 instruction and L1 data caches (Harvard where it matters for bandwidth). This is why self-modifying code and JITs require explicit instruction-cache invalidation — the I-cache does not snoop D-cache writes on ARM and RISC-V. On AArch64 you need `dc cvau` + `dsb ish` + `ic ivau` + `dsb ish` + `isb`; on RISC-V, `fence.i`. x86 is the outlier that keeps the caches coherent in hardware, which is why x86 JIT authors are often surprised when they port.

## 3. Instruction set architectures compared

| | x86-64 | AArch64 | RISC-V (RV64GC) |
|---|---|---|---|
| Origin | Intel 8086 (1978), 64-bit extension by AMD (2000) | Arm (ARMv8-A, 2011) | UC Berkeley (2010), RISC-V International |
| Philosophy | CISC | Load–store RISC | Load–store RISC, minimal base + extensions |
| Instruction length | **1–15 bytes, variable** | Fixed 32-bit | 32-bit, with optional 16-bit "C" compressed |
| General registers | 16 (RAX…R15); APX adds 32 | 31 (X0–X30) + SP + XZR | 32 (x0–x31), x0 hardwired to zero |
| Condition codes | Yes (EFLAGS), implicit | Yes (NZCV), explicit `S` suffix | **None** — compare-and-branch fused |
| Addressing modes | Very rich: `[base + index*scale + disp]` | Moderate; pre/post-index, register offset | **Only `reg + immediate`** |
| Memory model | TSO (strong) | Weakly ordered, release/acquire built in | Weak (RVWMO), or Ztso |
| Licensing | Intel/AMD cross-licence; effectively closed | Commercial licence from Arm | **Open, royalty-free** |
| Typical use | Desktop, server, HPC | Mobile, Apple silicon, AWS Graviton, embedded | Embedded, accelerators, research, increasing commercial use |

**Why RISC-V matters.** Not because it is technically superior — AArch64 is an excellent ISA and RISC-V's minimalism creates real code-density and instruction-count costs. It matters because the *ISA is the most important interface in computing* and, for the first time, it is a standard rather than a product. Its consequences:

1. **No licence fee and no licensor veto.** Anyone can implement it. Startups, universities and national programmes (notably China's, in response to export controls) build cores without negotiating with Arm.
2. **Modularity.** RV32I/RV64I is a genuinely tiny base (about 40 instructions). Extensions bolt on: M (multiply/divide), A (atomics), F/D (float/double), C (compressed), V (vector), plus a long tail of Zb*, Zk*, Zi* extensions. "RV64GC" is the common general-purpose bundle (IMAFD + C).
3. **Profiles bring order.** Because extension soup fragments software, RISC-V International defines *profiles* (RVA20, RVA22, RVA23) that name a mandatory set an application-class OS can rely on.
4. **It became a curriculum standard.** Patterson & Hennessy rewrote *Computer Organization and Design* around it, and Harris & Harris did the same. A student in 2026 learns computer architecture in RISC-V.

The original Berkeley technical reports are still listed by RISC-V International: user-level ISA v1.0 (2011, UCB/EECS-2011-62), v2.0 (2014), v2.1 (2016), privileged architecture v1.7 (2015) and v1.9 (2016). Current ratified specifications live in the RISC-V docs library.

## 4. Registers, addressing modes and the stack

**Registers** are the only storage the ALU touches directly — roughly one cycle of latency against ~4 cycles for L1 and ~200–300 cycles for DRAM. Register allocation is therefore the single most valuable thing a compiler back end does.

**Addressing modes** on x86-64 collapse whole address computations into one instruction. The `lea` (load effective address) instruction is the clearest example: it computes `base + index*scale + disp` without touching memory, so compilers use it as a three-operand add-and-shift. You will see this below.

**The stack** grows downward on all three architectures. A typical frame contains, from high address to low: the arguments that did not fit in registers, the return address (pushed by `call` on x86; placed in the link register `x30`/`ra` on AArch64 and RISC-V and spilled by the callee), the saved frame pointer, saved callee-saved registers, and local variables.

### Calling conventions

**System V AMD64 ABI** (Linux, macOS, BSD): first six integer/pointer arguments in RDI, RSI, RDX, RCX, R8, R9; first eight floats in XMM0–XMM7; return in RAX (128-bit in RAX:RDX), floats in XMM0/XMM1. Callee-saved: RBX, RSP, RBP, R12–R15; everything else is caller-saved. Stack 16-byte aligned at the call instruction. A **128-byte red zone** below RSP may be used by leaf functions without adjusting the stack pointer — but not by signal handlers, which is why kernel code compiles with `-mno-red-zone`.

**Microsoft x64** differs enough to matter: only RCX, RDX, R8, R9 for integers; RDI and RSI are *callee-saved*; and the caller must allocate 32 bytes of **shadow space** before every call regardless of argument count.

**AAPCS64** (AArch64): X0–X7 for the first eight integer/pointer arguments and for return; X8 is the indirect result register; X9–X15 caller-saved; X19–X28 callee-saved; X29 frame pointer, X30 link register. SP must be 16-byte aligned at all times.

**RISC-V**: a0–a7 (x10–x17) for arguments and a0/a1 for return; ra (x1) is the link register; sp (x2) is 16-byte aligned; s0–s11 are callee-saved; t0–t6 caller-saved. Register x0 always reads zero, which is what lets RISC-V synthesise `mv`, `nop`, `not` and unconditional jumps out of a small instruction set.

## 5. Real listings: the same function on three ISAs

The source, compiled on this machine on 2026-08-25:

```c
/* sum.c */
int sum_to(int n) {
    int total = 0;
    for (int i = 1; i <= n; i++)
        total += i;
    return total;
}
```

### x86-64, gcc 13.3.0, `-O0` (`gcc -S -O0 -fno-asynchronous-unwind-tables sum.c`)

```gas
sum_to:
        endbr64                      # CET landing pad — indirect-branch target marker
        pushq   %rbp                 # save caller's frame pointer
        movq    %rsp, %rbp           # establish this frame
        movl    %edi, -20(%rbp)      # spill arg n (RDI, SysV arg 1) to the stack
        movl    $0,   -8(%rbp)       # total = 0
        movl    $1,   -4(%rbp)       # i = 1
        jmp     .L2                  # jump to the condition test
.L3:
        movl    -4(%rbp), %eax       # load i
        addl    %eax, -8(%rbp)       # total += i   (read-modify-write to memory)
        addl    $1, -4(%rbp)         # i++
.L2:
        movl    -4(%rbp), %eax       # load i
        cmpl    -20(%rbp), %eax      # compare i with n, setting EFLAGS
        jle     .L3                  # if i <= n, loop
        movl    -8(%rbp), %eax       # return value in EAX
        popq    %rbp
        ret
```

Every variable lives in memory. This is what `-O0` means: no register allocation beyond scratch use of EAX. Note `endbr64` — Intel CET indirect-branch tracking, emitted by default on modern distributions.

### x86-64, gcc 13.3.0, `-O2` — and the machine code

```gas
sum_to:
        endbr64
        testl   %edi, %edi           # n <= 0 ?
        jle     .L4
        leal    1(%rdi), %ecx        # ecx = n + 1  (loop bound)
        xorl    %edx, %edx           # total = 0
        andl    $1, %edi             # n & 1 — parity, for the peeled iteration
        movl    $1, %eax             # i = 1
        je      .L3                  # n even → straight into the unrolled loop
        movl    $2, %eax             # n odd → peel one iteration: i = 2
        movl    $1, %edx             #                             total = 1
        cmpl    %ecx, %eax
        je      .L1
.L3:
        leal    1(%rdx,%rax,2), %edx # total = total + 2*i + 1  — TWO iterations at once
        addl    $2, %eax             # i += 2
        cmpl    %ecx, %eax
        jne     .L3
.L1:
        movl    %edx, %eax
        ret
.L4:
        xorl    %edx, %edx
        movl    %edx, %eax
        ret
```

GCC has unrolled the loop by two and folded the two additions `total += i; total += (i+1)` into a single `lea` computing `total + 2i + 1`. It peels one iteration when `n` is odd. This is the ordinary, unremarkable behaviour of an optimising compiler, and it is why reasoning about performance from source alone is unreliable.

The corresponding machine code (`gcc -c -O2 sum.c && objdump -d sum.o`):

```
0000000000000000 <sum_to>:
   0:   f3 0f 1e fa             endbr64
   4:   85 ff                   test   %edi,%edi
   6:   7e 38                   jle    40 <sum_to+0x40>
   8:   8d 4f 01                lea    0x1(%rdi),%ecx
   b:   31 d2                   xor    %edx,%edx
   d:   83 e7 01                and    $0x1,%edi
  10:   b8 01 00 00 00          mov    $0x1,%eax
  15:   74 11                   je     28 <sum_to+0x28>
  17:   b8 02 00 00 00          mov    $0x2,%eax
  1c:   ba 01 00 00 00          mov    $0x1,%edx
  21:   39 c8                   cmp    %ecx,%eax
  23:   74 0e                   je     33 <sum_to+0x33>
  25:   0f 1f 00                nopl   (%rax)          # padding to align the loop head
  28:   8d 54 42 01             lea    0x1(%rdx,%rax,2),%edx
  2c:   83 c0 02                add    $0x2,%eax
  2f:   39 c8                   cmp    %ecx,%eax
  31:   75 f5                   jne    28 <sum_to+0x28>
  33:   89 d0                   mov    %edx,%eax
  35:   c3                      ret
```

Note the variable instruction lengths — 2, 3, 4, 5 and 7 bytes all appear — and the multi-byte `nop` at `0x25` inserted purely to align the loop entry at `0x28` to a 16-byte-friendly boundary for the fetch unit.

### AArch64, clang 18.1.3, `-O0` (`clang -S -O0 --target=aarch64-linux-gnu sum.c`)

```asm
sum_to:
        sub     sp, sp, #16          # allocate 16-byte frame (SP stays 16-aligned)
        str     w0, [sp, #12]        # spill arg n (X0/W0 = AAPCS64 arg 1)
        str     wzr, [sp, #8]        # total = 0   (WZR is the zero register)
        mov     w8, #1
        str     w8, [sp, #4]         # i = 1
        b       .LBB0_1
.LBB0_1:
        ldr     w8, [sp, #4]         # i
        ldr     w9, [sp, #12]        # n
        subs    w8, w8, w9           # flags = i - n   (S suffix = set NZCV)
        b.gt    .LBB0_4              # if i > n, exit
        b       .LBB0_2
.LBB0_2:
        ldr     w9, [sp, #4]
        ldr     w8, [sp, #8]
        add     w8, w8, w9           # total += i
        str     w8, [sp, #8]
        b       .LBB0_3
.LBB0_3:
        ldr     w8, [sp, #4]
        add     w8, w8, #1           # i++
        str     w8, [sp, #4]
        b       .LBB0_1
.LBB0_4:
        ldr     w0, [sp, #8]         # return value in W0
        add     sp, sp, #16
        ret
```

Load–store architecture in its purest form: arithmetic never touches memory, so every `total += i` is an explicit `ldr`/`add`/`str` triple. `W` registers are the low 32 bits of the 64-bit `X` registers; writing a `W` register zeroes the upper half.

### AArch64, clang 18.1.3, `-O1`

```asm
sum_to:
        subs    w8, w0, #1           # w8 = n - 1, set flags
        b.lt    .LBB0_2              # n < 1 → return 0
        sub     w9, w0, #2
        umull   x8, w8, w9           # 64-bit product of (n-1)(n-2)
        lsr     x8, x8, #1           # /2
        add     w8, w8, w0, lsl #1   # + 2n   (shifted register operand — free)
        sub     w0, w8, #1           # - 1
        ret
.LBB0_2:
        mov     w0, wzr
        ret
```

The loop is **gone**. LLVM recognised the induction variable and replaced the whole thing with the closed form n(n+1)/2, algebraically rearranged as ((n−1)(n−2)/2) + 2n − 1 to keep the intermediate in a 64-bit product and avoid overflow in the halving. Note `add w8, w8, w0, lsl #1` — AArch64's shifted-register operand does the multiply-by-two inside the add, for free.

### RISC-V RV64, clang 18.1.3, `-O0` (`clang -S -O0 --target=riscv64-linux-gnu sum.c`)

```asm
sum_to:
        addi    sp, sp, -32
        sd      ra, 24(sp)           # save return address (RISC-V has no push)
        sd      s0, 16(sp)           # save callee-saved frame pointer
        addi    s0, sp, 32
        sw      a0, -20(s0)          # spill arg n (a0 = x10)
        li      a0, 0
        sw      a0, -24(s0)          # total = 0
        li      a0, 1
        sw      a0, -28(s0)          # i = 1
        j       .LBB0_1
.LBB0_1:
        lw      a1, -28(s0)          # i
        lw      a0, -20(s0)          # n
        blt     a0, a1, .LBB0_4      # branch if n < i  — compare AND branch, no flags
        j       .LBB0_2
.LBB0_2:
        lw      a1, -28(s0)
        lw      a0, -24(s0)
        addw    a0, a0, a1           # total += i  (addw = 32-bit add, sign-extended)
        sw      a0, -24(s0)
        j       .LBB0_3
.LBB0_3:
        lw      a0, -28(s0)
        addiw   a0, a0, 1            # i++
        sw      a0, -28(s0)
        j       .LBB0_1
```

Two things to notice. First, **no condition codes**: `blt a0, a1, label` compares and branches in one instruction, which is why RISC-V needs no flags register and why its out-of-order implementations avoid a serialising rename dependency that x86 must handle. Second, the `w` suffix — `addw`, `addiw` — is RV64's 32-bit arithmetic that sign-extends into the 64-bit register, needed because C's `int` is 32-bit on a 64-bit machine.

### RISC-V RV64, `-O1`

```asm
sum_to:
        blez    a0, .LBB0_2
        slli    a1, a0, 1            # 2n
        addi    a2, a0, -1
        addi    a0, a0, -2
        slli    a0, a0, 32           # widen to 64-bit for the multiply
        slli    a2, a2, 32
        mulhu   a0, a2, a0           # high half of the unsigned 64×64 product
        srli    a0, a0, 1
        add     a0, a0, a1
        addiw   a0, a0, -1
        ret
.LBB0_2:
        li      a0, 0
        ret
```

Same closed-form transformation as AArch64, but expressed with `mulhu` and shift games because RISC-V lacks a widening-multiply-with-shift addressing trick.

### The simplest possible comparison

```c
int add3(int a, int b, int c) { return a + b + c; }
```

| ISA | Output |
|---|---|
| x86-64 `-O2` | `addl %esi, %edi` / `leal (%rdi,%rdx), %eax` / `ret` |
| AArch64 `-O2` | `add w8, w1, w0` / `add w0, w8, w2` / `ret` |
| RISC-V `-O2` | `add a0, a0, a1` / `addw a0, a0, a2` / `ret` |

x86 uses `lea` as a three-operand add because its two-operand `add` would clobber a source. AArch64 and RISC-V, having three-operand instructions, do not need the trick. This one function shows the CISC/RISC difference more clearly than any prose.

## 6. The pipeline, hazards and speculation

A classic five-stage RISC pipeline: **IF** (instruction fetch) → **ID** (decode / register read) → **EX** (execute) → **MEM** (memory access) → **WB** (write back). Ideal throughput is one instruction per cycle; the point of pipelining is to raise clock frequency by shortening the critical path in each stage.

**Hazards** are the reasons it does not work perfectly:
- **Structural** — two instructions need the same unit. Fixed by duplicating units or by stalling.
- **Data (RAW)** — an instruction needs a result not yet written back. Fixed by **forwarding/bypassing** the value from EX or MEM straight back to EX; the one case forwarding cannot fix is a load-use hazard, which costs a bubble.
- **Control** — a branch's target is unknown until it executes. Fixed by prediction.

**Branch prediction** is the difference between a modern core and a toy. TAGE-style predictors combine multiple history lengths and reach >99% accuracy on typical code; an indirect-branch target buffer predicts virtual calls and jump tables; a return-address stack predicts returns. A mispredict on a deep out-of-order core costs 15–20+ cycles of squashed work. The practical consequence for a programmer: *unpredictable* branches are expensive, predictable ones are nearly free, and branchless code (`cmov`, `csel`, arithmetic masks) wins only when the branch is genuinely unpredictable.

**Out-of-order and superscalar execution.** A modern core fetches and decodes several instructions per cycle (superscalar), renames their architectural registers onto a much larger physical register file to eliminate false WAR/WAW dependencies, issues them to execution ports as their operands become ready (out-of-order), and retires them in program order from a reorder buffer so that exceptions and interrupts remain precise. Speculation carries all of this past unresolved branches. Spectre and Meltdown (2018) were the discovery that the *microarchitectural* side effects of squashed speculative work are observable through the cache, breaking the assumption that speculation is invisible to software.

**SIMD.** One instruction, many data lanes.
- x86: MMX (64-bit) → SSE/SSE2 (128) → AVX (256) → AVX2 → AVX-512 (512, with masking and many sub-extensions) → AVX10.
- Arm: NEON/ASIMD (fixed 128-bit) → **SVE/SVE2** (*vector-length agnostic*: the same binary runs on 128- to 2048-bit implementations, with predicate registers and a `whilelt`-driven loop idiom that removes the scalar tail).
- RISC-V: the **V extension**, also vector-length agnostic, with a `vsetvl` instruction that hands the loop back the number of elements it may process this iteration.

Vector-length agnosticism is the important design idea: Arm and RISC-V learned from x86's need to recompile for every new width.

## 7. Memory hierarchy and caches

| Level | Typical size | Typical latency |
|---|---|---|
| Register | ~1 KB | <1 cycle |
| L1d / L1i | 32–64 KB each | ~4 cycles |
| L2 | 0.5–2 MB per core | ~12–20 cycles |
| L3 (shared) | 8–128 MB | ~40–80 cycles |
| DRAM | GB | ~200–350 cycles |
| NVMe SSD | TB | ~10–100 µs |

(Order-of-magnitude figures; exact numbers vary by microarchitecture and are not sourced here.)

Caches are organised in **lines**, almost universally 64 bytes. Sets and ways determine placement; associativity trades hit rate against lookup energy. What matters to a programmer:

- **Spatial locality:** touching one byte pulls in 64. Array-of-structs versus struct-of-arrays is decided by which fields are accessed together.
- **Temporal locality:** blocked/tiled matrix multiply beats naive triple loops by an order of magnitude at large N, purely by reuse.
- **False sharing:** two threads writing different variables in the same 64-byte line ping-pong the line between cores. Pad to a cache line (`alignas(64)`).
- **Prefetchers** detect sequential and constant-stride patterns. Pointer chasing defeats them; that is the real reason linked lists lose to arrays.
- **Cache coherence** (MESI and its variants) keeps per-core caches consistent. It is the hardware that makes shared-memory concurrency possible and the reason atomics cost what they cost.

## 8. Virtual memory and the MMU

Each process gets its own virtual address space. The **MMU** translates virtual to physical addresses using **page tables** — on x86-64 a four-level radix tree (PML4 → PDPT → PD → PT, 9 bits per level, 12-bit offset, 4 KB pages), extendable to five levels for 57-bit addresses. The **TLB** caches recent translations; a TLB miss triggers a page-table walk, and huge pages (2 MB, 1 GB) exist mostly to reduce TLB pressure.

Page-table entries carry permission bits (present, writable, user/supervisor, no-execute) and accounting bits (accessed, dirty). This machinery gives you process isolation, demand paging, copy-on-write `fork`, memory-mapped files, shared libraries mapped once into many processes, and guard pages. `mmap` is the syscall that exposes it.

## 9. Interrupts, exceptions and the boot process

**Exceptions** are synchronous (a page fault, a divide by zero, a system call via `syscall`/`svc`/`ecall`). **Interrupts** are asynchronous (a timer, a NIC, a keyboard). Both vector through a table — the IDT on x86, VBAR_EL1 on AArch64, `mtvec`/`stvec` on RISC-V — into a handler that saves state, services the event and returns. Precise exceptions (the guarantee that the architectural state looks exactly as if instructions before the faulting one completed and none after started) are what makes out-of-order execution invisible to the OS.

**Boot, on a modern x86-64 PC:**
1. Power-on; the CPU starts in a reset state and fetches from the reset vector.
2. **UEFI firmware** initialises DRAM (memory training), enumerates PCIe, sets up the ACPI tables.
3. Firmware reads the **GPT** partition table, finds the EFI System Partition, and loads a `.efi` boot application (shim → GRUB, or systemd-boot, or the kernel directly via EFI stub).
4. The bootloader loads the kernel image and initramfs, builds a boot parameter structure and jumps to the kernel entry point.
5. The kernel sets up page tables, enables paging fully, initialises the scheduler and drivers, mounts the root filesystem, and execs PID 1.

On an embedded SoC the sequence is a boot ROM → first-stage loader in SRAM → DDR init → U-Boot (or equivalent) → kernel or bare-metal image. Secure boot chains signature verification through every stage from an immutable root of trust in ROM.

## 10. ELF, linking and loading

ELF (Executable and Linkable Format) is the object format on Linux, BSD, and most embedded targets. From `readelf -h` on the object file compiled above:

```
Magic:   7f 45 4c 46 02 01 01 00 ...
Class:                             ELF64
Data:                              2's complement, little endian
Type:                              REL (Relocatable file)
Machine:                           Advanced Micro Devices X86-64
Number of section headers:         12
```

and `readelf -S`:

```
[ 1] .text             PROGBITS   size 0x45   flags AX   align 16
[ 2] .data             PROGBITS   size 0      flags WA
[ 3] .bss              NOBITS     size 0      flags WA
[ 4] .comment          PROGBITS
[ 6] .note.gnu.property NOTE
[ 7] .eh_frame         PROGBITS
```

The essential sections: `.text` (code, read+execute), `.rodata` (constants), `.data` (initialised writable data), `.bss` (zero-initialised, occupies no file space — note `NOBITS` and size 0 above), `.symtab`/`.strtab` (symbols), `.rela.text` (relocations), `.eh_frame` (unwind info), `.debug_*` (DWARF).

**Static linking** resolves symbols and applies relocations at build time, producing a self-contained binary. **Dynamic linking** leaves undefined symbols for the loader (`ld.so`), which maps shared objects and resolves symbols through the **GOT** (global offset table, for data) and **PLT** (procedure linkage table, for lazily bound functions). Position-independent code makes all this possible by addressing everything RIP-relative.

The three classic linking failures every engineer meets: *undefined reference* (a declaration with no definition — usually a missing library or a C++ name-mangling mismatch), *multiple definition* (a definition in a header without `inline`/`static`), and *symbol found at link time but not at run time* (an `LD_LIBRARY_PATH`, `rpath` or ABI-version problem).

## 11. How a compiler lowers C to assembly

1. **Preprocess** — macro expansion and `#include` textual substitution. `gcc -E`.
2. **Parse** to an AST; run semantic analysis and type checking.
3. **Lower to IR.** GCC uses GIMPLE then RTL; Clang emits **LLVM IR**, an SSA-form, typed, target-independent language. See it with `clang -S -emit-llvm`.
4. **Optimise the IR** — constant folding and propagation, dead code elimination, common subexpression elimination, inlining, loop-invariant code motion, strength reduction, induction-variable recognition (which is exactly what produced the closed-form results above), vectorisation, and tail-call elimination.
5. **Instruction selection** — pattern-match IR onto target instructions (this is where `lea` gets chosen for an add).
6. **Register allocation** — graph colouring or linear scan; spill what does not fit.
7. **Instruction scheduling** — reorder to hide latency, respecting dependencies and the target's port model.
8. **Emit assembly**, then assemble to an object file, then link.

**The toolchain commands worth memorising:**

```bash
gcc -E  file.c -o file.i          # preprocessed source
gcc -S  -O2 file.c -o file.s      # assembly (add -masm=intel if you prefer)
gcc -c  -O2 file.c -o file.o      # object file
objdump -d file.o                 # disassemble, with machine-code bytes
objdump -dS file.o                # interleaved with source (needs -g)
readelf -h / -S / -s / -r file.o  # ELF header / sections / symbols / relocations
nm -C file.o                      # symbols, demangled
size file.o                       # .text/.data/.bss sizes
clang -S -emit-llvm file.c        # LLVM IR
gcc -fverbose-asm -S file.c       # assembly annotated with variable names
gcc -fopt-info-vec file.c         # report which loops were vectorised
strings / ldd / strace / ltrace   # inspecting a built binary
```

**Compiler Explorer** (godbolt.org) is the single best tool in this file. It shows source and assembly side by side, colour-linked, for dozens of compilers, versions and target architectures at once — including all three ISAs above. Use it constantly; it turns "what does the compiler do with this?" from a research question into a two-second experiment.

## Sources

- [x86 calling conventions — System V AMD64 and Microsoft x64](https://en.wikipedia.org/wiki/X86_calling_conventions) — Wikipedia
- [RISC-V ratified specifications](https://riscv.org/specifications/ratified/) — RISC-V International
- [C23 (ISO/IEC 9899:2024)](https://en.wikipedia.org/wiki/C23_(C_standard_revision)) — Wikipedia
- All assembly listings, disassembly and ELF dumps in this file were generated on 2026-08-25 with **gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0** and **Ubuntu clang version 18.1.3**, using the commands shown.
- [Compiler Explorer](https://godbolt.org/) — for reproducing any of the above across other compilers and targets.

## Open questions

- Cache latency and size figures in §7 are order-of-magnitude conventions, **not** taken from a vendor optimisation manual. For real numbers use the Intel 64 and IA-32 Optimization Reference Manual, AMD's Software Optimization Guide, or Agner Fog's instruction tables, and measure on the target part.
- AAPCS64 register roles are stated from general knowledge; the Arm *Procedure Call Standard for the Arm 64-bit Architecture* document itself was not fetched.
- RISC-V profile contents (RVA20/22/23) are described qualitatively; the profile specification was not fetched and the exact mandatory extension lists are `needs-verification`.
- The `fence.i` / AArch64 cache-maintenance sequences are given from general knowledge and should be checked against the current architecture reference manual before use in production code.

