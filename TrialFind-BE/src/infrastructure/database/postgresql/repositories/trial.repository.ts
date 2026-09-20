import { Injectable } from '@nestjs/common';
import { Trial } from '../../../../domain/entities/trial.entity';
import { ITrialRepository } from '../../../../domain/abstracts/ITrialRepository.service';
import { PrismaService } from '../prisma.service';

@Injectable()
export class TrialRepository extends ITrialRepository {
    constructor(private readonly prisma: PrismaService) {
        super();
    }

    async getAll(): Promise<Trial[]> {
        const rows = await this.prisma.trial.findMany();
        return rows.map((r) => Object.assign(new Trial(), r));
    }

    async findById(id: string): Promise<Trial | null> {
        const row = await this.prisma.trial.findUnique({ where: { id } });
        return row ? Object.assign(new Trial(), row) : null;
    }
}