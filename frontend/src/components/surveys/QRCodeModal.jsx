import { useEffect, useState } from "react";
import { useUnits } from "../../hooks/useUnits";
import { Modal } from "../ui/Modal";
import { Button, Select } from "../ui/primitives";
import { renderRoundedSurveyQr, RoundedSurveyQr } from "./RoundedSurveyQr";

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

export function QRCodeModal({ survey, onClose }) {
  const [dataUrl, setDataUrl] = useState(null);
  const [branchId, setBranchId] = useState("");
  const { data: units } = useUnits({ only_active: true });
  const branches = (units || []).filter((unit) => unit.unit_type === "BRANCH");
  const publicUrl = survey
    ? `${window.location.origin}/khao-sat/${survey.slug}${branchId ? `?branch=${branchId}` : ""}`
    : "";

  useEffect(() => {
    if (!survey) return setDataUrl(null);
    renderRoundedSurveyQr(publicUrl, 420).then(setDataUrl).catch(() => setDataUrl(null));
  }, [survey, publicUrl]);
  useEffect(() => setBranchId(""), [survey?.id]);

  const onPrint = () => {
    if (!dataUrl) return;
    const win = window.open("", "_blank", "width=420,height=560");
    if (!win) return;
    win.document.write(`<html><head><title>QR - ${escapeHtml(survey.title)}</title></head><body style="text-align:center;padding:32px;font-family:sans-serif"><h3>${escapeHtml(survey.title)}</h3><img src="${dataUrl}" style="width:280px;height:280px"><p style="font-size:12px;color:#555;word-break:break-all">${escapeHtml(publicUrl)}</p></body></html>`);
    win.document.close();
    win.focus();
    win.print();
  };

  const onBulkPrint = async () => {
    if (!survey || !branches.length) return;
    const items = await Promise.all(branches.map(async (branch) => {
      const code = branch.code || branch.id;
      const url = `${window.location.origin}/khao-sat/${survey.slug}?branch=${encodeURIComponent(code)}`;
      return { branch, url, image: await renderRoundedSurveyQr(url, 420) };
    }));
    const win = window.open("", "_blank");
    if (!win) return;
    const cards = items.map(({ branch, url, image }) => `<article class="card"><h2>${escapeHtml(branch.name)}</h2><img src="${image}" alt="QR ${escapeHtml(branch.name)}"><p>${escapeHtml(url)}</p></article>`).join("");
    win.document.write(`<html><head><title>QR ${escapeHtml(survey.title)} - tất cả chi nhánh</title><style>body{font-family:Arial,sans-serif;margin:20px;color:#111827}.sheet{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.card{text-align:center;border:1px solid #d1d5db;border-radius:12px;padding:16px;break-inside:avoid}.card h2{font-size:18px;margin:0 0 10px}.card img{width:240px;height:240px;max-width:100%}.card p{font-size:10px;color:#4b5563;word-break:break-all;margin:10px 0 0}@media print{body{margin:10mm}}</style></head><body><h1>${escapeHtml(survey.title)}</h1><div class="sheet">${cards}</div></body></html>`);
    win.document.close();
    win.focus();
    setTimeout(() => win.print(), 300);
  };

  return (
    <Modal open={!!survey} onClose={onClose} title="Mã QR khảo sát" size="sm">
      {survey && <div className="flex flex-col items-center gap-3">
        <div className="w-full"><Select value={branchId} onChange={(event) => setBranchId(event.target.value)}>
          <option value="">Link chung (người dân tự chọn chi nhánh)</option>
          {branches.map((branch) => <option key={branch.id} value={branch.id}>Gán tại: {branch.name}</option>)}
        </Select></div>
        <RoundedSurveyQr value={publicUrl} size={224} className="rounded-lg border border-rule" />
        <p className="max-w-xs break-all text-center text-xs text-muted">{publicUrl}</p>
        <div className="flex flex-wrap justify-center gap-2">
          <a href={dataUrl || "#"} download={`qr-${survey.slug}.png`} className="btn btn-secondary" aria-disabled={!dataUrl}>Tải PNG</a>
          <Button variant="secondary" onClick={onPrint} disabled={!dataUrl}>In QR</Button>
          <Button variant="secondary" onClick={onBulkPrint} disabled={!branches.length}>Xuất QR tất cả chi nhánh</Button>
        </div>
      </div>}
    </Modal>
  );
}
