import { useState, useEffect } from "react";

export type ThemeMode = "auto" | "dark" | "light";

export function useTheme() {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem("conso_theme") as ThemeMode | null;
    return saved || "auto";
  });

  useEffect(() => {
    const root = document.documentElement;

    const applyTheme = () => {
      let isDark = true;
      if (theme === "dark") {
        isDark = true;
      } else if (theme === "light") {
        isDark = false;
      } else {
        // Auto
        isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      }

      if (isDark) {
        root.classList.add("dark");
        root.classList.remove("light");
      } else {
        root.classList.remove("dark");
        root.classList.add("light");
      }
    };

    applyTheme();
    localStorage.setItem("conso_theme", theme);

    if (theme === "auto") {
      const media = window.matchMedia("(prefers-color-scheme: dark)");
      const listener = () => applyTheme();
      media.addEventListener("change", listener);
      return () => media.removeEventListener("change", listener);
    }
  }, [theme]);

  return { theme, setTheme };
}
