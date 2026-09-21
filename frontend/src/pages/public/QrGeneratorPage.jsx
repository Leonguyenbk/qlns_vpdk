import { useEffect, useMemo, useState } from "react";
import { RoundedSurveyQr, renderRoundedSurveyQr } from "../../components/surveys/RoundedSurveyQr";
import { Button, TextInput } from "../../components/ui/primitives";

export default function QrGeneratorPage() {
  const [value, setValue] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const qrValue = useMemo(() => value.trim(), [value]);

  useEffect(() => {
    let alive = true;
    if (!qrValue) {
      setDownloadUrl("");
      return undefined;
    }
    renderRoundedSurveyQr(qrValue, 720).then((url) => alive && setDownloadUrl(url));
    return () => {
      alive = false;
    };
  }, [qrValue]);

  return (
    <main className="min-h-screen bg-canvas px-4 py-10 text-ink-2 sm:px-6">
      <div className="mx-auto max-w-xl">
        <div className="card p-6 sm:p-8">
          <p className="eyebrow mb-2">VPĐK Đắk Lắk</p>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Tạo mã QR</h1>
          <p className="mt-2 text-sm text-muted">Dán đường dẫn hoặc nhập nội dung cần chia sẻ để tạo mã QR có logo VPĐK.</p>
          <label className="label mt-6" htmlFor="qr-content">Nội dung hoặc đường dẫn</label>
          <TextInput
            id="qr-content"
            value={value}
            onChange={(event) => {
              setValue(event.target.value);
              setDownloadUrl("");
            }}
            placeholder="https://vpdkdaklak.vn/..."
            autoFocus
          />
          <div className="mt-6 flex justify-center rounded-xl border border-rule bg-white p-5">
            {qrValue ? <RoundedSurveyQr value={qrValue} size={280} /> : <div className="flex h-[280px] w-[280px] items-center justify-center text-center text-sm text-muted">Nhập nội dung để xem mã QR</div>}
          </div>
          <div className="mt-5 flex justify-end">
            <a href={downloadUrl || "#"} download="ma-qr-vpdk.png">
              <Button type="button" disabled={!qrValue}>Tải mã QR PNG</Button>
            </a>
          </div>
          <p className="mt-4 text-xs text-muted">Mã dùng mức sửa lỗi cao, nền trắng và tương phản đen/trắng để dễ quét.</p>
        </div>
      </div>
    </main>
  );
}
