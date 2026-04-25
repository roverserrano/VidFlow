export function EmptyState({ title, children }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      {children && <span>{children}</span>}
    </div>
  );
}

