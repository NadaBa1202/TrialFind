import { PartialType } from '@nestjs/swagger';
import { CreatePatientDto } from './createPatient.dto';

export class UpdatePatientDto extends PartialType(CreatePatientDto) {}