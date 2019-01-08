# PyJEXL

[![CircleCI](https://circleci.com/gh/mozilla/pyjexl.svg?style=svg)](https://circleci.com/gh/mozilla/pyjexl)

A Python-based JEXL parser and evaluator.

**NOTE:** This library handles the JEXL from
[TomFrost's JEXL library][jexl]. It does **NOT** handle the
similarly-named Apache Commons JEXL language.

[jexl]: https://github.com/TomFrost/Jexl

## Limitations and Differences from JEXL

* JavaScript-style implicit type conversions aren't supported, but may be added
  in the future. Instead, Python type semantics are used.
* Property access is only supported for mapping objects currently.
* Several odd edge-cases in JEXL are ignored because they are unintuitive,
  difficult to implement, or a bad pattern:
  * Implicitly using the first element in an array when chaining identifiers
    is not supported. In JEXL, if `foo.bar` is a list, the expression
    `foo.bar.baz` is equivalent to `foo.bar[0].baz`.
  * Conditional expressions (AKA ternary expressions) cannot have a missing
    consequent, i.e. `"foo" ?: 4` is invalid.

## License

Licensed under the MIT License. See `LICENSE` for details.
