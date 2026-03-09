import { ShimmerBar } from "@/lib/motion";

export function PlanSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Loading your plan">
      <div className="space-y-3">
        <ShimmerBar height="2.5rem" width="80%" />
        <ShimmerBar height="1.25rem" width="55%" />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <ShimmerBar height="10rem" className="rounded-xl" />
        <ShimmerBar height="10rem" className="rounded-xl" />
        <ShimmerBar height="10rem" className="rounded-xl" />
      </div>

      <ShimmerBar height="1px" width="100%" />

      <div className="space-y-3">
        <ShimmerBar height="1.5rem" width="40%" />
        <div className="grid gap-4 sm:grid-cols-2">
          <ShimmerBar height="7rem" className="rounded-xl" />
          <ShimmerBar height="7rem" className="rounded-xl" />
          <ShimmerBar height="7rem" className="rounded-xl" />
          <ShimmerBar height="7rem" className="rounded-xl" />
        </div>
      </div>

      <ShimmerBar height="1px" width="100%" />

      <div className="space-y-3">
        <ShimmerBar height="1.5rem" width="30%" />
        <div className="grid gap-4 sm:grid-cols-2">
          <ShimmerBar height="8rem" className="rounded-xl" />
          <ShimmerBar height="8rem" className="rounded-xl" />
        </div>
      </div>

      <ShimmerBar height="1px" width="100%" />

      <ShimmerBar height="12rem" className="rounded-xl" />
    </div>
  );
}
