import {
  request,
  API_PATHS,
  DEMO_MODE,
  setToken,
  setRefreshToken,
  getRefreshToken,
  clearToken,
} from "./api";

const normalizeAdmin = (data) => {
  const rawRole = data?.role || "election_admin";
  return {
    ...data,
    name: data?.name || data?.username || "Administrator",
    role: ["org_admin", "election_admin", "auditor"].includes(rawRole) ? "admin" : rawRole,
    backendRole: rawRole,
  };
};

/** The current backend supports administrator password + OTP authentication. */
export async function login(identifier, password, accountType = "admin") {
  // Demo mode shares one simulated login endpoint. The Django package currently
  // implements administrator OTP login only; /api/voter/login is the expected
  // contract for a future voter-auth endpoint and is not present in that backend.
  const endpoint = DEMO_MODE || accountType === "admin" ? API_PATHS.login : API_PATHS.voterLogin;
  const data = await request(endpoint, {
    method: "post",
    data: DEMO_MODE
      ? { identifier, password }
      : accountType === "admin"
        ? { username: identifier, password }
        : { identifier, password },
  });
  if (data?.otp_required) {
    return {
      otpRequired: true,
      otpSession: data.otp_session,
      message: data.message || "A one-time code was sent to your registered contact.",
      demoOtpCode: data.demo_otp_code || null,
    };
  }
  if (data?.access || data?.token) setToken(data.access || data.token);
  if (data?.refresh) setRefreshToken(data.refresh);
  if (data?.user) return { user: accountType === "admin" ? normalizeAdmin(data.user) : { ...data.user, role: "voter" } };
  throw new Error("The authentication service returned an incomplete response.");
}

export async function verifyOtp(code, otpSession) {
  const data = await request(API_PATHS.otpVerify, {
    method: "post",
    data: DEMO_MODE ? { code, otp_session: otpSession } : { otp: code, otp_session: otpSession },
  });
  setToken(data.access || data.token);
  if (data.refresh) setRefreshToken(data.refresh);
  const user = normalizeAdmin(data.user || {
    username: data.username,
    role: data.role,
  });
  return { user };
}

export async function fetchCurrentUser() {
  const data = await request(API_PATHS.me);
  return normalizeAdmin(data);
}

export async function logout() {
  const refresh = getRefreshToken();
  try {
    if (refresh) {
      await request(API_PATHS.logout, { method: "post", data: { refresh } });
    }
  } finally {
    clearToken();
  }
}
