const protectedPath = [/auth/i, /billing/i, /migration/i, /schema/i, /secret/i, /deploy/i, /api\/.*contract/i, /(^|\/)\.env(\.|$)?/i, /credential/i, /token/i, /private[-_]?key/i];
const protectedText = [/delete\s+all/i, /drop\s+table/i, /rotate\s+secret/i, /public\s+api/i, /broad\s+refactor/i, /unclear/i, /api[_-]?key\s*=/i, /secret\s*=/i, /token\s*=/i, /-----BEGIN [A-Z ]*PRIVATE KEY-----/i];

export interface ProtectedRiskResult { risky: boolean; reasons: string[] }

export function classifyProtectedRisk(paths: string[], diffText: string, taskText: string): ProtectedRiskResult {
  const reasons: string[] = [];
  if (paths.some((path) => protectedPath.some((pattern) => pattern.test(path)))) reasons.push('protected_path');
  if (protectedText.some((pattern) => pattern.test(diffText))) reasons.push('protected_diff');
  if (protectedText.some((pattern) => pattern.test(taskText))) reasons.push('protected_task_intent');
  return { risky: reasons.length > 0, reasons };
}
