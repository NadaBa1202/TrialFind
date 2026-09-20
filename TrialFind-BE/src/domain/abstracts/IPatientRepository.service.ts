import { Patient } from '../entities/patient.entity';
import { IRepository } from './IRepository.service';

export abstract class IPatientRepository extends IRepository<Patient> {
    abstract findAllByCaregiver(caregiverId: string): Promise<Patient[]>;
    abstract findByIdAndCaregiver(id: string, caregiverId: string): Promise<Patient | null>;
}