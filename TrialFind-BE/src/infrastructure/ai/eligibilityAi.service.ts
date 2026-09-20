import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import {
    AssessEligibilityInput,
    AssessEligibilityResult,
    IEligibilityAiService,
} from '../../domain/abstracts/IEligibilityAi.service';

@Injectable()
export class EligibilityAiService extends IEligibilityAiService {
    private readonly logger = new Logger(EligibilityAiService.name);

    constructor(private readonly config: ConfigService) {
        super();
    }

    async assess(input: AssessEligibilityInput): Promise<AssessEligibilityResult> {
        const baseUrl = this.config.get<string>('ai.baseUrl');
        const apiKey = this.config.get<string>('ai.apiKey');
        const timeoutMs = this.config.get<number>('ai.timeoutMs') ?? 120_000;

        // The AI service may be a Kaggle notebook behind a tunnel: it can be asleep, restarting,
        // or on a new URL. Surface that as a clean 503 instead of a generic 500.
        const res = await fetch(`${baseUrl}/eligibility/assess`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(apiKey ? { 'x-api-key': apiKey } : {}),
            },
            body: JSON.stringify({
                patient_context: input.patientContext,
                turns: input.turns.map((t) => ({
                    role: t.role,
                    content: t.content,
                    criterion_id: t.criterionId ?? null,
                })),
                criteria: input.criteria,
            }),
            signal: AbortSignal.timeout(timeoutMs),
        }).catch((err: Error) => {
            this.logger.error(`AI service unreachable: ${err.message}`);
            throw new ServiceUnavailableException('The eligibility assistant is temporarily unavailable.');
        });

        if (!res.ok) {
            this.logger.error(`AI service responded with ${res.status}`);
            throw new ServiceUnavailableException('The eligibility assistant is temporarily unavailable.');
        }
        return (await res.json()) as AssessEligibilityResult;
    }
}
