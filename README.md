# Morlock
> Very simple was my explanation, and plausible enough -- as most wrong theories are!
*-- H. G. Wells, The Time Machine*

<hl>

Implementation of a symbolic synthesizer for the SyGuS format, based on ["Synthesis of Loop-Free Programs"](http://dl.acm.org/citation.cfm?id=1993506) by Gulwani *et. al*. 

## Dependencies
Morlock requires an up-to-date installation of [Z3](https://github.com/Z3Prover/z3), made for Python 3.

## Usage
Morlock is written in Python 3. For usage assistance, navigate to the directory containing Morlock and run:
`python3 ./morlock -h`
Morlock takes input in the [SyGuS](http://www.sygus.org/) file format, with some caveats:
1. No current support for `let`-bindings. This will be added in the future.
2. Only one synthesis function per file. Any more and Morlock will throw an exception.
3. Grammars with a single non-terminal only. If a grammar with more than one non-terminal is provided, Morlock will assume they're all the same.
4. Only support for the LIA and BV theories. This is easily changed by modifying `morlock/symbols.py`.

## Equations
To be explored later.