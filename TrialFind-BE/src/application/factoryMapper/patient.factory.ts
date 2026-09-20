import { Injectable } from '@nestjs/common';
import { Patient } from '../../domain/entities/patient.entity';
import { CreatePatientDto } from '../dtos/patient/createPatient.dto';
import { UpdatePatientDto } from '../dtos/patient/updatePatient.dto';

@Injectable()
export class PatientFactory {
    createNewPatient(dto: CreatePatientDto, caregiverId: string): Partial<Patient> {
        return {
            caregiverId,
            firstName: dto.firstName,
            lastName: dto.lastName,
            dateOfBirth: new Date(dto.dateOfBirth),
            sex: dto.sex,
            relationshipToCaregiver: dto.relationshipToCaregiver,
            conditionSummary: dto.conditionSummary ?? null,
            city: dto.city ?? null,
            region: dto.region ?? null,
            country: dto.country ?? null,
        };
    }

    buildUpdatePayload(dto: UpdatePatientDto): Partial<Patient> {
        const payload: Partial<Patient> = {};
        if (dto.firstName !== undefined) payload.firstName = dto.firstName;
        if (dto.lastName !== undefined) payload.lastName = dto.lastName;
        if (dto.dateOfBirth !== undefined) payload.dateOfBirth = new Date(dto.dateOfBirth);
        if (dto.sex !== undefined) payload.sex = dto.sex;
        if (dto.relationshipToCaregiver !== undefined)
            payload.relationshipToCaregiver = dto.relationshipToCaregiver;
        if (dto.conditionSummary !== undefined) payload.conditionSummary = dto.conditionSummary;
        if (dto.city !== undefined) payload.city = dto.city;
        if (dto.region !== undefined) payload.region = dto.region;
        if (dto.country !== undefined) payload.country = dto.country;
        return payload;
    }
}