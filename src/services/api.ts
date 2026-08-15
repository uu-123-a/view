export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status = 0, data: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = 25000,
): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(input, {
      credentials: "same-origin",
      ...init,
      signal: controller.signal,
    });
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === "AbortError") {
      throw new ApiError("服务响应超时，请稍后重试。", 408);
    }
    if (reason instanceof TypeError) {
      throw new ApiError("无法连接后端服务，请确认 Flask 服务已经启动。", 0, reason);
    }
    throw reason;
  } finally {
    window.clearTimeout(timer);
  }
}

export async function apiJson<T>(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = 25000,
): Promise<T> {
  const response = await apiFetch(input, init, timeoutMs);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof data?.error === "string" ? data.error : `请求失败（${response.status}）`;
    throw new ApiError(message, response.status, data);
  }
  return data as T;
}
