export type CriterionSection = 'inclusion' | 'exclusion';

export type CriterionInput = {
    id: string;
    section: CriterionSection;
    text: string;
};

/** One persisted message. `criterionId` is set on assistant messages that asked about one criterion. */
export type ConversationTurn = {
    role: 'assistant' | 'caregiver';
    content: string;
    criterionId?: string | null;
};

export type AssessEligibilityInput = {
    /** Registration data (age, sex, condition summary) — never names or contact details. */
    patientContext: string;
    turns: ConversationTurn[];
    criteria: CriterionInput[];
};

export type CriterionVerdict = {
    criterion_id?: string;
    section?: CriterionSection;
    criterion: string;
    verdict: 'eligible' | 'not_eligible' | 'insufficient_information';
    reasoning?: string;
};

export type AssessEligibilityResult = {
    status: 'need_more_info' | 'final';
    /**
     * 'likely_eligible' = nothing rules the patient out, but the remaining criteria are ones
     * the caregiver cannot answer — the study team has to confirm them.
     */
    verdict: 'eligible' | 'not_eligible' | 'likely_eligible' | 'unknown';
    overall_verdict: 'eligible' | 'not_eligible' | 'unknown';
    details: CriterionVerdict[];
    unclear_criteria: CriterionVerdict[];
    pending_criteria: CriterionVerdict[];
    next_question: string | null;
    next_criterion_id: string | null;
    followup_questions: string[];
    criteria_remaining: number;
};

export abstract class IEligibilityAiService {
    abstract assess(input: AssessEligibilityInput): Promise<AssessEligibilityResult>;
}
