import React from "react";
import { motion, AnimatePresence } from "motion/react";
import { Plus } from "lucide-react";

export interface PersonaOption {
  id: string;
  label: string;
  description: string;
  category: "default" | "built_in" | "managed" | "add";
  availability: "available" | "unavailable" | "placeholder";
  initials?: string;
  color?: string;
}

interface PersonaWheelProps {
  open: boolean;
  personas: PersonaOption[];
  selectedId: string;
  anchor?: { x: number; y: number };
  onSelect: (persona: PersonaOption) => void;
  onClose: () => void;
}

const POSITIONS = [
  { angle: -42, label: "upper" },
  { angle: 8, label: "right" },
  { angle: 58, label: "lower" },
];

const RADIUS = 86;

function toXY(angleDeg: number, r: number) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: Math.cos(rad) * r, y: Math.sin(rad) * r };
}

function SelectionBadge() {
  return (
    <div
      style={{
        position: "absolute",
        bottom: -2,
        right: -2,
        width: 16,
        height: 16,
        borderRadius: 999,
        background: "#F7CF45",
        border: "2px solid #171717",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path
          d="M2 5 L4.2 7.2 L8 3"
          stroke="#171717"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function MedallionAvatar({
  persona,
  highlighted,
  selected,
}: {
  persona: PersonaOption;
  highlighted: boolean;
  selected: boolean;
}) {
  const size = 52;

  if (persona.id === "you_know_who") {
    return (
      <div
        style={{
          width: size,
          height: size,
          borderRadius: 999,
          background: "#1A1A18",
          border: highlighted ? "3px solid #F7CF45" : "2.5px solid #171717",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: highlighted
            ? "0 0 14px rgba(247,207,69,0.5), 0 4px 12px rgba(17,17,17,0.3)"
            : "0 4px 12px rgba(17,17,17,0.25)",
          position: "relative",
        }}
      >
        <svg viewBox="0 0 32 32" width={30} height={30}>
          <circle cx="16" cy="16" r="15" fill="#252520" />
          <ellipse cx="16" cy="17" rx="7" ry="6" fill="#1E1E1C" />
          <rect x="9" y="13.5" width="14" height="3.5" rx="1.75" fill="#111110" />
          <ellipse cx="13" cy="15.3" rx="1.6" ry="1.2" fill="#F7CF45" />
          <ellipse cx="19" cy="15.3" rx="1.6" ry="1.2" fill="#F7CF45" />
        </svg>
        {selected && <SelectionBadge />}
      </div>
    );
  }

  if (persona.id === "ai_assistant") {
    return (
      <div
        style={{
          width: size,
          height: size,
          borderRadius: 999,
          background: "#4B8FD8",
          border: highlighted ? "3px solid #F7CF45" : "2.5px solid #171717",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: highlighted
            ? "0 0 14px rgba(247,207,69,0.45), 0 4px 12px rgba(17,17,17,0.25)"
            : "0 4px 12px rgba(17,17,17,0.2)",
          position: "relative",
        }}
      >
        <span
          style={{
            fontFamily: "'Nunito', sans-serif",
            fontWeight: 900,
            fontSize: 18,
            color: "white",
            letterSpacing: "-1px",
          }}
        >
          AI
        </span>
        {selected && <SelectionBadge />}
      </div>
    );
  }

  if (persona.category === "add") {
    return (
      <div
        style={{
          width: size,
          height: size,
          borderRadius: 999,
          background: "rgba(255,248,232,0.72)",
          border: "2.5px dashed rgba(23,23,23,0.44)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 12px rgba(17,17,17,0.14)",
        }}
      >
        <Plus size={21} color="rgba(23,23,23,0.62)" strokeWidth={2.6} />
      </div>
    );
  }

  const bgColor = persona.color || "#4B8FD8";
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 999,
        background: bgColor,
        border: highlighted ? "3px solid #F7CF45" : "2.5px solid #171717",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: highlighted
          ? "0 0 14px rgba(247,207,69,0.45), 0 4px 12px rgba(17,17,17,0.25)"
          : "0 4px 12px rgba(17,17,17,0.2)",
        position: "relative",
      }}
    >
      <span
        style={{
          fontFamily: "'Nunito', sans-serif",
          fontWeight: 900,
          fontSize: 18,
          color: "white",
          letterSpacing: "-1px",
        }}
      >
        {persona.initials}
      </span>
      {selected && <SelectionBadge />}
    </div>
  );
}

export function PersonaWheel({
  open,
  personas,
  selectedId,
  anchor,
  onSelect,
  onClose,
}: PersonaWheelProps) {
  const visiblePersonas = personas.slice(0, 3);
  const [hoveredId, setHoveredId] = React.useState<string | null>(selectedId);

  React.useEffect(() => {
    if (open) {
      setHoveredId(null);
    }
  }, [open]);

  const center = anchor ?? { x: 86, y: 180 };

  const optionCenters = visiblePersonas.map((persona, i) => {
    const offset = toXY(POSITIONS[i]?.angle ?? 0, RADIUS);
    return {
      persona,
      x: center.x + offset.x,
      y: center.y + offset.y,
    };
  });

  const updateHoverFromPointer = (event: React.PointerEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    let nearest: { id: string; distance: number } | null = null;

    for (const point of optionCenters) {
      const distance = Math.hypot(point.x - x, point.y - y);
      if (!nearest || distance < nearest.distance) {
        nearest = { id: point.persona.id, distance };
      }
    }

    setHoveredId(nearest && nearest.distance < 46 ? nearest.id : null);
  };

  const selectHoveredPersona = () => {
    const persona = visiblePersonas.find((item) => item.id === hoveredId);
    if (persona) {
      onSelect(persona);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.18 }}
          onClick={onClose}
          onPointerMove={updateHoverFromPointer}
          onPointerUp={selectHoveredPersona}
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(17,17,17,0.16)",
            zIndex: 50,
            backdropFilter: "blur(0.5px)",
          }}
        >
          {/* Avatar-anchored wheel */}
          <div
            style={{ position: "absolute", inset: 0 }}
          >
            <motion.div
              initial={{ scale: 0.82, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.82, opacity: 0 }}
              transition={{ duration: 0.16 }}
              style={{
                position: "absolute",
                left: center.x - 43,
                top: center.y - 43,
                width: 86,
                height: 86,
                borderRadius: 999,
                border: "3px solid rgba(247,207,69,0.95)",
                boxShadow:
                  "0 0 0 3px rgba(23,23,23,0.8), 0 8px 22px rgba(17,17,17,0.24)",
                pointerEvents: "none",
              }}
            />

            {/* Medallions */}
            {optionCenters.map(({ persona, x, y }, i) => {
              const isSelected = persona.id === selectedId;
              const isHovered = persona.id === hoveredId;

              return (
                <motion.div
                  key={persona.id}
                  initial={{ scale: 0, opacity: 0, x: 0, y: 0 }}
                  animate={{
                    scale: 1,
                    opacity: 1,
                    x: x - 26,
                    y: y - 26,
                  }}
                  exit={{ scale: 0, opacity: 0, x: 0, y: 0 }}
                  transition={{
                    type: "spring",
                    stiffness: 380,
                    damping: 26,
                    delay: i * 0.05,
                  }}
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    zIndex: isHovered ? 120 : 90 - i,
                    cursor: persona.availability === "placeholder" ? "default" : "pointer",
                    filter: isHovered
                      ? "drop-shadow(0 0 10px rgba(247,207,69,0.95))"
                      : undefined,
                  }}
                  onClick={(event) => {
                    event.stopPropagation();
                    if (persona.availability !== "placeholder") {
                      onSelect(persona);
                    }
                  }}
                >
        <MedallionAvatar persona={persona} highlighted={isSelected || isHovered} selected={isSelected} />
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
