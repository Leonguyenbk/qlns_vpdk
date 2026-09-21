import { useEffect, useState } from "react";
import QRCode from "qrcode";

function roundedRect(context, x, y, size, radius) {
  const r = Math.min(radius, size / 2);
  context.beginPath();
  if (typeof context.roundRect === "function") context.roundRect(x, y, size, size, r);
  else {
    context.moveTo(x + r, y);
    context.arcTo(x + size, y, x + size, y + size, r);
    context.arcTo(x + size, y + size, x, y + size, r);
    context.arcTo(x, y + size, x, y, r);
    context.arcTo(x, y, x + size, y, r);
    context.closePath();
  }
  context.fill();
}

export async function renderRoundedSurveyQr(value, size = 420) {
  if (!value || typeof document === "undefined") return "";
  const qr = QRCode.create(value, { errorCorrectionLevel: "H" });
  const moduleCount = qr.modules.size;
  const margin = 4;
  const cell = Math.max(2, Math.floor(size / (moduleCount + margin * 2)));
  const canvas = document.createElement("canvas");
  canvas.width = cell * (moduleCount + margin * 2);
  canvas.height = canvas.width;
  const context = canvas.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "#111827";
  for (let row = 0; row < moduleCount; row += 1) {
    for (let column = 0; column < moduleCount; column += 1) {
      if (!qr.modules.data[row * moduleCount + column]) continue;
      roundedRect(context, (column + margin) * cell, (row + margin) * cell, cell, cell * 0.24);
    }
  }
  const center = canvas.width / 2;
  const logoSize = cell * 8;
  context.fillStyle = "#ffffff";
  roundedRect(context, center - logoSize / 2, center - logoSize / 2, logoSize, cell);
  const logo = await new Promise((resolve) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => resolve(null);
    image.src = "/vpdk-logo.png";
  });
  if (logo) {
    context.save();
    context.beginPath();
    context.arc(center, center, logoSize / 2 - cell * 0.35, 0, Math.PI * 2);
    context.clip();
    context.drawImage(logo, center - logoSize / 2, center - logoSize / 2, logoSize, logoSize);
    context.restore();
  } else {
    context.fillStyle = "#111827";
    context.font = `700 ${Math.max(8, cell * 1.7)}px Arial, sans-serif`;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText("VPĐK", center, center);
  }
  return canvas.toDataURL("image/png");
}

export function RoundedSurveyQr({ value, size = 224, className }) {
  const [src, setSrc] = useState("");
  useEffect(() => {
    let alive = true;
    setSrc("");
    renderRoundedSurveyQr(value, Math.max(320, size * 2)).then((url) => alive && setSrc(url));
    return () => {
      alive = false;
    };
  }, [value, size]);
  if (!src) return <div style={{ width: size, height: size }} className={className} />;
  return <img src={src} width={size} height={size} alt="Mã QR khảo sát" className={className} />;
}
