import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useEmployee } from "../../hooks/useEmployees";
import { TextInput } from "../ui/primitives";
import { IconClose, IconSearch } from "../ui/icons";

/** Tìm và chọn 1 nhân sự theo mã/họ tên/SĐT (tìm phía server, danh sách nhân
 * sự quá lớn để hiển thị hết trong 1 dropdown). Phát ra employee_id đã chọn. */
export function EmployeePicker({ value, onChange, placeholder = "Gõ mã, họ tên hoặc SĐT để tìm…" }) {
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), 300);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    const onDoc = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const { data: selected } = useEmployee(value);
  const { data, isFetching } = useQuery({
    queryKey: ["employees", "picker", debounced],
    queryFn: () =>
      api.get("/employees", { params: { keyword: debounced, page_size: 8 } }).then((r) => r.data.data),
    enabled: !!debounced,
  });
  const results = data?.items || [];

  const pick = (emp) => {
    onChange(emp.id, emp);
    setQuery("");
    setOpen(false);
  };

  if (value && selected) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-rule bg-paper-2 px-3 py-2 text-sm">
        <span className="min-w-0 flex-1 truncate">
          <span className="font-medium text-ink">{selected.full_name}</span>
          <span className="text-muted"> · {selected.employee_code}</span>
          {selected.current_unit && (
            <span className="text-muted"> · {selected.current_unit.name}</span>
          )}
        </span>
        <button
          type="button"
          className="shrink-0 p-1 text-muted hover:text-danger"
          onClick={() => onChange(null, null)}
          aria-label="Bỏ chọn nhân sự"
        >
          <IconClose size={15} />
        </button>
      </div>
    );
  }

  return (
    <div className="relative" ref={boxRef}>
      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-0 flex w-9 items-center justify-center text-muted">
          <IconSearch size={15} />
        </span>
        <TextInput
          className="pl-9"
          value={query}
          placeholder={placeholder}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
        />
      </div>
      {open && debounced && (
        <div
          className="absolute z-10 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-rule bg-paper shadow-[var(--shadow-pop)]"
        >
          {isFetching ? (
            <p className="px-3 py-2 text-sm text-muted">Đang tìm…</p>
          ) : results.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted">Không tìm thấy nhân sự phù hợp.</p>
          ) : (
            results.map((emp) => (
              <button
                key={emp.id}
                type="button"
                className="flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left text-sm hover:bg-paper-2"
                onClick={() => pick(emp)}
              >
                <span className="font-medium text-ink">{emp.full_name}</span>
                <span className="text-xs text-muted">
                  {emp.employee_code}
                  {emp.current_unit ? ` · ${emp.current_unit.name}` : ""}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
