import { EligibilitySession } from '../entities/eligibility-session.entity';
import { EligibilityMessage, MessageRole } from '../entities/eligibility-message.entity';

export abstract class IEligibilitySessionRepository {
    abstract create(patientId: string, trialId: string): Promise<EligibilitySession>;
    abstract findById(id: string): Promise<EligibilitySession | null>;
    abstract updateVerdict(id: string, verdict: string, detail: Record<string, any>): Promise<void>;
    abstract addMessage(
        sessionId: string,
        role: MessageRole,
        content: string,
        criterionId?: string | null,
    ): Promise<EligibilityMessage>;
    abstract getMessages(sessionId: string): Promise<EligibilityMessage[]>;
}
