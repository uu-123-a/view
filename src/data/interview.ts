import type { InterviewHistory } from "../types/interview";

export const questions = [
  "请用两分钟介绍一下你自己，并重点说明与目标岗位最相关的经历。",
  "你在项目中遇到过最棘手的技术问题是什么？你是如何定位并解决的？",
  "如果线上模型的准确率突然下降，你会按照什么顺序排查？",
  "请讲一个你与团队成员意见不一致的例子，你最终是如何推进事情的？",
  "为什么选择这个岗位？你希望未来三年在哪些方面获得成长？",
];

export const initialHistory: InterviewHistory[] = [
  { date: "07月26日", role: "多模态算法工程师", score: 82, type: "技术面" },
  { date: "07月19日", role: "大模型应用工程师", score: 76, type: "HR 面" },
  { date: "07月12日", role: "NLP 算法工程师", score: 71, type: "技术面" },
];

export const radar = [
  { name: "专业能力", score: 86 },
  { name: "逻辑表达", score: 78 },
  { name: "岗位匹配", score: 84 },
  { name: "沟通协作", score: 72 },
  { name: "问题解决", score: 88 },
  { name: "稳定自信", score: 75 },
];

export const emotion = [
  { turn: "开场", confidence: 68, tension: 55 },
  { turn: "Q1", confidence: 73, tension: 46 },
  { turn: "Q2", confidence: 80, tension: 35 },
  { turn: "Q3", confidence: 77, tension: 40 },
  { turn: "Q4", confidence: 86, tension: 26 },
];
