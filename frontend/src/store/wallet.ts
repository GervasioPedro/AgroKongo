import { create } from "zustand";

export type WalletState = {
  saldoDisponivelKz: number;
  saldoEscrowKz: number;
  pendentes: number;
  setResumo: (payload: {
    saldoDisponivelKz: number;
    saldoEscrowKz: number;
    pendentes: number;
  }) => void;
};

export const useWalletStore = create<WalletState>((set) => ({
  saldoDisponivelKz: 0,
  saldoEscrowKz: 0,
  pendentes: 0,
  setResumo: (payload) => set(payload)
}));
