import { Injectable, NotFoundException } from '@nestjs/common';
import { IEligibilitySessionRepository } from '../../../domain/abstracts/IEligibilitySessionRepository.service';
import { IPatientRepository } from '../../../domain/abstracts/IPatientRepository.service';
import { ITrialRepository } from '../../../domain/abstracts/ITrialRepository.service';
import {
    AssessEligibilityResult,
    ConversationTurn,
    CriterionInput,
    IEligibilityAiService,
} from '../../../domain/abstracts/IEligibilityAi.service';
import { Patient } from '../../../domain/entities/patient.entity';
import { Trial } from '../../../domain/entities/trial.entity';

@Injectable()
export class SendEligibilityMessageUseCase {
    constructor(
        private readonly sessionRepository: IEligibilitySessionRepository,
        private readonly trialRepository: ITrialRepository,
        private readonly patientRepository: IPatientRepository,
        private readonly aiService: IEligibilityAiService,
    ) {}

    async execute(sessionId: string, caregiverMessage: string) {
        const session = await this.sessionRepository.findById(sessionId);
        if (!session) throw new NotFoundException('Eligibility session not found');

        const trial = await this.trialRepository.findById(session.trialId);
        if (!trial) throw new NotFoundException('Trial not found');

        const patient = await this.patientRepository.get(session.patientId);
        if (!patient) throw new NotFoundException('Patient not found');

        await this.sessionRepository.addMessage(sessionId, 'CAREGIVER', caregiverMessage);
        const history = await this.sessionRepository.getMessages(sessionId);

        // The whole conversation is sent every time (with the criterion each assistant question
        // was about), so the AI side can re-derive everything from what is persisted.
        const turns: ConversationTurn[] = history.map((m) => ({
            role: m.role === 'CAREGIVER' ? 'caregiver' : 'assistant',
            content: m.content,
            criterionId: m.criterionId ?? null,
        }));

        const result = await this.aiService.assess({
            patientContext: this.buildPatientContext(patient),
            turns,
            criteria: this.buildCriteria(trial),
        });

        const isFinal = result.status === 'final';
        const assistantContent = isFinal
            ? this.buildFinalSummary(result)
            : (result.next_question ?? 'Could you share a bit more detail?');

        await this.sessionRepository.addMessage(
            sessionId,
            'ASSISTANT',
            assistantContent,
            isFinal ? null : result.next_criterion_id,
        );

        if (isFinal) {
            await this.sessionRepository.updateVerdict(
                sessionId,
                this.toStoredVerdict(result.verdict),
                result,
            );
        }

        return {
            assistantMessage: assistantContent,
            status: result.status,
            verdict: isFinal ? result.verdict : 'in_progress',
            criteriaRemaining: result.criteria_remaining,
            pendingCriteria:
                result.verdict === 'likely_eligible'
                    ? result.pending_criteria.map((c) => c.criterion)
                    : [],
            details: result.details,
        };
    }

    /** Keep the section: an exclusion criterion must never be judged like an inclusion one. */
    private buildCriteria(trial: Trial): CriterionInput[] {
        return [
            ...trial.inclusionCriteria.map((c) => ({ id: c.id, section: 'inclusion' as const, text: c.text })),
            ...trial.exclusionCriteria.map((c) => ({ id: c.id, section: 'exclusion' as const, text: c.text })),
        ];
    }

    /**
     * What Phase 1 already told us, so the assistant does not ask for it again.
     * Deliberately no name, phone or address — the AI service does not need them.
     */
    private buildPatientContext(patient: Patient): string {
        const lines = [
            `Age: ${this.ageInYears(patient.dateOfBirth)} years old.`,
            `Sex: ${patient.sex.toLowerCase()}.`,
        ];
        if (patient.conditionSummary) {
            lines.push(`Registered condition summary: ${patient.conditionSummary}`);
        }
        return lines.join('\n');
    }

    private ageInYears(dateOfBirth: Date): number {
        const now = new Date();
        let age = now.getFullYear() - dateOfBirth.getFullYear();
        const beforeBirthday =
            now.getMonth() < dateOfBirth.getMonth() ||
            (now.getMonth() === dateOfBirth.getMonth() && now.getDate() < dateOfBirth.getDate());
        if (beforeBirthday) age--;
        return age;
    }

    private toStoredVerdict(verdict: AssessEligibilityResult['verdict']): string {
        switch (verdict) {
            case 'eligible':
                return 'ELIGIBLE';
            case 'not_eligible':
                return 'NOT_ELIGIBLE';
            default:
                return 'LIKELY_ELIGIBLE';
        }
    }

    private buildFinalSummary(result: AssessEligibilityResult): string {
        switch (result.verdict) {
            case 'not_eligible': {
                const blocking = result.details.filter((d) => d.verdict === 'not_eligible');
                const detail = blocking.length
                    ? ` Criteria of note: ${blocking.map((b) => b.criterion).join('; ')}.`
                    : '';
                return `Based on what you've shared, the patient does not appear eligible for this trial.${detail} The study team makes the final decision.`;
            }
            case 'likely_eligible': {
                const n = result.pending_criteria.length;
                return (
                    `Based on what you've shared, nothing rules the patient out for this trial. ` +
                    `${n} requirement${n === 1 ? '' : 's'} couldn't be checked with the information available ` +
                    `and would need to be confirmed by the study team.`
                );
            }
            default:
                return `Based on what you've shared, the patient appears to meet all the criteria for this trial. The study team will still confirm eligibility.`;
        }
    }
}
