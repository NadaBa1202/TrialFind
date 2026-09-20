import { Injectable } from '@nestjs/common';
import { IPatientRepository } from '../../../domain/abstracts/IPatientRepository.service';
import { CreatePatientDto } from '../../dtos/patient/createPatient.dto';
import { PatientFactory } from '../../factoryMapper/patient.factory';

@Injectable()
export class CreatePatientUseCase {
    constructor(
        private readonly patientRepository: IPatientRepository,
        private readonly patientFactory: PatientFactory,
    ) {}

    async execute(dto: CreatePatientDto, caregiverId: string) {
        const newPatient = this.patientFactory.createNewPatient(dto, caregiverId);
        return this.patientRepository.create(newPatient);
    }
}