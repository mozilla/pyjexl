# PyJEXL

A Python-based JEXL parser and evaluator.

__NOTE:__ This library handles the JEXL from
[TechnologyAdvice's JEXL library][jexl]. It does __NOT__ handle the
similarly-named Apache Commons JEXL language.

[jexl]: https://github.com/TechnologyAdvice/Jexl

## Limitations and Differences from JEXL

- JavaScript-style implicit type conversions aren't supported, but may be added
  in the future. Instead, Python type semantics are used.
- Property access is only supported for mapping objects currently.
- Several odd edge-cases in JEXL are ignored because they are unintuitive,
  difficult to implement, or a bad pattern:
  - Implicitly using the first element in an array when chaining identifiers
    is not supported. In JEXL, if `foo.bar` is a list, the expression
    `foo.bar.baz` is equivalent to `foo.bar[0].baz`.
  - Conditional expressions (AKA ternary expressions) cannot have a missing
    consequent, i.e. `"foo" ?: 4` is invalid.

## License

Licensed under the MIT License. See `LICENSE` for details.
