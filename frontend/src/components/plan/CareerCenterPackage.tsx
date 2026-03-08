import { forwardRef } from "react";
import type { CareerCenterPackage as CCPackage } from "@/lib/types";

const pageHeading = { fontSize: "18pt", fontWeight: "bold", borderBottom: "2px solid #000", paddingBottom: "6px", marginBottom: "12px" } as const;
const heading = { fontSize: "14pt", fontWeight: "bold", marginBottom: "8px" } as const;
const subheading = { fontSize: "12pt", fontWeight: "bold", marginBottom: "6px" } as const;
const spacing = { marginBottom: "12px" } as const;
const checkMark = "\u2713";
const crossMark = "\u2717";

function StaffSummarySection({ data }: { data: CCPackage }) {
  const { staff_summary: s } = data;
  return (
    <div>
      <h1 style={pageHeading}>
        Career Center Ready Package: Staff Summary
      </h1>
      <div style={spacing}>
        <h2 style={subheading}>Employment Goal</h2>
        <p style={{ margin: 0 }}>{s.employment_goal}</p>
      </div>
      <div style={spacing}>
        <h2 style={subheading}>Barrier Profile</h2>
        <ul style={{ margin: 0, paddingLeft: "20px" }}>
          {s.barrier_profile.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
      </div>
      {s.wioa_eligibility && (
        <div style={spacing}>
          <h2 style={subheading}>WIOA Eligibility</h2>
          <ul style={{ margin: 0, paddingLeft: "20px", listStyle: "none" }}>
            <li>{s.wioa_eligibility.adult_program ? checkMark : crossMark} WIOA Adult Program</li>
            <li>{s.wioa_eligibility.supportive_services ? checkMark : crossMark} Supportive Services</li>
            <li>{s.wioa_eligibility.ita_training ? checkMark : crossMark} ITA Training</li>
          </ul>
        </div>
      )}
      <div style={spacing}>
        <h2 style={subheading}>Staff Next Steps</h2>
        <ol style={{ margin: 0, paddingLeft: "20px" }}>
          {s.staff_next_steps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </div>
    </div>
  );
}

function ResidentPlanSection({ data }: { data: CCPackage }) {
  const { resident_plan: r } = data;
  return (
    <div data-page-break style={{ pageBreakBefore: "always" }}>
      <h1 style={pageHeading}>
        YOUR PLAN FOR MONDAY MORNING
      </h1>
      <div style={spacing}>
        <h2 style={subheading}>Documents to Bring</h2>
        <ul style={{ margin: 0, paddingLeft: "20px", listStyle: "none" }}>
          {r.document_checklist.map((doc) => (
            <li key={doc.label}>
              {"[ ] "}{doc.label}{doc.required ? " *" : ""}
            </li>
          ))}
        </ul>
      </div>
      <div style={spacing}>
        <h2 style={subheading}>What to Say</h2>
        <ul style={{ margin: 0, paddingLeft: "20px" }}>
          {r.what_to_say.map((line, i) => (
            <li key={i} style={{ fontStyle: "italic" }}>{line}</li>
          ))}
        </ul>
      </div>
      <div style={spacing}>
        <h2 style={subheading}>What to Expect</h2>
        <ol style={{ margin: 0, paddingLeft: "20px" }}>
          {r.what_to_expect.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ol>
      </div>
      <div style={{ border: "2px solid #000", padding: "12px", ...spacing }}>
        <h2 style={heading}>{r.career_center.name}</h2>
        <p style={{ margin: "2px 0" }}>{r.career_center.address}</p>
        <p style={{ margin: "2px 0" }}>Phone: {r.career_center.phone}</p>
        <p style={{ margin: "2px 0" }}>Hours: {r.career_center.hours}</p>
        <p style={{ margin: "2px 0" }}>Transit: {r.career_center.transit_route}</p>
      </div>
      {r.programs.length > 0 && (
        <div style={spacing}>
          <h2 style={subheading}>Programs You May Qualify For</h2>
          <ul style={{ margin: 0, paddingLeft: "20px" }}>
            {r.programs.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function CreditPathwaySection({ data }: { data: CCPackage }) {
  const c = data.credit_pathway;
  if (!c) return null;
  return (
    <div data-page-break style={{ pageBreakBefore: "always" }}>
      <h1 style={pageHeading}>
        Credit Pathway
      </h1>
      {c.blocking.length > 0 && (
        <div style={spacing}>
          <h2 style={subheading}>Items Blocking Employment</h2>
          <ul style={{ margin: 0, paddingLeft: "20px" }}>
            {c.blocking.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}
      {c.dispute_steps.length > 0 && (
        <div style={spacing}>
          <h2 style={subheading}>Dispute Steps</h2>
          <ol style={{ margin: 0, paddingLeft: "20px" }}>
            {c.dispute_steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}
      {c.free_resources.length > 0 && (
        <div style={spacing}>
          <h2 style={subheading}>Free Resources</h2>
          <ul style={{ margin: 0, paddingLeft: "20px" }}>
            {c.free_resources.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export const CareerCenterPrintLayout = forwardRef<HTMLDivElement, { data: CCPackage }>(
  function CareerCenterPrintLayout({ data }, ref) {
    return (
      <div
        ref={ref}
        style={{
          fontFamily: "Arial, Helvetica, sans-serif",
          fontSize: "11pt",
          lineHeight: "1.5",
          color: "#000",
          background: "#fff",
          padding: "16px",
        }}
      >
        <StaffSummarySection data={data} />
        <ResidentPlanSection data={data} />
        <CreditPathwaySection data={data} />
      </div>
    );
  },
);
