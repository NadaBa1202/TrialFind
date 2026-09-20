import { Injectable } from '@nestjs/common';
import { AuthException } from '../../exceptions/auth.exception';
import { ICaregiverRepository } from '../../../domain/abstracts/ICaregiverRepository.service';
import { LoginDto } from '../../dtos/auth/login.dto';
import { IHashService } from '../../../domain/abstracts/IHash.service';
import { IJwtService } from '../../../domain/abstracts/IJwt.service';
import { TokenType } from '../../../domain/enums/tokenType.enums';

const MAX_FAILED_ATTEMPTS = 5;
const LOCKOUT_DURATION_MS = 15 * 60 * 1000; // 15 minutes

@Injectable()
export class LoginUseCase {
    constructor(
        private readonly caregiverRepository: ICaregiverRepository,
        private readonly hashService: IHashService,
        private readonly jwtService: IJwtService,
    ) {}

    async execute(dto: LoginDto) {
        const caregiver = await this.caregiverRepository.findByEmail(dto.email);

        // Same generic error whether the email doesn't exist or the password is
        // wrong — never reveal which one it was (account enumeration defense).
        if (!caregiver) {
            throw AuthException.invalidCredentials();
        }

        if (caregiver.isLocked()) {
            throw AuthException.accountLocked();
        }

        const passwordMatches = await this.hashService.compare(dto.password, caregiver.password);
        if (!passwordMatches) {
            const attempts = caregiver.failedLoginAttempts + 1;
            const lockedUntil =
                attempts >= MAX_FAILED_ATTEMPTS ? new Date(Date.now() + LOCKOUT_DURATION_MS) : null;
            await this.caregiverRepository.registerFailedLogin(caregiver.id, lockedUntil);
            throw AuthException.invalidCredentials();
        }

        await this.caregiverRepository.resetFailedLogins(caregiver.id);

        const accessToken = this.jwtService.generateToken(
            { sub: caregiver.id, email: caregiver.email },
            TokenType.ACCESS,
        );
        const refreshToken = this.jwtService.generateToken({ sub: caregiver.id }, TokenType.REFRESH);

        // Store only a hash of the refresh token — a DB leak alone can't be used to
        // forge sessions.
        const refreshTokenHash = await this.hashService.hash(refreshToken);
        await this.caregiverRepository.setRefreshTokenHash(caregiver.id, refreshTokenHash);

        return { accessToken, refreshToken, caregiver: caregiver.toSafeProfile() };
    }
}