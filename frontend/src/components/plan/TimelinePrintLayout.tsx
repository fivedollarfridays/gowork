import type { ActionPlan } from "@/lib/types";
import { sectionHeading, sectionSpacing } from "./pdf-styles";

const CATEGORY_PREFIX: Record<string, string> = {
  job_application: "Job",
  benefits_enrollment: "Benefits",
  credit_repair: "Credit",
  criminal_record: "Legal",
  training: "Training",
  career_center: "Career Center",
  housing: "Housing",
  childcare: "Childcare",
};

interface TimelinePrintLayoutProps {
  actionPlan: ActionPlan;
}

export function TimelinePrintLayout({ actionPlan }: TimelinePrintLayoutProps) {
  const nonEmpty = actionPlan.phases.filter((p) => p.actions.length > 0);
  if (nonEmpty.length === 0) return null;

  return (
    <div style={sectionSpacing}>
      <h2 style={sectionHeading}>Action Plan Timeline</h2>
      {nonEmpty.map((phase) => (
        <div key={phase.phase_id} style={{ marginBottom: "10px" }}>
          <p style={{ fontWeight: "bold", fontSize: "13px", margin: "0 0 4px" }}>
            {phase.label}
          </p>
          <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "11px" }}>
            {phase.actions.map((action, i) => {
              const prefix = CATEGORY_PREFIX[action.category] ?? "";
              return (
                <li key={i} style={{ marginBottom: "2px" }}>
                  {prefix && <span style={{ color: "#6b7280" }}>[{prefix}] </span>}
                  {action.title}
                  {action.detail && (
                    <span style={{ color: "#6b7280" }}> — {action.detail}</span>
                  )}
                  {action.resource_phone && (
                    <span style={{ color: "#6b7280" }}> ({action.resource_phone})</span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
