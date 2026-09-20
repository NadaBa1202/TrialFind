export type TrialLocation = {
    facility?: string | null;
    city?: string | null;
    state?: string | null;
    country?: string | null;
    status?: string | null;
};

export type TrialCriterion = {
    id: string;
    text: string;
};

export class Trial {
    id: string;
    nctId: string;
    title: string;
    status: string;
    conditions: string[];
    minAge?: number | null;
    maxAge?: number | null;
    sex: 'ALL' | 'MALE' | 'FEMALE';
    inclusionCriteria: TrialCriterion[];
    exclusionCriteria: TrialCriterion[];
    phases: string[];
    briefSummary?: string | null;
    studyUrl?: string | null;
    locations: TrialLocation[];
    createdAt: Date;
    updatedAt: Date;
}