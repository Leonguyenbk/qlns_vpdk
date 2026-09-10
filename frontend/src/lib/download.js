import { api } from "./api";

/** Lấy tên file từ header Content-Disposition (hỗ trợ filename*=UTF-8''...). */
function filenameFromHeaders(headers, fallback) {
  const cd = headers?.["content-disposition"] || headers?.["Content-Disposition"] || "";
  const star = /filename\*=UTF-8''([^;]+)/i.exec(cd);
  if (star) return decodeURIComponent(star[1]);
  const plain = /filename="?([^"]+)"?/i.exec(cd);
  return plain ? plain[1] : fallback;
}

/** Tải một endpoint trả về file (blob) và lưu về máy. */
export async function downloadFile(url, { params, fallbackName = "download" } = {}) {
  const res = await api.get(url, { params, responseType: "blob" });
  const name = filenameFromHeaders(res.headers, fallbackName);
  const href = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1000);
}
