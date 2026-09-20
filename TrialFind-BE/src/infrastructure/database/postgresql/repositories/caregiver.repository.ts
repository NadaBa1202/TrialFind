import { Injectable } from '@nestjs/common';
import { Caregiver } from '../../../../domain/entities/caregiver.entity';
import { ICaregiverRepository } from '../../../../domain/abstracts/ICaregiverRepository.service';
import { PrismaService } from '../prisma.service';
import { CaregiverModel } from '../models/caregiver.model';

@Injectable()
export class CaregiverRepository extends ICaregiverRepository {
    constructor(private readonly prisma: PrismaService) {
        super();
    }

    async getAll(): Promise<Caregiver[]> {
        const rows = await this.prisma.caregiver.findMany({ where: { deletedAt: null } });
        return rows.map((r) => this.toEntity(r));
    }

    async get(id: string): Promise<Caregiver | null> {
        const row = await this.prisma.caregiver.findFirst({ where: { id, deletedAt: null } });
        return row ? this.toEntity(row) : null;
    }

    async findByEmail(email: string): Promise<Caregiver | null> {
        const row = await this.prisma.caregiver.findFirst({
            where: { email: email.toLowerCase(), deletedAt: null },
        });
        return row ? this.toEntity(row) : null;
    }

    async create(item: Partial<Caregiver>): Promise<Caregiver> {
        const row = await this.prisma.caregiver.create({ data: item as any });
        return this.toEntity(row);
    }

    async update(id: string, item: Partial<Caregiver>): Promise<Caregiver | null> {
        const row = await this.prisma.caregiver.update({ where: { id }, data: item as any });
        return this.toEntity(row);
    }

    async delete(id: string): Promise<boolean> {
        await this.prisma.caregiver.update({ where: { id }, data: { deletedAt: new Date() } });
        return true;
    }

    async setRefreshTokenHash(id: string, hash: string | null): Promise<void> {
        await this.prisma.caregiver.update({ where: { id }, data: { refreshTokenHash: hash } });
    }

    async setPasswordResetToken(
        id: string,
        hash: string | null,
        expiresAt: Date | null,
    ): Promise<void> {
        await this.prisma.caregiver.update({
            where: { id },
            data: { passwordResetTokenHash: hash, passwordResetExpiresAt: expiresAt },
        });
    }

    async registerFailedLogin(id: string, lockedUntil: Date | null): Promise<void> {
        await this.prisma.caregiver.update({
            where: { id },
            data: { failedLoginAttempts: { increment: 1 }, lockedUntil },
        });
    }

    async resetFailedLogins(id: string): Promise<void> {
        await this.prisma.caregiver.update({
            where: { id },
            data: { failedLoginAttempts: 0, lockedUntil: null },
        });
    }

    private toEntity(row: CaregiverModel): Caregiver {
        return Object.assign(new Caregiver(), row);
    }
}