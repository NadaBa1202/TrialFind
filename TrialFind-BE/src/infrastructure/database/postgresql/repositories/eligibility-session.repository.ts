import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { IEligibilitySessionRepository } from '../../../../domain/abstracts/IEligibilitySessionRepository.service';
import { EligibilitySession } from '../../../../domain/entities/eligibility-session.entity';
import { EligibilityMessage, MessageRole } from '../../../../domain/entities/eligibility-message.entity';

@Injectable()
export class EligibilitySessionRepository extends IEligibilitySessionRepository {
    constructor(private readonly prisma: PrismaService) {
        super();
    }

    async create(patientId: string, trialId: string): Promise<EligibilitySession> {
        const row = await this.prisma.eligibilitySession.create({
            data: { patientId, trialId, verdict: 'IN_PROGRESS' },
        });
        return Object.assign(new EligibilitySession(), row);
    }

    async findById(id: string): Promise<EligibilitySession | null> {
        const row = await this.prisma.eligibilitySession.findUnique({ where: { id } });
        return row ? Object.assign(new EligibilitySession(), row) : null;
    }

    async updateVerdict(id: string, verdict: string, detail: Record<string, any>): Promise<void> {
        await this.prisma.eligibilitySession.update({
            where: { id },
            data: { verdict: verdict as any, verdictDetail: detail },
        });
    }

    async addMessage(
        sessionId: string,
        role: MessageRole,
        content: string,
        criterionId?: string | null,
    ): Promise<EligibilityMessage> {
        const row = await this.prisma.eligibilityMessage.create({
            data: { sessionId, role, content, criterionId: criterionId ?? null },
        });
        return Object.assign(new EligibilityMessage(), row);
    }

    async getMessages(sessionId: string): Promise<EligibilityMessage[]> {
        const rows = await this.prisma.eligibilityMessage.findMany({
            where: { sessionId },
            orderBy: { createdAt: 'asc' },
        });
        return rows.map((r) => Object.assign(new EligibilityMessage(), r));
    }
}
