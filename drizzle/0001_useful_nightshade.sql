CREATE TABLE `aptitude_attempts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`candidateId` int NOT NULL,
	`answers` json NOT NULL,
	`scoreCorrect` int NOT NULL,
	`scoreTotal` int NOT NULL,
	`scorePercent` int NOT NULL,
	`passed` boolean NOT NULL,
	`categoryBreakdown` json,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `aptitude_attempts_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `candidates` (
	`id` int AUTO_INCREMENT NOT NULL,
	`fullName` varchar(200) NOT NULL,
	`birthdate` date NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `candidates_id` PRIMARY KEY(`id`),
	CONSTRAINT `candidates_name_dob_unique` UNIQUE(`fullName`,`birthdate`)
);
--> statement-breakpoint
CREATE TABLE `safety_progress` (
	`id` int AUTO_INCREMENT NOT NULL,
	`candidateId` int NOT NULL,
	`lessonId` varchar(64) NOT NULL,
	`videoWatched` boolean NOT NULL DEFAULT false,
	`watchedAt` timestamp,
	`bestQuizPercent` int,
	`quizPassed` boolean NOT NULL DEFAULT false,
	`completedAt` timestamp,
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `safety_progress_id` PRIMARY KEY(`id`),
	CONSTRAINT `safety_progress_candidate_lesson` UNIQUE(`candidateId`,`lessonId`)
);
--> statement-breakpoint
CREATE TABLE `safety_quiz_attempts` (
	`id` int AUTO_INCREMENT NOT NULL,
	`candidateId` int NOT NULL,
	`lessonId` varchar(64) NOT NULL,
	`answers` json NOT NULL,
	`scoreCorrect` int NOT NULL,
	`scoreTotal` int NOT NULL,
	`scorePercent` int NOT NULL,
	`passed` boolean NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `safety_quiz_attempts_id` PRIMARY KEY(`id`)
);
