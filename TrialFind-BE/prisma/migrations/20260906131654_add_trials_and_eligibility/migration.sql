-- CreateEnum
CREATE TYPE "EligibilityVerdict" AS ENUM ('ELIGIBLE', 'NOT_ELIGIBLE', 'UNKNOWN', 'IN_PROGRESS');

-- CreateEnum
CREATE TYPE "MessageRole" AS ENUM ('CAREGIVER', 'ASSISTANT');

-- CreateTable
CREATE TABLE "trials" (
    "id" TEXT NOT NULL,
    "nctId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "conditions" TEXT[],
    "minAge" INTEGER,
    "maxAge" INTEGER,
    "sex" TEXT NOT NULL,
    "inclusionCriteria" JSONB NOT NULL,
    "exclusionCriteria" JSONB NOT NULL,
    "phases" TEXT[],
    "briefSummary" TEXT,
    "studyUrl" TEXT,
    "locations" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "trials_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "eligibility_sessions" (
    "id" TEXT NOT NULL,
    "patientId" TEXT NOT NULL,
    "trialId" TEXT NOT NULL,
    "verdict" "EligibilityVerdict" NOT NULL DEFAULT 'IN_PROGRESS',
    "verdictDetail" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "eligibility_sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "eligibility_messages" (
    "id" TEXT NOT NULL,
    "sessionId" TEXT NOT NULL,
    "role" "MessageRole" NOT NULL,
    "content" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "eligibility_messages_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "trials_nctId_key" ON "trials"("nctId");

-- AddForeignKey
ALTER TABLE "eligibility_sessions" ADD CONSTRAINT "eligibility_sessions_patientId_fkey" FOREIGN KEY ("patientId") REFERENCES "patients"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "eligibility_sessions" ADD CONSTRAINT "eligibility_sessions_trialId_fkey" FOREIGN KEY ("trialId") REFERENCES "trials"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "eligibility_messages" ADD CONSTRAINT "eligibility_messages_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "eligibility_sessions"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
