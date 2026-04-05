from __future__ import annotations

import argparse
import contextlib
import gc
import io
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))

from hairpin.interpreter import Interpreter


@dataclass(frozen=True)
class Benchmark:
    name: str
    filename: str
    description: str
    expected_stdout: str
    warmups: int = 1
    timed_runs: int = 5


BENCHMARKS = [
    Benchmark(
        name="countdown",
        filename="countdown.hp",
        description="tail-recursive integer/control-flow loop",
        expected_stdout="0",
    ),
    Benchmark(
        name="fib-mod",
        filename="fib_mod.hp",
        description="large integer arithmetic with TCO loop",
        expected_stdout="544942611",
    ),
    Benchmark(
        name="primes-sieve",
        filename="primes_50000.hp",
        description="cons-list sieve and modulo-heavy filtering",
        expected_stdout="5133",
    ),
    Benchmark(
        name="string-roundtrip",
        filename="string_roundtrip.hp",
        description="repeated chars/string round-trips on a large string",
        expected_stdout="true",
    ),
    Benchmark(
        name="list-reverse",
        filename="list_reverse.hp",
        description="tail-recursive list construction and repeated reversal",
        expected_stdout="30000",
    ),
]


def _run_source(source: str) -> str:
    interp = Interpreter()
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        interp.run(source)
    return output.getvalue()


def _benchmark_source(source: str, bench: Benchmark) -> list[float]:
    for _ in range(bench.warmups):
        warmup_output = _run_source(source)
        if warmup_output != bench.expected_stdout:
            raise RuntimeError(
                f"{bench.name}: expected {bench.expected_stdout!r} during warmup, got {warmup_output!r}"
            )

    runs: list[float] = []
    for _ in range(bench.timed_runs):
        gc.collect()
        start = time.perf_counter()
        output = _run_source(source)
        elapsed = time.perf_counter() - start
        if output != bench.expected_stdout:
            raise RuntimeError(f"{bench.name}: expected {bench.expected_stdout!r}, got {output!r}")
        runs.append(elapsed)
    return runs


def _format_seconds(seconds: float) -> str:
    return f"{seconds:.3f}s"


def _print_text_table(results: list[tuple[Benchmark, list[float]]]) -> None:
    print("Hairpin benchmark results")
    print("========================")
    print("timed runs: 5  warmups: 1")
    print()
    for bench, runs in results:
        median = statistics.median(runs)
        print(f"{bench.name:16} {_format_seconds(median):>8}  {bench.description}")
        print(" " * 16 + " runs: " + ", ".join(_format_seconds(run) for run in runs))
        print(" " * 16 + f" output: {bench.expected_stdout}")
        print()


def _print_markdown_table(results: list[tuple[Benchmark, list[float]]]) -> None:
    print("| Benchmark | Description | Median of 5 runs | Individual runs |")
    print("|-----------|-------------|------------------|-----------------|")
    for bench, runs in results:
        median = statistics.median(runs)
        formatted_runs = ", ".join(_format_seconds(run) for run in runs)
        print(
            f"| `{bench.name}` | {bench.description} | {_format_seconds(median)} | {formatted_runs} |"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Hairpin benchmark suite.")
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print the results as a Markdown table.",
    )
    args = parser.parse_args()

    results: list[tuple[Benchmark, list[float]]] = []
    for bench in BENCHMARKS:
        source = (ROOT / bench.filename).read_text()
        runs = _benchmark_source(source, bench)
        results.append((bench, runs))

    if args.markdown:
        _print_markdown_table(results)
    else:
        _print_text_table(results)


if __name__ == "__main__":
    main()
