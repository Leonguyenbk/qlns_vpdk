import { Spinner } from "./Spinner";
import { Button } from "./primitives";
import { apiErrorMessage } from "../../lib/api";

export function LoadingState({ label = "Đang tải dữ liệu..." }) {
  return (
    <div className="flex justify-center py-12">
      <Spinner label={label} />
    </div>
  );
}

export function EmptyState({ title = "Không có dữ liệu", description, action }) {
  return (
    <div className="flex flex-col items-center gap-2 py-12 text-center">
      <div className="text-3xl">📭</div>
      <p className="font-medium text-slate-700">{title}</p>
      {description && <p className="max-w-sm text-sm text-slate-500">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center">
      <div className="text-3xl">⚠️</div>
      <p className="font-medium text-red-600">{apiErrorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Thử lại
        </Button>
      )}
    </div>
  );
}
