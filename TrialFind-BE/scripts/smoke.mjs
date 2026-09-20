/**
 * End-to-end smoke test: Nest -> Postgres -> Python AI service.
 * Needs Node 18+, nothing to install.
 *
 *   node scripts/smoke.mjs
 *   API_URL=http://localhost:5555 TRIAL_ID=<uuid> node scripts/smoke.mjs
 *
 * It picks the trial with the FEWEST criteria (fast demo) unless TRIAL_ID is given,
 * sends one rich message, then answers every follow-up with "I don't know" until the
 * session ends — which also proves the "no endless loop" fix works.
 */
const API = process.env.API_URL ?? 'http://localhost:5555';
const MAX_TURNS = 60;
const stamp = Date.now();

let accessToken = null;

async function call(method, route, body) {
    const res = await fetch(`${API}${route}`, {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
        console.error(`\n✗ ${method} ${route} -> ${res.status}`);
        console.error(JSON.stringify(json.message ?? json, null, 2));
        process.exit(1);
    }
    return json.data; // ResponseInterceptor wraps everything in { status, message, data }
}

const step = (label) => console.log(`\n▶ ${label}`);

// 1. account
const email = `smoke+${stamp}@example.com`;
const password = 'Sm0ke-Test!pass';
step('register + login');
await call('POST', '/auth/register', { email, password, firstName: 'Smoke', lastName: 'Test' });
const login = await call('POST', '/auth/login', { email, password });
accessToken = login.accessToken;
console.log('  logged in as', login.caregiver.email);

// 2. patient
step('create patient (72, female, mild Alzheimer\'s)');
const patient = await call('POST', '/patients', {
    firstName: 'Test',
    lastName: 'Patient',
    dateOfBirth: `${new Date().getFullYear() - 72}-03-12`,
    sex: 'FEMALE',
    relationshipToCaregiver: 'mother',
    conditionSummary: "Mild Alzheimer's disease",
});
console.log('  patient', patient.id);

// 3. discovery
step('search trials');
const trials = await call('POST', '/trials/search', {
    age: 72,
    sex: 'FEMALE',
    condition: 'alzheimer',
});
console.log(`  ${trials.length} matching trial(s)`);
if (!trials.length) {
    console.error('  no trials matched — did you run `npx prisma db seed`?');
    process.exit(1);
}
const size = (t) => t.inclusionCriteria.length + t.exclusionCriteria.length;
const trial = process.env.TRIAL_ID
    ? trials.find((t) => t.id === process.env.TRIAL_ID) ?? trials[0]
    : [...trials].sort((a, b) => size(a) - size(b))[0];
console.log(`  using ${trial.nctId} (${size(trial)} criteria): ${trial.title}`);

// 4. eligibility conversation
step('start eligibility session');
const started = await call('POST', '/eligibility/sessions', { patientId: patient.id, trialId: trial.id });
console.log('  assistant:', started.assistantMessage);

let reply = "She is 72 years old, diagnosed with mild Alzheimer's disease. Her MMSE score was 22.";
let last = null;
for (let turn = 1; turn <= MAX_TURNS; turn++) {
    console.log(`\n  caregiver: ${reply}`);
    const t0 = Date.now();
    last = await call('POST', `/eligibility/sessions/${started.sessionId}/messages`, { message: reply });
    console.log(`  assistant (${((Date.now() - t0) / 1000).toFixed(1)}s): ${last.assistantMessage}`);
    console.log(`  [status=${last.status} verdict=${last.verdict} remaining=${last.criteriaRemaining}]`);
    if (last.status === 'final') break;
    reply = "I don't know";
}

step('result');
if (last?.status !== 'final') {
    console.error(`✗ session did not finish within ${MAX_TURNS} turns`);
    process.exit(1);
}
console.log(`✓ finished with verdict: ${last.verdict}`);
if (last.pendingCriteria?.length) {
    console.log(`  ${last.pendingCriteria.length} criteria left for the study team to confirm`);
}
