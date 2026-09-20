export abstract class Base {
    id: string;
    createdAt: Date;
    updatedAt: Date;
    deletedAt?: Date | null;
}