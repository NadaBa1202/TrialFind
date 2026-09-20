import { Injectable } from '@nestjs/common';
import { AuthException } from '../../exceptions/auth.exception';
import { ICaregiverRepository } from '../../../domain/abstracts/ICaregiverRepository.service';
import { IHashService } from '../../../domain/abstracts/IHash.service';
import { IJwtService } from '../../../domain/abstracts/IJwt.service';
import { TokenType } from '../../../domain/enums/tokenType.enums';

@Injectable()
export class RefreshUseCase {
    constructor(
        private readonly caregiverRepository: ICaregiverRepository,
        private readonly hashService: IHashService,
        private readonly jwtService: IJwtService,
    ) {}

    /** caregiverId + rawRefreshToken come from a refresh token the passport strategy already verified. */
    async execute(caregiverId: string, presentedRefreshToken: string) {
        const caregiver = await this.caregiverRepository.get(caregiverId);
        if (!caregiver || !caregiver.refreshTokenHash) {
            throw AuthException.invalidOrExpiredToken();
        }

        const matches = await this.hashService.compare(
            presentedRefreshToken,
            caregiver.refreshTokenHash,
        );
        if (!matches) {
            // Presented token doesn't match what we last issued — possible reuse of a
            // stolen/rotated-out token. Invalidate the session entirely.
            await this.caregiverRepository.setRefreshTokenHash(caregiver.id, null);
            throw AuthException.invalidOrExpiredToken();
        }

        const accessToken = this.jwtService.generateToken(
            { sub: caregiver.id, email: caregiver.email },
            TokenType.ACCESS,
        );
        const newRefreshToken = this.jwtService.generateToken(
            { sub: caregiver.id },
            TokenType.REFRESH,
        );
        const newRefreshTokenHash = await this.hashService.hash(newRefreshToken);
        await this.caregiverRepository.setRefreshTokenHash(caregiver.id, newRefreshTokenHash);

        return { accessToken, refreshToken: newRefreshToken };
    }

    async logout(caregiverId: string): Promise<void> {
        await this.caregiverRepository.setRefreshTokenHash(caregiverId, null);
    }
}