export type Stage = "home" | "profile" | "reviewNotes" | "schedule" | "applications" | "knowledge" | "career" | "resumeCenter" | "notifications" | "jobs" | "setup" | "interview" | "report" | "history" | "mistakes" | "admin" | "adminJobs" | "system" | "analytics";

export type Message = {
  role: "ai" | "user";
  text: string;
  evaluation?: {
    score: number;
    level: string;
    feedback: string;
    strength: string;
    improvement: string;
    source: "spark" | "fallback";
    emotion?: EmotionObservation;
  };
};

export type EmotionObservation = {
  label: "confident" | "calm" | "nervous" | "positive";
  label_text: string;
  confidence: number;
  tension: number;
  positivity: number;
  stability: number;
  tip: string;
  basis: "answer_text";
  disclaimer: string;
};

export type InterviewHistory = {
  id?: string;
  date: string;
  role: string;
  score: number;
  type: string;
  duration_seconds?: number;
};
