import { describe, expect, it } from 'vitest';
import { Badge, Button, Card, Input } from './index';

describe('@scoutai/ui exports', () => {
  it('exports component functions', () => {
    expect(typeof Button).toBe('function');
    expect(typeof Input).toBe('function');
    expect(typeof Card).toBe('function');
    expect(typeof Badge).toBe('function');
  });
});
