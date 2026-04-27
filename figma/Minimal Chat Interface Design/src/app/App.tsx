import { ChatScreen } from "./components/ChatScreen";

export default function App() {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        minHeight: "100dvh",
        background: "#2A2822",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily:
          "'Nunito', -apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        backgroundImage: `radial-gradient(circle at 30% 20%, rgba(247,207,69,0.08) 0%, transparent 55%),
          radial-gradient(circle at 70% 80%, rgba(75,143,216,0.06) 0%, transparent 50%)`,
      }}
    >
      {/* Phone mockup frame */}
      <div
        style={{
          width: "min(390px, 100vw)",
          height: "min(844px, 100dvh)",
          position: "relative",
          borderRadius: "clamp(0px, calc((100vw - 390px) * 999), 44px)",
          overflow: "hidden",
          boxShadow:
            "0 0 0 1px rgba(255,255,255,0.06), 0 40px 100px rgba(0,0,0,0.65), 0 0 0 8px #111110",
        }}
      >
        {/* App content */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
          }}
        >
          <ChatScreen />
        </div>
      </div>

      {/* Desktop hint */}
      <div
        style={{
          position: "fixed",
          bottom: 18,
          left: "50%",
          transform: "translateX(-50%)",
          fontSize: 11.5,
          color: "rgba(255,255,255,0.22)",
          letterSpacing: "0.4px",
          whiteSpace: "nowrap",
          pointerEvents: "none",
        }}
      >
        长按 Agent 头像切换人格 · 右划边缘打开设置
      </div>
    </div>
  );
}
