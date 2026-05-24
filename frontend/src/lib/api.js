import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const TOKEN_KEY = "mm_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const client = axios.create({
  baseURL: API,
});

client.interceptors.request.use((config) => {
  const t = tokenStore.get();
  if (t) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      tokenStore.clear();
    }
    return Promise.reject(err);
  }
);

export default client;

export const api = {
  // Public
  getWelcomeQuote: () => client.get("/quotes/welcome").then((r) => r.data),
  health: () => client.get("/health").then((r) => r.data),

  // Auth
  startGoogleAuth: (redirect) =>
    client.get("/auth/google/start", { params: { redirect } }).then((r) => r.data),
  me: () => client.get("/auth/me").then((r) => r.data),
  logout: () => client.post("/auth/logout").then((r) => r.data),

  // Chats
  listChats: () => client.get("/chats").then((r) => r.data),
  createChat: (mode, title) => client.post("/chats", { mode, title }).then((r) => r.data),
  getChat: (chatId) => client.get(`/chats/${chatId}`).then((r) => r.data),
  deleteChat: (chatId) => client.delete(`/chats/${chatId}`).then((r) => r.data),
  sendMessage: (chat_id, text) =>
    client.post("/chats/message", { chat_id, text }).then((r) => r.data),

  // Subscription
  getSubStatus: () => client.get("/subscription/status").then((r) => r.data),
  getPackages: () => client.get("/subscription/packages").then((r) => r.data),
  createCheckout: (package_id, origin_url) =>
    client.post("/payments/checkout", { package_id, origin_url }).then((r) => r.data),
  verifyPayment: (payload) => client.post("/payments/verify", payload).then((r) => r.data),
  getPaymentStatus: (orderId) =>
    client.get(`/payments/status/${orderId}`).then((r) => r.data),
  openBillingPortal: (return_url) =>
    client.post("/subscription/portal", { return_url }).then((r) => r.data),

  // Engagement
  getStreak: () => client.get("/streak").then((r) => r.data),
};
