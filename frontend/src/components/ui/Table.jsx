import clsx from "clsx";
import { Button } from "./primitives";

export function Table({ columns, rows, rowKey = "id", empty }) {
  if (!rows?.length) return empty || null;
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={clsx(
                  "px-4 py-3 text-left font-semibold text-slate-600",
                  c.align === "right" && "text-right",
                  c.className
                )}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row) => (
            <tr key={row[rowKey]} className="hover:bg-slate-50/70">
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={clsx("px-4 py-3 text-slate-700", c.align === "right" && "text-right")}
                >
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({ pagination, onChange }) {
  if (!pagination) return null;
  const { page, total_pages, total, page_size } = pagination;
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-200 px-4 py-3 text-sm text-slate-500 sm:flex-row">
      <span>
        Tổng <strong>{total}</strong> bản ghi · Trang {page}/{total_pages || 1} · {page_size}/trang
      </span>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          className="px-3 py-1"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Trước
        </Button>
        <Button
          variant="secondary"
          className="px-3 py-1"
          disabled={page >= (total_pages || 1)}
          onClick={() => onChange(page + 1)}
        >
          Sau
        </Button>
      </div>
    </div>
  );
}
