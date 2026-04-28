import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default client;

export const api = {
  // Public
  getWelcomeQuote: () => client.get("/quotes/welcome").then((r) => r.data),
  health: () => client.get("/health").then((r) => r.data),

  // Auth
  exchangeSession: (session_id) =>
    client.post("/auth/session", { session_id }).then((r) => r.data),
  me: () => client.get("/auth/me").then((r) => r.data),
  logout: () => client.post("/auth/logout").then((r) => r.data),

  // Chats
  listChats: () => client.get("/chats").then((r) => r.data),
  createChat: (mode, title) =>
    client.post("/chats", { mode, title }).then((r) => r.data),
  getChat: (chatId) => client.get(`/chats/${chatId}`).then((r) => r.data),
  deleteChat: (chatId) => client.delete(`/chats/${chatId}`).then((r) => r.data),
  sendMessage: (chat_id, text) =>
    client.post("/chats/message", { chat_id, text }).then((r) => r.data),

  // Subscription
  getSubStatus: () => client.get("/subscription/status").then((r) => r.data),
  getPackages: () => client.get("/subscription/packages").then((r) => r.data),
  createCheckout: (package_id, origin_url) =>
    client
      .post("/payments/checkout", { package_id, origin_url })
      .then((r) => r.data),
  getPaymentStatus: (sessionId) =>
    client.get(`/payments/status/${sessionId}`).then((r) => r.data),
  openBillingPortal: (return_url) =>
    client
      .post("/subscription/portal", { return_url })
      .then((r) => r.data),

  // Engagement
  getStreak: () => client.get("/streak").then((r) => r.data),
};
