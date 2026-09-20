/**
 * Loads data/trial_summary.json (produced by parse_trials.py) into the `trials` table.
 * Safe to run many times: trials are upserted on their NCT id.
 *
 *   npx prisma db seed
 *   TRIALS_JSON=../data/trial_summary.json npx prisma db seed     # custom location
 *
 * package.json needs:  "prisma": { "seed": "ts-node prisma/seed.ts" }
 */
import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';

const prisma = new PrismaClient();

type CriterionJson = { id: string; text: string };

// shape written by parse_trials.py (snake_case)
type TrialSummary = {
    nct_id: string | null;
    title: string | null;
    status: string | null;
    conditions?: string[];
    min_age?: number | null;
    max_age?: number | null;
    sex?: string | null;
    inclusion_criteria?: CriterionJson[];
    exclusion_criteria?: CriterionJson[];
    phases?: string[];
    brief_summary?: string | null;
    study_url?: string | null;
    locations?: Record<string, unknown>[];
};

async function main() {
    const file = path.resolve(process.env.TRIALS_JSON ?? 'data/trial_summary.json');
    if (!fs.existsSync(file)) {
        throw new Error(
            `Trials file not found: ${file}\n` +
                `Run download_trials.py then parse_trials.py first, or set TRIALS_JSON.`,
        );
    }

    const trials: TrialSummary[] = JSON.parse(fs.readFileSync(file, 'utf-8'));
    let saved = 0;
    let skipped = 0;

    for (const t of trials) {
        if (!t.nct_id || !t.title) {
            skipped++;
            continue;
        }

        const data = {
            title: t.title,
            status: t.status ?? 'UNKNOWN',
            conditions: t.conditions ?? [],
            minAge: t.min_age ?? null,
            maxAge: t.max_age ?? null,
            sex: t.sex ?? 'ALL',
            inclusionCriteria: t.inclusion_criteria ?? [],
            exclusionCriteria: t.exclusion_criteria ?? [],
            phases: t.phases ?? [],
            briefSummary: t.brief_summary ?? null,
            studyUrl: t.study_url ?? null,
            locations: (t.locations ?? []) as object[],
        };

        await prisma.trial.upsert({
            where: { nctId: t.nct_id },
            create: { nctId: t.nct_id, ...data },
            update: data,
        });
        saved++;
    }

    const criteriaCounts = trials
        .filter((t) => t.nct_id)
        .map((t) => (t.inclusion_criteria?.length ?? 0) + (t.exclusion_criteria?.length ?? 0))
        .sort((a, b) => a - b);

    console.log(`Seeded ${saved} trials (${skipped} skipped: missing id or title).`);
    console.log(
        `Criteria per trial: min ${criteriaCounts[0] ?? 0}, median ${
            criteriaCounts[Math.floor(criteriaCounts.length / 2)] ?? 0
        }, max ${criteriaCounts[criteriaCounts.length - 1] ?? 0}`,
    );
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(() => prisma.$disconnect());
