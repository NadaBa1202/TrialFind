import { Module } from '@nestjs/common';
import { IHashService } from '../../domain/abstracts/IHash.service';
import { BcryptService } from './bcrypt.service';

@Module({
    providers: [{ provide: IHashService, useClass: BcryptService }],
    exports: [IHashService],
})
export class BcryptModule {}