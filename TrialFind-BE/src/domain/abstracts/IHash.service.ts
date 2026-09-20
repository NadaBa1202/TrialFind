export abstract class IHashService {
    abstract hash(plain: string): Promise<string>;
    abstract compare(plain: string, hashed: string): Promise<boolean>;
}