// קוד QR של מספר ההזמנה, שהשואל מציג בנקודה והמתנדב סורק (AB#178, באג #441)
// הספרייה: qrcode-generator 2.0.4 של Kazuhiko Arase (רישיון MIT, js/vendor/qrcode.LICENSE.txt)
import qrcode from "./vendor/qrcode.js";

export function qrSvg(text, label = "קוד QR של ההזמנה") {
  const qr = qrcode(0, "M");
  qr.addData(text);
  qr.make();
  return qr.createSvgTag({ cellSize: 4, margin: 2, scalable: true, alt: { text: label }, title: { text: text } });
}
