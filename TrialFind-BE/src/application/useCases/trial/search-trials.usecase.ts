import { Injectable } from '@nestjs/common';
import { ITrialRepository } from '../../../domain/abstracts/ITrialRepository.service';
import { Trial, TrialLocation } from '../../../domain/entities/trial.entity';
import { SearchTrialsDto } from '../../dtos/trial/searchTrials.dto';

@Injectable()
export class SearchTrialsUseCase {
    constructor(private readonly trialRepository: ITrialRepository) {}

    async execute(dto: SearchTrialsDto): Promise<Trial[]> {
        const trials = await this.trialRepository.getAll();

        return trials.filter((trial) => {
            if (trial.status !== 'RECRUITING') return false;
            if (!this.matchesAge(trial, dto.age)) return false;
            if (!this.matchesSex(trial, dto.sex)) return false;
            if (!this.matchesCondition(trial, dto.condition, dto.stage)) return false;
            if (dto.locations?.length && !this.matchesLocation(trial, dto.locations)) return false;
            return true;
        });
    }

    private matchesAge(trial: Trial, age: number): boolean {
        if (trial.minAge != null && age < trial.minAge) return false;
        if (trial.maxAge != null && age > trial.maxAge) return false;
        return true;
    }

    private matchesSex(trial: Trial, sex: string): boolean {
        return trial.sex === 'ALL' || trial.sex === sex;
    }

    private matchesCondition(trial: Trial, condition: string, stage?: string): boolean {
        const haystack = [...trial.conditions, trial.title, trial.briefSummary ?? '']
            .join(' ')
            .toLowerCase();

        if (!haystack.includes(condition.toLowerCase())) return false;
        if (stage) return haystack.includes(stage.toLowerCase());
        return true;
    }

    private matchesLocation(trial: Trial, preferred: string[]): boolean {
        return preferred.some((pref) => {
            const prefLower = pref.toLowerCase();
            return (trial.locations as TrialLocation[]).some((loc) =>
                [loc.city, loc.state, loc.country, loc.facility]
                    .filter(Boolean)
                    .some((field) => (field as string).toLowerCase().includes(prefLower)),
            );
        });
    }
}