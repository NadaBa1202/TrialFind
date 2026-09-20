import { TokenType } from '../enums/tokenType.enums';

export abstract class IJwtService {
    abstract generateToken(payload: Record<string, any>, tokenType: TokenType): string;
    abstract verifyToken(token: string, tokenType: TokenType): Record<string, any>;
}