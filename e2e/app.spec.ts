import { expect, test, type Page } from "@playwright/test";
const user = { id: 101, name: "端到端测试用户", email: "e2e@example.com", role: "user" };
async function mockApi(page: Page, authenticated = false) {
  await page.route("**/api/**", async route => { const request = route.request(); const path = new URL(request.url()).pathname;
    if (path === "/api/auth/me") return route.fulfill({ status: authenticated ? 200 : 401, json: { user: authenticated ? user : null } });
    if (path === "/api/admin/auth/me") return route.fulfill({ status: 401, json: { admin: null } });
    if (path === "/api/interviews/history") return route.fulfill({ json: { items: [] } });
    if (path === "/api/interviews/practice-progress") return route.fulfill({ json: { items: [] } });
    if (path === "/api/training-plan") return route.fulfill({ json: { plan: null, tasks: [] } });
    if (path === "/api/notifications") return route.fulfill({ json: { items: [], unread: 0 } });
    if (path === "/api/resumes") return route.fulfill({ json: { items: [] } });
    if (path === "/api/auth/login") return route.fulfill({ json: { user } });
    if (path === "/api/interviews/sessions") return route.fulfill({ status: 201, json: { session_id: "e2e-session", question: "请介绍一个最有代表性的项目。", question_number: 1, max_questions: 5, source: "fallback", mode: "interview" } });
    return route.fulfill({ json: {} });
  });
}
test("登录页可见且可切换注册与管理员入口", async ({ page }) => { await mockApi(page); await page.goto("/"); await expect(page.getByRole("heading", { name: "继续你的面试训练" })).toBeVisible(); await expect(page.getByText("把每一次练习")).toBeVisible(); await page.getByRole("button", { name: "注册" }).click(); await expect(page.getByRole("heading", { name: "从今天开始稳定进步" })).toBeVisible(); await page.getByRole("button", { name: "管理员独立入口" }).click(); await expect(page.getByRole("heading", { name: "管理员独立登录" })).toBeVisible(); await page.getByRole("button", { name: "返回普通用户登录" }).click(); await expect(page.getByRole("heading", { name: "继续你的面试训练" })).toBeVisible(); });
test("登录后显示导航并进入面试设置", async ({ page }) => { await mockApi(page, true); await page.goto("/"); const interviewNav = page.getByRole("button", { name: "模拟面试", exact: true }); await expect(interviewNav).toBeVisible(); await interviewNav.click(); await expect(page.getByRole("heading", { name: "定制你的面试场景" })).toBeVisible(); await expect(page.getByRole("button", { name: /进入面试间/ })).toBeVisible(); });
test("面试房间显示摄像头区域和回答框", async ({ page }) => { await mockApi(page, true); await page.addInitScript(() => { Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: undefined }); Object.defineProperty(window, "speechSynthesis", { configurable: true, value: { cancel() {}, speak() {} } }); }); await page.goto("/"); await page.getByRole("button", { name: "模拟面试", exact: true }).click(); await page.getByRole("button", { name: /进入面试间/ }).click(); await expect(page.getByText("MOSS 面试官 · 当前任务")).toBeVisible(); await expect(page.locator(".camera-card")).toBeVisible(); await expect(page.getByText("无法访问摄像头")).toBeVisible(); await expect(page.getByPlaceholder("输入回答，或点击麦克风进行语音作答…")).toBeVisible(); await expect(page.getByRole("button", { name: /语音回答/ })).toBeVisible(); });
