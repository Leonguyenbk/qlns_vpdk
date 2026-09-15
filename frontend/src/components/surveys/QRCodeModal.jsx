import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { useUnits } from "../../hooks/useUnits";
import { Modal } from "../ui/Modal";
import { Button, Select } from "../ui/primitives";
import { QRCodeImg } from "../goiso/QRCodeImg";

export function QRCodeModal({ survey, onClose }) {
  const [dataUrl, setDataUrl] = useState(null);
  const [branchId, setBranchId] = useState("");
  const { data: units } = useUnits({ only_active: true });
  const branches = (units || []).filter((u) => u.unit_type === "BRANCH");
  const publicUrl = survey
    ? `${window.location.origin}/khao-sat/${survey.slug}${branchId ? `?branch=${branchId}` : ""}`
    : "";

  // QRCodeImg (dùng chung với module Gọi số) chỉ hiển thị; cần thêm bản data URL
  // để tải PNG/in — sinh riêng bằng cùng thư viện `qrcode`.
  useEffect(() => {
    if (!survey) {
      setDataUrl(null);
      return;
    }
    QRCode.toDataURL(publicUrl, { width: 320, margin: 1 }).then(setDataUrl).catch(() => setDataUrl(null));
  }, [survey, publicUrl]);

  // Về trạng thái "chung" (không chọn chi nhánh) mỗi khi mở lại modal cho khảo sát khác.
  useEffect(() => {
    setBranchId("");
  }, [survey?.id]);

  const onPrint = () => {
    if (!dataUrl) return;
    const win = window.open("", "_blank", "width=420,height=560");
    if (!win) return;
    win.document.write(
      `<html><head><title>QR - ${survey.title}</title></head>` +
        `<body style="text-align:center;padding:32px;font-family:sans-serif;">` +
        `<h3 style="margin-bottom:16px;">${survey.title}</h3>` +
        `<img src="${dataUrl}" style="width:280px;height:280px" />` +
        `<p style="margin-top:12px;font-size:12px;color:#555;word-break:break-all;">${publicUrl}</p>` +
        `</body></html>`
    );
    win.document.close();
    win.focus();
    win.print();
  };

  return (
    <Modal open={!!survey} onClose={onClose} title="Mã QR khảo sát" size="sm">
      {survey && (
        <div className="flex flex-col items-center gap-3">
          <div className="w-full">
            <Select value={branchId} onChange={(e) => setBranchId(e.target.value)}>
              <option value="">Link chung (người dân tự chọn chi nhánh)</option>
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  Dán tại: {b.name}
                </option>
              ))}
            </Select>
          </div>
          <QRCodeImg value={publicUrl} size={224} className="rounded-lg border border-rule" />
          <p className="max-w-xs break-all text-center text-xs text-muted">{publicUrl}</p>
          <div className="flex gap-2">
            <a
              href={dataUrl || "#"}
              download={`qr-${survey.slug}.png`}
              className="btn btn-secondary"
              aria-disabled={!dataUrl}
            >
              Tải PNG
            </a>
            <Button variant="secondary" onClick={onPrint} disabled={!dataUrl}>
              In QR
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
