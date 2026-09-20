import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as bcrypt from 'bcrypt';
import { IHashService } from '../../domain/abstracts/IHash.service';

@Injectable()
export class BcryptService extends IHashService {
    private readonly saltRounds: number;

    constructor(private readonly config: ConfigService) {
        super();
        this.saltRounds = this.config.get<number>('security.bcryptSaltRounds') ?? 12;
    }

    async hash(plain: string): Promise<string> {
        return bcrypt.hash(plain, this.saltRounds);
    }

    async compare(plain: string, hashed: string): Promise<boolean> {
        return bcrypt.compare(plain, hashed);
    }
}