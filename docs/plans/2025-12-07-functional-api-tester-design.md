# Functional API Tester Design

## Purpose

Generate regression tests for a JavaScript library's functional APIs before an upgrade. Given a library name and source directory, produce tests that verify `fn(inputs) === outputs` relationships hold after the library version changes.

## Context

This is Tool A of a two-tool approach:
- **Tool A (this doc)**: Functional API tester - for pure functions where we test input/output relationships
- **Tool B (future)**: Side-effect API tester - for libraries that modify DOM, trigger events, etc.

Many libraries will need both tools. A charting library might have pure data transformation functions (Tool A) and DOM rendering functions (Tool B).

## Design

### Phase 1: Library API Discovery

Three sources, all static analysis:

1. **Type definitions** - Fetch from `@types/libraryname` or bundled `.d.ts` in the library's npm package. Provides function signatures, parameter types, return types.
2. **Documentation** - Scrape library's API docs for semantic context and examples.
3. **Codebase usage** - Parse user's source to scope down to functions they actually use.

Output: A focused list of library functions relevant to this codebase.

Note: Eval-based dynamic usage is out of scope.

### Phase 2: Usage Detection

Static analysis of the user's source code:

1. **Find imports** - `import { groupBy } from 'lodash'` or `const _ = require('lodash')`
2. **Find call sites** - Where are those imports invoked?
3. **Extract static arguments** - When arguments are literals, capture them directly.

Output: List of call sites with location, function name, and any statically-extractable arguments.

### Phase 3: Runtime Input Capture

For call sites where arguments are dynamic:

1. Developer injects instrumentation into their local environment.
2. Developer uses the app - clicks around, triggers representative flows.
3. Instrumentation captures function calls and outputs executable test code directly.
4. Developer copies generated test assertions into their test file.

Output: JavaScript test code like:
```javascript
expect(_.groupBy(
  [{"name": "alice", "age": 30}, {"name": "bob", "age": 30}],
  "age"
)).toEqual({
  "30": [{"name": "alice", "age": 30}, {"name": "bob", "age": 30}]
});
```

### Phase 4: Test Generation

Generate two types of tests:

**Complete tests** - When we captured all inputs and outputs:
```javascript
test('_.groupBy groups users by age', () => {
  expect(_.groupBy(
    [{"name": "alice", "age": 30}, {"name": "bob", "age": 30}],
    "age"
  )).toEqual({
    "30": [{"name": "alice", "age": 30}, {"name": "bob", "age": 30}]
  });
});
```

**Incomplete tests** - When we couldn't capture everything, generate a failing test with details in the failure message:
```javascript
test('_.map with processUser - requires manual input', () => {
  throw new Error(`
Unable to generate complete test for _.map

Location: src/utils/transform.js:87
Issue: Could not capture 'processUser' function body
Original usage: _.map(users, processUser)

To fix: Replace this test with concrete inputs and expected output
  `);
});
```

Passing tests validate behavior; failing tests document gaps the developer must address manually.

## Developer Workflow

1. **Run discovery**: `tool analyze --library lodash --source ./src`
   - Fetches library types/docs
   - Scans source for usages
   - Generates tests from statically-extractable arguments
   - Outputs: test file + instrumentation script for dynamic call sites

2. **Inject instrumentation**: Developer adds instrumentation script to their local dev environment.

3. **Capture and generate**: Developer uses the app normally.
   - Instrumentation outputs test code directly (not traces)
   - Developer copies generated test assertions into their test file

4. **Upgrade library**: Developer upgrades the library, runs tests, fixes any regressions.

## Scope

### v1 In Scope

- JavaScript libraries with `@types` definitions available
- ES modules and CommonJS imports
- Serializable inputs (primitives, objects, arrays)
- Simple lambdas (`x => x * 2`)
- Jest output format (most popular)
- One test file per library
- Deduplication to representative samples (not every call)

### v1 Out of Scope

- Eval-based dynamic usage
- Complex function references (captured as failing tests with details)
- DOM elements, circular references
- Side-effect APIs (Tool B)
- User-configurable test framework (v2)
- Advanced test organization (v2)

## Future Considerations

### v2 Features
- User-selectable test framework (Vitest, Mocha, Playwright test, etc.)
- Smarter test organization (by source file, by function, etc.)
- Better "representative sample" selection algorithms

### Tool B (Side-effect API Tester)
- Runtime observation of DOM/visual changes
- Links behavior back to library components
- Integration-style tests: "clicking this library component causes these changes"
