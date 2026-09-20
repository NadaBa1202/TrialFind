import { Base } from './base.entity';
import { Sex } from '../enums/sex.enums';

export class Patient extends Base {
    caregiverId: string;

    firstName: string;
    lastName: string;
    dateOfBirth: Date;
    sex: Sex;

    relationshipToCaregiver: string;
    conditionSummary?: string | null;

    city?: string | null;
    region?: string | null;
    country?: string | null;
}