/* The demo's limits, as the server enforces them. The browser checks them first so most refusals need no round trip,
   but the server stays the authority. */
export const LIMITS = {
  fileMb: 5,
  pages: 30,
  files: 3,
  minutes: 30,
  questionChars: 500,
  questionsPerHour: 20,
  sentHistoryTurns: 5, /* earlier answered turns sent with each question, so follow-ups work */
  historyAnswerChars: 600, /* each earlier answer is cut to this many characters before it is sent */
  historyTurns: 20, /* questions kept on screen; the oldest drop off first */
};

export const MAX_FILE_BYTES = LIMITS.fileMb * 1024 * 1024;

export const MESSAGES = {
  notPdf: "Only PDF files are supported.",
  tooBig: `This file is larger than ${LIMITS.fileMb} MB.`,
  tooManyFiles: `You can have up to ${LIMITS.files} files at a time. Delete one to add another.`,
  questionTooLong: `Questions can be up to ${LIMITS.questionChars} characters.`,
};

/* "28 min left" for the list; the last minute is "Under a minute left" */
export function formatTimeLeft(seconds) {
  if (seconds < 60) return "Under a minute left";
  return `${Math.ceil(seconds / 60)} min left`;
}
