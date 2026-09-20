import { Injectable } from '@nestjs/common';
import { Patient } from '../../../../domain/entities/patient.entity';
import { IPatientRepository } from '../../../../domain/abstracts/IPatientRepository.service';
import { PrismaService } from '../prisma.service';

@Injectable()
export class PatientRepository extends IPatientRepository {
    constructor(private readonly prisma: PrismaService) {
        super();
    }

    async getAll(): Promise<Patient[]> {
        const rows = await this.prisma.patient.findMany({ where: { deletedAt: null } });
        return rows.map((r) => this.toEntity(r));
    }

    async get(id: string): Promise<Patient | null> {
        const row = await this.prisma.patient.findFirst({ where: { id, deletedAt: null } });
        return row ? this.toEntity(row) : null;
    }

    async findAllByCaregiver(caregiverId: string): Promise<Patient[]> {
        const rows = await this.prisma.patient.findMany({
            where: { caregiverId, deletedAt: null },
            orderBy: { createdAt: 'desc' },
        });
        return rows.map((r) => this.toEntity(r));
    }

    async findByIdAndCaregiver(id: string, caregiverId: string): Promise<Patient | null> {
        const row = await this.prisma.patient.findFirst({
            where: { id, caregiverId, deletedAt: null },
        });
        return row ? this.toEntity(row) : null;
    }

    async create(item: Partial<Patient>): Promise<Patient> {
        const row = await this.prisma.patient.create({ data: item as any });
        return this.toEntity(row);
    }

    async update(id: string, item: Partial<Patient>): Promise<Patient | null> {
        const row = await this.prisma.patient.update({ where: { id }, data: item as any });
        return this.toEntity(row);
    }

    async delete(id: string): Promise<boolean> {
        await this.prisma.patient.update({ where: { id }, data: { deletedAt: new Date() } });
        return true;
    }

    private toEntity(row: any): Patient {
        return Object.assign(new Patient(), row);
    }
}