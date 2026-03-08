import { JobMatchCard } from "./JobMatchCard";
import { StaggerContainer, StaggerItem } from "@/lib/motion";
import type { ScoredJobMatch } from "@/lib/types";

interface JobBucketSectionProps {
  title: string;
  jobs: ScoredJobMatch[];
  description?: string;
}

export function JobBucketSection({ title, jobs, description }: JobBucketSectionProps) {
  if (jobs.length === 0) return null;

  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold text-primary">{title}</h2>
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      <StaggerContainer className="grid gap-4 sm:grid-cols-2">
        {jobs.map((job, i) => (
          <StaggerItem key={`${job.bucket}-${job.title}-${job.company}-${i}`}>
            <JobMatchCard job={job} />
          </StaggerItem>
        ))}
      </StaggerContainer>
    </div>
  );
}
