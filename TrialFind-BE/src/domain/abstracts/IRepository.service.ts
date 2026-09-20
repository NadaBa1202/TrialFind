export abstract class IRepository<T> {
    abstract getAll(): Promise<T[]>;
    abstract get(id: string): Promise<T | null>;
    abstract create(item: Partial<T>): Promise<T>;
    abstract update(id: string, item: Partial<T>): Promise<T | null>;
    abstract delete(id: string): Promise<boolean>;
}