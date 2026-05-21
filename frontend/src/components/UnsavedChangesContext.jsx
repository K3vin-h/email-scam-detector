import { createContext, useContext, useMemo, useState } from 'react';

const UnsavedChangesContext = createContext(null);

export function UnsavedChangesProvider({ children }) {
  const [guard, setGuard] = useState({ active: false, onBlocked: null });
  const value = useMemo(() => ({ guard, setGuard }), [guard]);
  return (
    <UnsavedChangesContext.Provider value={value}>
      {children}
    </UnsavedChangesContext.Provider>
  );
}

export function useUnsavedChanges() {
  return useContext(UnsavedChangesContext);
}
