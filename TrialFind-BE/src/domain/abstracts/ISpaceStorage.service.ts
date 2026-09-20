export abstract class ISpaceStorage {
    abstract getFile(fileName: string): Promise<object>;
    abstract uploadFile(file: Express.Multer.File, filename: string): Promise<string>;
    abstract uploadPublicFile(file: Express.Multer.File, filename: string): Promise<string>;
    abstract deleteFile(filename: string): Promise<string>;
}