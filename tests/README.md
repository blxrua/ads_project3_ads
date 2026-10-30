# Test inputs for the report

These are the 12 hand-written inputs used in Table 3.1 of
`report_safe_fruit.pdf`.

Build the final program and run one case:

```powershell
gcc -O2 -std=c99 -o safe_fruit v8_cycle_tree_dp.c
.\safe_fruit < tests\01_sample.in
```

Expected outputs are listed in Table 3.1 of the report.  The sample output is:

```text
12
002 004 006 008 009 014 015 016 017 018 019 020
239
```

`report_safe_fruit.tex` is the report source; compile it twice with
`pdflatex` to resolve the table of contents and cross-references.
