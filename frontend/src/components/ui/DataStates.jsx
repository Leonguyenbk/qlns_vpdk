import { Spinner } from "./Spinner";
import { Button } from "./primitives";
import { IconInbox, IconAlert, IconRefresh } from "./icons";
import { apiErrorMessage } from "../../lib/api";

export function LoadingState({ label = "Đang tải dữ liệu…" }) {
  return (
    <div className="flex justify-center py-14">
      <Spinner label={label} />
    </div>
  );
}

export function EmptyState({ title = "Không có dữ liệu", description, action }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-14 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-md border border-rule text-muted">
        <IconInbox size={20} />
      </span>
      <p className="mt-1 font-medium text-ink">{title}</p>
      {description && <p className="max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-14 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-md border border-[color:var(--color-danger-quiet)] bg-[color:var(--color-danger-quiet)] text-danger">
        <IconAlert size={20} />
      </span>
      <p className="max-w-sm font-medium text-danger">{apiErrorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          <IconRefresh size={15} />
          Thử lại
        </Button>
      )}
    </div>
  );
}
