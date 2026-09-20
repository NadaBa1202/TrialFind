import { Trial } from '../entities/trial.entity';

export abstract class ITrialRepository {
    abstract getAll(): Promise<Trial[]>;
    abstract findById(id: string): Promise<Trial | null>;
}