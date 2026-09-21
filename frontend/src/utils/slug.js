/**
 * Chuyển chuỗi tiếng Việt có dấu sang slug ASCII không dấu.
 * Ví dụ: "Thông báo giá đất 2025" → "thong-bao-gia-dat-2025"
 */
export function toSlug(str) {
  if (!str) return "";
  return str
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")   // bỏ dấu tổ hợp
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")      // bỏ ký tự đặc biệt
    .trim()
    .replace(/\s+/g, "-")              // khoảng trắng → gạch ngang
    .replace(/-+/g, "-");              // nhiều gạch ngang → một
}

