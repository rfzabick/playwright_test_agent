// tests/fixtures/sample_js/lodash_usage.js
import { groupBy, map } from 'lodash';

const users = [
  { name: 'Alice', age: 30 },
  { name: 'Bob', age: 30 },
];

const byAge = groupBy(users, 'age');
const names = map(users, u => u.name);
const doubled = map([1, 2, 3], x => x * 2);
