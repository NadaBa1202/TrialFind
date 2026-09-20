import { OnboardingInput } from "../types/onboarding.inputType";
import { PasswordResetInput } from "../types/passwordReset.inputType";

export abstract class IMailerService {
    abstract passwordResetEmail(input: PasswordResetInput): void;
    abstract passwordResetEmailMobile(input: PasswordResetInput): void;
    abstract onboardingEmail(input: OnboardingInput): void;
}
