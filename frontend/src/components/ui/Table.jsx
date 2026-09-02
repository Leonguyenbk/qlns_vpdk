import clsx from "clsx";
import { Button } from "./primitives";
import { IconChevronLeft, IconChevronRight } from "./icons";

export function Table({ columns, rows, rowKey = "id", empty }) {
  if (!rows?.length) return empty || null;
  return (
    <div className="overflow-x-auto">
      <table className="tabular min-w-full text-sm">
        <thead>
          <tr className="border-b border-rule-2">
            {columns.map((c) => (
              <th
                key={c.key}
                className={clsx(
                  "eyebrow px-4 py-2.5 text-left align-bottom",
                  c.align === "right" && "text-right",
                  c.className
                )}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row[rowKey]}
              className="border-b border-rule transition-colors last:border-0 hover:bg-paper-2"
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={clsx(
                    "px-4 py-3 text-ink-2",
                    c.align === "right" && "text-right",
                    c.tdClassName
                  )}
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
  const pages = total_pages || 1;
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-rule px-4 py-3 text-xs text-muted sm:flex-row">
      <span className="mono">
        {total} bản ghi · trang {page}/{pages} · {page_size}/trang
      </span>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          className="px-2.5 py-1"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          <IconChevronLeft size={15} />
          Trước
        </Button>
        <Button
          variant="secondary"
          className="px-2.5 py-1"
          disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Sau
          <IconChevronRight size={15} />
        </Button>
      </div>
    </div>
  );
}
