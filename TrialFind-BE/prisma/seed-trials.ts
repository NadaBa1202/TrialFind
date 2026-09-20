import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';

const prisma = new PrismaClient();

async function main() {
    const filePath = process.argv[2] ?? 'trial_summary.json';
    const trials = JSON.parse(fs.readFileSync(filePath, 'utf-8'));

    for (const t of trials) {
        await prisma.trial.upsert({
            where: { nctId: t.nct_id },
            update: {},
            create: {
                nctId: t.nct_id,
                title: t.title,
                status: t.status,
                conditions: t.conditions ?? [],
                minAge: t.min_age,
                maxAge: t.max_age,
                sex: t.sex ?? 'ALL',
                inclusionCriteria: t.inclusion_criteria ?? [],
                exclusionCriteria: t.exclusion_criteria ?? [],
                phases: t.phases ?? [],
                briefSummary: t.brief_summary,
                studyUrl: t.study_url,
                locations: t.locations ?? [],
            },
        });
    }
    console.log(`Seeded ${trials.length} trials.`);
}

main()
    .catch((e) => { console.error(e); process.exit(1); })
    .finally(() => prisma.$disconnect());