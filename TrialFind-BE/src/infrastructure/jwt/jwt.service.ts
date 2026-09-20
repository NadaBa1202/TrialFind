import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService as NestJwtService } from '@nestjs/jwt';
import { IJwtService } from '../../domain/abstracts/IJwt.service';
import { TokenType } from '../../domain/enums/tokenType.enums';

@Injectable()
export class JwtServiceImpl extends IJwtService {
    constructor(
        private readonly jwt: NestJwtService,
        private readonly config: ConfigService,
    ) {
        super();
    }

    generateToken(payload: Record<string, any>, tokenType: TokenType): string {
        const { secret, expiresIn } = this.configFor(tokenType);
        return this.jwt.sign(payload, { secret, expiresIn });
    }

    verifyToken(token: string, tokenType: TokenType): Record<string, any> {
        const { secret } = this.configFor(tokenType);
        // Throws JsonWebTokenError/TokenExpiredError on failure — callers must catch
        // and translate to AuthException.invalidOrExpiredToken() rather than leaking
        // the raw jwt error to the client.
        return this.jwt.verify(token, { secret });
    }

    private configFor(tokenType: TokenType): { secret: string; expiresIn: string } {
        switch (tokenType) {
            case TokenType.ACCESS:
                return {
                    secret: this.config.get<string>('jwt.access.secret'),
                    expiresIn: this.config.get<string>('jwt.access.expiresIn'),
                };
            case TokenType.REFRESH:
                return {
                    secret: this.config.get<string>('jwt.refresh.secret'),
                    expiresIn: this.config.get<string>('jwt.refresh.expiresIn'),
                };
            case TokenType.RESET:
                return {
                    secret: this.config.get<string>('jwt.reset.secret'),
                    expiresIn: this.config.get<string>('jwt.reset.expiresIn'),
                };
        }
    }
}