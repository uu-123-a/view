import { useEffect, useRef, useState } from "react";
import { Camera, CameraOff, ShieldCheck, UserRound } from "lucide-react";

type CameraState = "loading" | "active" | "off" | "denied";

export default function CameraPreview() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [state, setState] = useState<CameraState>("loading");

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) { setState("denied"); return; }
    setState("loading");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
      streamRef.current?.getTracks().forEach(track => track.stop());
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setState("active");
    } catch { setState("denied"); }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setState("off");
  }

  useEffect(() => { void startCamera(); return () => streamRef.current?.getTracks().forEach(track => track.stop()); }, []);

  return <div className="camera-card">
    <video ref={videoRef} className={state === "active" ? "camera-video visible" : "camera-video"} autoPlay muted playsInline aria-label="候选人摄像头实时画面" />
    {state !== "active" && <div className="camera-placeholder"><div className="camera-placeholder-icon">{state === "denied" ? <CameraOff size={34} /> : <UserRound size={38} />}</div><strong>{state === "loading" && "正在启动摄像头…"}{state === "off" && "摄像头已关闭"}{state === "denied" && "无法访问摄像头"}</strong><span>{state === "denied" ? "请在浏览器地址栏中允许摄像头权限" : "画面仅在当前浏览器中显示"}</span>{state !== "loading" && <button className="camera-retry" onClick={startCamera}><Camera size={16} /> 开启摄像头</button>}</div>}
    <div className="camera-overlay"><div className="camera-live"><i className={state === "active" ? "on" : ""} />{state === "active" ? "摄像头已开启" : "摄像头未开启"}</div><button className="camera-toggle" onClick={state === "active" ? stopCamera : startCamera} aria-label={state === "active" ? "关闭摄像头" : "开启摄像头"}>{state === "active" ? <CameraOff size={17} /> : <Camera size={17} />}</button></div>
    <div className="camera-privacy"><ShieldCheck size={14} /> 本地实时预览，不会自动上传或保存视频</div>
  </div>;
}
