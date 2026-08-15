export { mockInterviewFeature } from "./mock-interview";
export { emotionFeedbackFeature } from "./emotion-feedback";
export { interviewReportFeature } from "./interview-report";
export { knowledgeGraphFeature } from "./knowledge-graph";
export { jobsFeature } from "./jobs";
export { learningPathFeature } from "./learning-path";
export { careersFeature } from "./careers";
export { userCenterFeature } from "./user-center";

export type ProductFeature = {
  id: string;
  name: string;
  description: string;
  route: string;
};
