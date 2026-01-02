CREATE TABLE public."User" (
	id text NOT NULL,
	email text NOT NULL,
	"password" text NULL,
	provider text NOT NULL DEFAULT 'local'::text,
	"providerAccountId" text NULL,
	"role" public."Role" NOT NULL DEFAULT 'USER'::"Role",
	"avatarUrl" text NULL,
	"emailValidated" bool NOT NULL DEFAULT false,
	"emailVerificationToken" text NULL,
	"accessToken" text NULL,
	"resetToken" text NULL,
	"resetTokenExpiry" timestamp(3) NULL,
	"createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"updatedAt" timestamp(3) NOT NULL,
	CONSTRAINT "User_pkey" PRIMARY KEY (id)
);
CREATE UNIQUE INDEX "User_emailVerificationToken_key" ON public."User" USING btree ("emailVerificationToken");
CREATE UNIQUE INDEX "User_email_key" ON public."User" USING btree (email);

CREATE TABLE public."CandidateInterview" (
	id text NOT NULL,
	"userId" text NOT NULL,
	"mockInterviewId" text NOT NULL,
	"level" public."InterviewLevel" NULL,
	status public."CandidateInterviewStatus" NOT NULL DEFAULT 'PENDING'::"CandidateInterviewStatus",
	"recordingUrl" text NULL,
	"codeEditorSnapshot" text NULL,
	"designEditorSnapshot" text NULL,
	"videoRecording" bool NOT NULL DEFAULT false,
	"audioRecording" bool NOT NULL DEFAULT false,
	"dataUsage" bool NOT NULL DEFAULT false,
	terms bool NOT NULL DEFAULT false,
	"createdAt" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"updatedAt" timestamp(3) NOT NULL,
	CONSTRAINT "CandidateInterview_pkey" PRIMARY KEY (id),
	CONSTRAINT "CandidateInterview_mockInterviewId_fkey" FOREIGN KEY ("mockInterviewId") REFERENCES public."MockInterview"(id) ON DELETE RESTRICT ON UPDATE CASCADE,
	CONSTRAINT "CandidateInterview_userId_fkey" FOREIGN KEY ("userId") REFERENCES public."User"(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX "CandidateInterview_mockInterviewId_idx" ON public."CandidateInterview" USING btree ("mockInterviewId");
CREATE INDEX "CandidateInterview_userId_idx" ON public."CandidateInterview" USING btree ("userId");