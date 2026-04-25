export function StatusBar({ status, progress }) {
  const visibleProgress = typeof progress === "number" && progress >= 0;

  return (
    <footer className="status-bar">
      <span>{status}</span>
      {visibleProgress && (
        <div className="status-progress" aria-label="Progreso global">
          <span style={{ width: `${Math.min(progress, 100)}%` }} />
        </div>
      )}
      {visibleProgress && <strong>{progress.toFixed(1)}%</strong>}
    </footer>
  );
}

