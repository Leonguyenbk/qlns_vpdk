import { createContext, useContext, useState } from "react";

const NewsContext = createContext();

export function NewsProvider({ children }) {
  const [newCount, setNewCount] = useState(0);
  return (
    <NewsContext.Provider value={{ newCount, setNewCount }}>
      {children}
    </NewsContext.Provider>
  );
}

export function useNews() {
  return useContext(NewsContext);
}