import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export type DefaultModelValue = string | null;

interface AppSettingsState {
  defaultLlmModel: DefaultModelValue;
  defaultEmbeddingModel: DefaultModelValue;
  setDefaultLlmModel: (value: DefaultModelValue) => void;
  setDefaultEmbeddingModel: (value: DefaultModelValue) => void;
}

export const useAppSettingsStore = create<AppSettingsState>()(
  devtools(
    persist(
      (set) => ({
        defaultLlmModel: null,
        defaultEmbeddingModel: null,
        setDefaultLlmModel: (value) => set({ defaultLlmModel: value }, false, 'setDefaultLlmModel'),
        setDefaultEmbeddingModel: (value) => set({ defaultEmbeddingModel: value }, false, 'setDefaultEmbeddingModel'),
      }),
      {
        name: 'app-settings',
        partialize: (state) => ({
          defaultLlmModel: state.defaultLlmModel,
          defaultEmbeddingModel: state.defaultEmbeddingModel,
        }),
      }
    ),
    { name: 'app-settings-store' }
  )
);

