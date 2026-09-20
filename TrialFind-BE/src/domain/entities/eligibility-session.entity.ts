export type EligibilityVerdict =
    | 'ELIGIBLE'
    | 'LIKELY_ELIGIBLE' // nothing rules the patient out; remaining criteria need the study team
    | 'NOT_ELIGIBLE'
    | 'UNKNOWN'
    | 'IN_PROGRESS';

export class EligibilitySession {
    id: string;
    patientId: string;
    trialId: string;
    verdict: EligibilityVerdict;
    verdictDetail?: Record<string, any> | null;
    createdAt: Date;
    updatedAt: Date;
}
