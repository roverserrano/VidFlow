export function ProgressBar({ value }) {
  const percent = typeof value === "number" && value >= 0 ? Math.min(value, 100) : 0;

  return (
    <div className="progress-bar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
      <span style={{ width: `${percent}%` }} />
    </div>
  );
}

