import { useEffect, useState } from "react";
import QRCode from "qrcode";

/* QR sinh phía trình duyệt (không gửi nội dung ra dịch vụ ngoài). */
export function QRCodeImg({ value, size = 168, className }) {
  const [src, setSrc] = useState("");
  useEffect(() => {
    let alive = true;
    if (!value) return undefined;
    QRCode.toDataURL(value, { width: size, margin: 1 })
      .then((url) => alive && setSrc(url))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [value, size]);
  if (!src) return <div style={{ width: size, height: size }} className={className} />;
  return <img src={src} width={size} height={size} alt="Mã QR" className={className} />;
}
