import axios from "axios";
import QRCode from "qrcode";
import { request, API_PATHS, API_BASE_URL, getToken, DEMO_MODE } from "./api";

/** Backend creates and stores one signed token/QR per eligible voter. */
export const generateQr = (electionId) =>
  request(API_PATHS.qrGenerateForElection(electionId), { method: "post" });

export const downloadQrImage = async (electionId, voterId, voterCode) => {
  if (DEMO_MODE) {
    const data = await request(`/api/elections/${electionId}/voters/${voterId}/qr`);
    const dataUrl = await QRCode.toDataURL(data.qr_payload, { width: 320, margin: 2 });
    const link = document.createElement("a");
    link.href = dataUrl;
    link.download = `election-${electionId}-${voterCode || voterId}-qr.png`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    return;
  }
  const response = await axios.get(
    `${API_BASE_URL}/api/elections/${electionId}/voters/${voterId}/qr`,
    {
      responseType: "blob",
      headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
      timeout: 20000,
    }
  );
  const blobUrl = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = `election-${electionId}-${voterCode || voterId}-qr.png`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(blobUrl);
};

export const verifyQr = async (rawValue, electionId) => {
  // QR readers may return either a raw token or the full URL encoded in the QR.
  let token = String(rawValue || "").trim();
  try {
    const parsed = new URL(token);
    token = parsed.searchParams.get("token") || token;
  } catch { /* manual token input */ }
  return request(API_PATHS.qrVerify, {
    method: "post",
    data: { token, election_id: Number(electionId) },
  });
};
