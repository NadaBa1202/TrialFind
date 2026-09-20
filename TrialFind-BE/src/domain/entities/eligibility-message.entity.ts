export type MessageRole = 'CAREGIVER' | 'ASSISTANT';

export class EligibilityMessage {
    id: string;
    sessionId: string;
    role: MessageRole;
    content: string;
    /** On ASSISTANT messages that asked about one specific criterion: that criterion's id. */
    criterionId?: string | null;
    createdAt: Date;
}
