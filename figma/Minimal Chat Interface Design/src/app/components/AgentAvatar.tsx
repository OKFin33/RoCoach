import React from "react";

interface AgentAvatarProps {
  size?: number;
  ringColor?: string; // 'neutral' | 'yellow' | 'orange' | 'gray' | 'blue'
  variant?: "you_know_who" | "ai_assistant";
  thinking?: boolean;
  onClick?: () => void;
  onLongPress?: (anchor: { x: number; y: number }) => void;
  showBadge?: boolean;
}

export function AgentAvatar({
  size = 40,
  ringColor = "neutral",
  variant = "you_know_who",
  thinking = false,
  onClick,
  onLongPress,
  showBadge = true,
}: AgentAvatarProps) {
  const longPressRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    const target = event.currentTarget;
    longPressRef.current = setTimeout(() => {
      const rect = target.getBoundingClientRect();
      onLongPress?.({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      });
    }, 420);
  };

  const handlePointerUp = () => {
    if (longPressRef.current) {
      clearTimeout(longPressRef.current);
      longPressRef.current = null;
    }
  };

  const ringColors: Record<string, string> = {
    neutral: "#2D2D2A",
    yellow: "#F7CF45",
    orange: "#D8892E",
    gray: "#D8D2C2",
    blue: "#4B8FD8",
  };

  const ring = ringColors[ringColor] ?? ringColors.neutral;

  return (
    <div
      style={{ width: size, height: size, cursor: onLongPress ? "pointer" : "default", userSelect: "none" }}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      onClick={onClick}
    >
      <svg
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        style={{
          filter: thinking ? "drop-shadow(0 0 6px rgba(75,143,216,0.55))" : undefined,
        }}
      >
        {/* Outer ring */}
        <circle
          cx="24"
          cy="24"
          r="22.5"
          fill="none"
          stroke={ring}
          strokeWidth="3"
          style={{
            transition: "stroke 0.3s ease",
          }}
        />
        {variant === "ai_assistant" ? (
          <>
            <circle cx="24" cy="24" r="20" fill="#4B8FD8" />
            <circle cx="24" cy="24" r="15" fill="#6EA9E7" opacity="0.55" />
            <path
              d="M12 31 Q24 39 36 31 L36 36 Q30 43 24 43 Q18 43 12 36 Z"
              fill="#2F6FB6"
              opacity="0.7"
            />
            <text
              x="24"
              y="29"
              textAnchor="middle"
              fill="#FFFDF3"
              fontSize="13"
              fontWeight="900"
              fontFamily="Nunito, -apple-system, sans-serif"
            >
              AI
            </text>
          </>
        ) : (
          <>
            {/* Background fill */}
            <circle cx="24" cy="24" r="20" fill="#1A1A18" />

            {/* Hood shape — covers upper ⅔ */}
            <path
              d="M8 24 Q7 8 24 6 Q41 8 40 24 L40 20 Q38 12 24 10 Q10 12 8 20 Z"
              fill="#111110"
            />
            {/* Cloak body — lower portion */}
            <path
              d="M4 34 Q4 44 24 46 Q44 44 44 34 L44 30 Q38 38 24 38 Q10 38 4 30 Z"
              fill="#111110"
            />
            {/* Face/mask area */}
            <ellipse cx="24" cy="26" rx="10" ry="9" fill="#252520" />

            {/* Eye visor / brow bar */}
            <rect x="14.5" y="21" width="19" height="5" rx="2.5" fill="#1A1A18" />

            {/* Left eye glow */}
            <ellipse cx="19.5" cy="23.5" rx="2.2" ry="1.6" fill="#F7CF45" opacity="0.95" />
            <ellipse cx="19.5" cy="23.5" rx="1" ry="0.8" fill="#FFEC80" />

            {/* Right eye glow */}
            <ellipse cx="28.5" cy="23.5" rx="2.2" ry="1.6" fill="#F7CF45" opacity="0.95" />
            <ellipse cx="28.5" cy="23.5" rx="1" ry="0.8" fill="#FFEC80" />

            {/* Lower face / mask chin */}
            <rect x="17" y="28" width="14" height="5" rx="2.5" fill="#1E1E1C" />

            {/* Collar highlight */}
            <ellipse cx="24" cy="36.5" rx="8" ry="3" fill="#1E1E1C" />
          </>
        )}

        {/* Thinking pulse ring (blue) */}
        {thinking && (
          <circle
            cx="24"
            cy="24"
            r="22.5"
            fill="none"
            stroke="#4B8FD8"
            strokeWidth="2.5"
            strokeDasharray="6 4"
            opacity="0.7"
          >
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 24 24"
              to="360 24 24"
              dur="2.5s"
              repeatCount="indefinite"
            />
          </circle>
        )}

        {/* Active persona check badge */}
        {showBadge && ringColor === "yellow" && (
          <g>
            <circle cx="38" cy="10" r="6" fill="#F7CF45" stroke="#171717" strokeWidth="1.5" />
            <path
              d="M35 10 L37.2 12.2 L41 8"
              stroke="#171717"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </g>
        )}
        {/* Fallback shield badge */}
        {ringColor === "orange" && (
          <g>
            <circle cx="38" cy="10" r="6" fill="#D8892E" stroke="#171717" strokeWidth="1.5" />
            <path
              d="M38 6.5 L40.5 8.5 L40.5 11.5 Q40.5 13.5 38 14.5 Q35.5 13.5 35.5 11.5 L35.5 8.5 Z"
              fill="#171717"
              opacity="0.9"
            />
          </g>
        )}
      </svg>
    </div>
  );
}

/** Small user avatar — cartoon style */
export function UserAvatar({ size = 32 }: { size?: number }) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
    >
      {/* Outer ring */}
      <circle cx="20" cy="20" r="18.5" fill="#E8B92E" stroke="#171717" strokeWidth="2.5" />
      {/* Face */}
      <circle cx="20" cy="21" r="13" fill="#FFD8A8" />
      {/* Hat brim */}
      <ellipse cx="20" cy="11" rx="11" ry="4" fill="#5B3FA0" stroke="#171717" strokeWidth="2" />
      {/* Hat top */}
      <rect x="13" y="4" width="14" height="9" rx="4" fill="#7B5FC8" stroke="#171717" strokeWidth="2" />
      {/* Hat band */}
      <rect x="13" y="10" width="14" height="3" rx="1" fill="#F7CF45" />
      {/* Eyes */}
      <circle cx="16.5" cy="21" r="1.8" fill="#171717" />
      <circle cx="23.5" cy="21" r="1.8" fill="#171717" />
      <circle cx="17" cy="20.3" r="0.6" fill="white" />
      <circle cx="24" cy="20.3" r="0.6" fill="white" />
      {/* Cheek blush */}
      <ellipse cx="14" cy="24" rx="2.5" ry="1.5" fill="#FF9B9B" opacity="0.5" />
      <ellipse cx="26" cy="24" rx="2.5" ry="1.5" fill="#FF9B9B" opacity="0.5" />
      {/* Smile */}
      <path d="M16 25.5 Q20 28.5 24 25.5" stroke="#171717" strokeWidth="1.5" strokeLinecap="round" fill="none" />
    </svg>
  );
}
