import { create } from "zustand";

export type Notification = {
  id: string;
  message: string;
  read: boolean;
  createdAtISO: string;
};

export type NotificationsState = {
  items: Notification[];
  unreadCount: number;
  setItems: (items: Notification[]) => void;
  markRead: (id: string) => void;
};

export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  items: [],
  unreadCount: 0,
  setItems: (items) =>
    set({
      items,
      unreadCount: items.filter((n) => !n.read).length
    }),
  markRead: (id) => {
    const items = get().items.map((n) => (n.id === id ? { ...n, read: true } : n));
    set({ items, unreadCount: items.filter((n) => !n.read).length });
  }
}));
