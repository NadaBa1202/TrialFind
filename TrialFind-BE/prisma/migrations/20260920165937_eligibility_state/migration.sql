-- AlterEnum
ALTER TYPE "EligibilityVerdict" ADD VALUE 'LIKELY_ELIGIBLE';

-- AlterTable
ALTER TABLE "eligibility_messages" ADD COLUMN     "criterionId" TEXT;

-- CreateIndex
CREATE INDEX "eligibility_messages_sessionId_createdAt_idx" ON "eligibility_messages"("sessionId", "createdAt");
