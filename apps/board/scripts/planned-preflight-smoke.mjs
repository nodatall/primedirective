#!/usr/bin/env node
import { preflightPlannedSkill } from '../api/dist/repos/preflight.js';

const result = preflightPlannedSkill('/Volumes/Code/primedirective');
console.log(JSON.stringify({ planned_preflight_smoke: result.ok ? 'passed' : 'failed', errors: result.errors }, null, 2));
process.exit(result.ok ? 0 : 1);
